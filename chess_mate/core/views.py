"""
This module contains the views for the ChessMate application, including endpoints for fetching, 
analyzing, and providing feedback on chess games, as well as user authentication and registration.
"""

# Standard library imports
import os
import json
import logging

# Django imports
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django_ratelimit.decorators import ratelimit   # type: ignore

# Third-party imports
import requests
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import chess.engine
from openai import OpenAI
import stripe

# Local application imports
from .models import Game, GameAnalysis, Profile
from .chess_services import ChessComService, LichessService, save_game
from .game_analyzer import GameAnalyzer
from .validators import validate_password_complexity

STOCKFISH_PATH = os.getenv("STOCKFISH_PATH")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def index(request):
    """
    Render the index page.
    """
    return render(request, "index.html")

@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def fetch_games(request):
    """
    Fetch games from Chess.com or Lichess APIs based on the username and platform provided.
    """
    user = request.user
    data = request.data
    platform = data.get("platform")
    username = data.get("username")
    game_type = data.get("game_type", "rapid")

    # Validate game type
    allowed_game_types = ["bullet", "blitz", "rapid", "classical"]
    if game_type not in allowed_game_types:
        return Response(
            {"error": "Invalid game type. Allowed types: bullet, blitz, rapid, classical."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not platform or not username:
        return Response(
            {"error": "Platform and username are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Fetch games based on platform
        games = []
        if platform == "chess.com":
            games = ChessComService.fetch_games(username, game_type)
        elif platform == "lichess":
            games = LichessService.fetch_games(username, game_type)
        else:
            return Response(
                {"error": "Invalid platform. Use 'chess.com' or 'lichess'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save fetched games
        saved_count = 0
        for game in games:
            if save_game(game, username, user):
                saved_count += 1

        return Response(
            {
                "message": f"Successfully fetched and saved {saved_count} games!",
                "total_games": len(games),
                "saved_games": saved_count
            },
            status=status.HTTP_201_CREATED
        )

    except requests.exceptions.HTTPError as http_err:
        return Response(
            {"error": f"HTTP error: {str(http_err)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    except (requests.exceptions.RequestException, ValueError) as e:
        logger.error("Error fetching games: %s", str(e))
        return Response(
            {"error": "Failed to fetch games. Please try again later."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_saved_games(request):
    """
    Retrieve saved games for the logged-in user.
    """
    user = request.user
    if not user.is_authenticated:
        return Response({"error": "User not authenticated."}, status=status.HTTP_401_UNAUTHORIZED)

    games = Game.objects.filter(player=user).values(
        "opponent", "result", "played_at", "game_url"
    )
    return Response(games, status=status.HTTP_200_OK)

@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def analyze_game_view(request, game_id):
    """
    Endpoint to analyze a specific game by its ID.
    """
    try:
        user = request.user
        depth = request.data.get("depth", 20)

        if not isinstance(depth, int) or depth <= 0:
            return JsonResponse({"error": "Invalid depth value."}, status=400)

        # Fetch the game from the database
        game = Game.objects.filter(id=game_id, player=user).first()
        if not game:
            return JsonResponse({"error": "Game not found or unauthorized access."}, status=404)

        # Initialize GameAnalyzer
        analyzer = GameAnalyzer()

        try:
            logger.info("Analyzing game %s", game_id)
            analysis_results = analyzer.analyze_games([game], depth=depth)
            
            # Generate comprehensive feedback
            feedback = analyzer.generate_feedback(analysis_results[game_id])
            
            # Save analysis results to the database
            game.analysis = analysis_results[game_id]
            game.save()

            response_data = {
                "message": "Game analyzed successfully!",
                "analysis": analysis_results[game_id],
                "feedback": feedback,
                "game_info": {
                    "id": game.id,
                    "opponent": game.opponent,
                    "result": game.result,
                    "played_at": game.played_at,
                    "opening_name": game.opening_name,
                    "is_white": game.is_white
                }
            }

            return Response(response_data, status=200)
        finally:
            try:
                analyzer.close_engine()
            except chess.engine.EngineTerminatedError:
                logger.warning("Engine already terminated.")
    except Game.DoesNotExist:
        return JsonResponse({"error": "Game not found."}, status=404)
    except Exception as e:
        logger.error("Error in analyze_game_view: %s: %s", game_id, str(e), exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)

def generate_feedback_without_ai(analysis_data, stats):
    """Generate structured feedback without using OpenAI API."""
    template = """
Opening Analysis:
• Based on your opening moves, {opening_feedback}
• Key suggestion: {opening_suggestion}

Middlegame Strategy:
• Your positional play shows {middlegame_feedback}
• Focus areas: {middlegame_areas}

Tactical Awareness:
• Statistics show {tactical_feedback}
• Recommendation: {tactical_suggestion}

Time Management:
• Analysis indicates {time_feedback}
• Key improvement: {time_suggestion}

Endgame Technique:
• Your endgame play {endgame_feedback}
• Practice suggestion: {endgame_suggestion}
"""
    
    # Opening feedback
    if stats["common_mistakes"].get("mistakes", 0) > 1 in range(1, 10):
        opening_feedback = "you might benefit from deeper opening preparation"
        opening_suggestion = "study the main lines of your chosen openings and understand their key ideas"
    else:
        opening_feedback = "you have a good grasp of opening principles"
        opening_suggestion = "consider expanding your opening repertoire"

    # Middlegame feedback
    if stats["average_accuracy"] < 70:
        middlegame_feedback = "room for improvement in positional understanding"
        middlegame_areas = "piece coordination and pawn structure management"
    else:
        middlegame_feedback = "good strategic understanding"
        middlegame_areas = "complex position evaluation and long-term planning"

    # Tactical feedback
    blunders = stats["common_mistakes"].get("blunders", 0)
    if blunders > 0.5:
        tactical_feedback = f"an average of {blunders:.1f} blunders per game"
        tactical_suggestion = "practice tactical puzzles daily focusing on calculation accuracy"
    else:
        tactical_feedback = "good tactical awareness"
        tactical_suggestion = "work on finding more advanced tactical opportunities"

    # Time management
    time_pressure = stats["common_mistakes"].get("time_pressure", 0)
    if time_pressure > 0.3:
        time_feedback = "you often get into time trouble"
        time_suggestion = "practice better time allocation in the opening and middlegame"
    else:
        time_feedback = "generally good time management"
        time_suggestion = "fine-tune your time usage in critical positions"

    # Endgame feedback
    if stats["average_accuracy"] > 80:
        endgame_feedback = "shows strong technical understanding"
        endgame_suggestion = "study more complex endgame positions"
    else:
        endgame_feedback = "could benefit from more practice"
        endgame_suggestion = "focus on basic endgame principles and common patterns"

    return template.format(
        opening_feedback=opening_feedback,
        opening_suggestion=opening_suggestion,
        middlegame_feedback=middlegame_feedback,
        middlegame_areas=middlegame_areas,
        tactical_feedback=tactical_feedback,
        tactical_suggestion=tactical_suggestion,
        time_feedback=time_feedback,
        time_suggestion=time_suggestion,
        endgame_feedback=endgame_feedback,
        endgame_suggestion=endgame_suggestion
    )

@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def analyze_batch_games_view(request):
    """
    Analyze a batch of games for the authenticated user.
    """
    try:
        user = request.user
        depth = request.data.get("depth", 20)
        num_games = request.data.get("num_games", 5)
        use_ai = request.data.get("use_ai", False)  # Make AI feedback optional

        if not isinstance(depth, int) or depth <= 0:
            return JsonResponse({"error": "Invalid depth value."}, status=400)

        if not num_games or not isinstance(num_games, int) or num_games <= 0:
            return JsonResponse({"error": "Invalid number of games value."}, status=400)

        # Fetch games for the user
        games = Game.objects.filter(player=user).order_by("-played_at")[:num_games]
        if not games.exists():
            return Response({"error": "No games found for analysis."}, status=404)

        analyzer = GameAnalyzer()
        try:
            logger.info("Starting batch analysis for user %s with %d games.", user.id, len(games))
            analysis_results = analyzer.analyze_games(games, depth=depth)

            # Save analysis results to the database
            for game in games:
                if game.id in analysis_results:
                    game.analysis = analysis_results[game.id]
                    game.save()

            # Generate comprehensive feedback for each game
            feedback_results = {}
            overall_stats = {
                "total_games": len(games),
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "average_accuracy": 0,
                "common_mistakes": {
                    "blunders": 0,
                    "mistakes": 0,
                    "inaccuracies": 0,
                    "time_pressure": 0
                },
                "improvement_areas": [],
                "strengths": []
            }

            total_accuracy = 0
            for game in games:
                if game.id in analysis_results:
                    # Generate feedback for this game
                    game_feedback = analyzer.generate_feedback(analysis_results[game.id])
                    feedback_results[game.id] = game_feedback

                    # Update overall stats
                    if game.result == "win":
                        overall_stats["wins"] += 1
                    elif game.result == "loss":
                        overall_stats["losses"] += 1
                    else:
                        overall_stats["draws"] += 1

                    # Track mistakes and patterns
                    overall_stats["common_mistakes"]["blunders"] += game_feedback["blunders"]
                    overall_stats["common_mistakes"]["mistakes"] += game_feedback["mistakes"]
                    overall_stats["common_mistakes"]["inaccuracies"] += game_feedback["inaccuracies"]
                    
                    # Calculate game accuracy
                    total_moves = len(analysis_results[game.id])
                    if total_moves > 0:
                        good_moves = total_moves - (
                            game_feedback["blunders"] + 
                            game_feedback["mistakes"] + 
                            game_feedback["inaccuracies"]
                        )
                        game_accuracy = (good_moves / total_moves) * 100
                        total_accuracy += game_accuracy

                        # Track time pressure
                        if len(game_feedback["time_management"]["time_pressure_moves"]) > 3:
                            overall_stats["common_mistakes"]["time_pressure"] += 1

            # Calculate averages
            num_analyzed_games = len(feedback_results)
            if num_analyzed_games > 0:
                overall_stats["average_accuracy"] = total_accuracy / num_analyzed_games
                
                # Normalize mistake counts
                for mistake_type in overall_stats["common_mistakes"]:
                    overall_stats["common_mistakes"][mistake_type] /= num_analyzed_games

                # Generate improvement areas
                if overall_stats["common_mistakes"]["blunders"] > 0.5:
                    overall_stats["improvement_areas"].append({
                        "area": "Tactical Awareness",
                        "description": "Focus on reducing tactical oversights and blunders"
                    })
                if overall_stats["common_mistakes"]["mistakes"] > 1:
                    overall_stats["improvement_areas"].append({
                        "area": "Strategic Planning",
                        "description": "Work on positional understanding and long-term planning"
                    })
                if overall_stats["common_mistakes"]["time_pressure"] > 0.3:
                    overall_stats["improvement_areas"].append({
                        "area": "Time Management",
                        "description": "Improve time management, especially in critical positions"
                    })

                # Identify strengths
                if overall_stats["average_accuracy"] > 80:
                    overall_stats["strengths"].append({
                        "area": "Overall Accuracy",
                        "description": "Strong overall play with few significant errors"
                    })
                if overall_stats["wins"] / num_analyzed_games > 0.6:
                    overall_stats["strengths"].append({
                        "area": "Competitive Performance",
                        "description": "Good win rate showing strong competitive ability"
                    })

            # Generate feedback (with or without AI)
            if use_ai and os.getenv("OPENAI_API_KEY"):
                try:
                    # ... existing OpenAI code ...
                    dynamic_feedback = response.choices[0].message.content.strip()
                except Exception as e:
                    logger.error("Error generating OpenAI feedback: %s", str(e))
                    dynamic_feedback = generate_feedback_without_ai(analysis_results, overall_stats)
            else:
                dynamic_feedback = generate_feedback_without_ai(analysis_results, overall_stats)

            response_data = {
                "message": "Batch analysis completed!",
                "results": {
                    "individual_games": feedback_results,
                    "overall_stats": overall_stats,
                    "dynamic_feedback": dynamic_feedback
                }
            }

            return Response(response_data, status=200)
        finally:
            try:
                analyzer.close_engine()
            except chess.engine.EngineTerminatedError:
                logger.warning("Engine already terminated.")
    except Exception as e:
        logger.error("Error in analyze_batch_games_view: %s", str(e), exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)

def generate_dynamic_feedback(results):
    feedback = {
        "timeManagement": {"avgTimePerMove": 0, "suggestion": ""},
        "opening": {"playedMoves": [], "suggestion": ""},
        "endgame": {"evaluation": "", "suggestion": ""},
        "tacticalOpportunities": []
    }

    total_moves = 0
    for game_analysis in results.values():
        for move in game_analysis:
            if move["is_capture"]:
                feedback["tacticalOpportunities"].append(
                    f"Tactical opportunity on move {move['move_number']}"
                )
            feedback["timeManagement"]["avgTimePerMove"] += move.get("time_spent", 0)
            total_moves += 1
            if move["move_number"] <= 5:
                feedback["opening"]["playedMoves"].append(move["move"])

    if total_moves > 0:
        feedback["timeManagement"]["avgTimePerMove"] /= total_moves

    # Generate refined suggestions via OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a chess analysis expert providing specific, actionable feedback to help players improve their game."},
                {"role": "user", "content": f"Provide actionable feedback for chess analysis: {json.dumps(feedback)}"}
            ],
            max_tokens=200,
            temperature=0.7
        )
        dynamic_feedback = response.choices[0].message.content.strip()
        feedback["dynamicFeedback"] = dynamic_feedback
    except Exception as e:
        logger.error("Error generating feedback with OpenAI: %s", e)

    return feedback

def extract_suggestion(feedback_text, section):
    """
    Extract the suggestion for a specific section from the dynamic feedback text.
    """
    try:
        start_index = feedback_text.index(f"{section} Suggestion:") + len(f"{section} Suggestion:")
        end_index = feedback_text.index("\n", start_index)
        return feedback_text[start_index:end_index].strip()
    except ValueError:
        return "No suggestion available."

@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def game_feedback_view(request, game_id):
    """
    Provide feedback for a specific game by its ID.
    """
    user = request.user
    game = Game.objects.filter(id=game_id, player=user).first()
    if not game:
        return JsonResponse({"error": "Game not found."}, status=404)

    game_analysis = GameAnalysis.objects.filter(game=game)
    if not game_analysis.exists():
        return JsonResponse({"error": "Analysis not found for this game."}, status=404)

    feedback = generate_dynamic_feedback({game.id: game_analysis})
    return JsonResponse({"feedback": feedback}, status=200)

@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def batch_feedback_view(request):
    """
    Generate and return feedback for a batch of games.
    """
    user = request.user
    game_ids = request.data.get("game_ids", [])

    games = Game.objects.filter(id__in=game_ids, player=user)
    if not games.exists():
        return Response({"error": "No valid games found."}, status=404)

    analyzer = GameAnalyzer()
    batch_feedback = {}

    for game in games:
        game_analysis = GameAnalysis.objects.filter(game=game)
        if game_analysis.exists():
            feedback = analyzer.generate_feedback(game_analysis)
            batch_feedback[game.id] = feedback

    return Response({"batch_feedback": batch_feedback}, status=200)

#==================================Login Logic==================================

# Helper function to generate tokens for a user
def get_tokens_for_user(user):
    """
    Generate JWT tokens for a given user.
    """
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }

@csrf_exempt
@api_view(["POST"])
def register_view(request):
    """
    Handle user registration.
    """
    data = request.data
    email = data.get("email")
    password = data.get("password")
    username = data.get("username")

    if not email or not password or not username:
        return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({"error": "Email already in use."}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already in use."}, status=status.HTTP_400_BAD_REQUEST)

    # Ensure password complexity is validated
    try:
        validate_password_complexity(password)
    except ValidationError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            user = User.objects.create_user(username=username, email=email, password=password)
            # Ensure Profile is created only if it does not exist
            Profile.objects.get_or_create(user=user)
        send_confirmation_email(user)
    except ValidationError as e:
        return Response(
            {"error": f"Failed to register user due to validation error: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        print(f"Unexpected error during registration: {str(e)}")
        return Response(
            {"error": "Failed to register user due to an unexpected error."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(
        {"message": "User registered successfully! Please confirm your email."},
        status=status.HTTP_201_CREATED
    )

# Helper function to send a confirmation email
def send_confirmation_email(user):
    """
    Send a confirmation email to the newly registered user.
    """
    subject = "Confirm Your Email"
    message = f"Hi {user.username},\n\nPlease confirm your email address to activate your account."
    recipient_list = [user.email]
    try:
        send_mail(subject, message, "your-email@example.com", recipient_list)
    except Exception as e:
        print(f"Error sending confirmation email: {str(e)}")  # Log the specific error
        raise ValidationError(
            "Failed to send confirmation email. Please check your email settings and try again."
        ) from e

@csrf_exempt
@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def login_view(request):
    """
    Handle user login.
    """
    if request.method == "POST":
        try:
            # Parse JSON payload
            data = json.loads(request.body.decode('utf-8'))  # Decode the request body

            # Ensure data is a dictionary
            if not isinstance(data, dict):
                return JsonResponse({"error": "Invalid JSON payload"}, status=400)

            # Extract fields
            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                return JsonResponse({"error": "Both email and password are required."}, status=400)

            try:
                user = User.objects.get(email=email)
            except ObjectDoesNotExist:
                return JsonResponse({"error": "Invalid email or password."}, status=400)

            user = authenticate(username=user.username, password=password)
            if user is None:
                return JsonResponse({"error": "Invalid email or password."}, status=400)

            tokens = get_tokens_for_user(user)
            return JsonResponse({"message": "Login successful!", "tokens": tokens}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Handle user logout by blacklisting the refresh token.
    """
    try:
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response({"error": "Refresh token is required."},
            status=status.HTTP_400_BAD_REQUEST)
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logout successful!"},
                        status=status.HTTP_200_OK)
    except AttributeError:
        return Response({"error": "Blacklisting is not enabled."},
                        status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#================================== Testing Data ==================================
def game_analysis_view(request, game_id):
    """
    Provide a mock analysis for a specific game by its ID.
    """
    analysis = [
        {"move": "e4", "score": 0.3},
        {"move": "e5", "score": 0.2},
        {"move": "Nf3", "score": 0.5},
    ]
    return JsonResponse({"game_id": game_id, "analysis": analysis})

#================================== Dashboard ==================================
@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_view(request):
    """
    Return user-specific games for the dashboard.
    """
    user = request.user
    games = Game.objects.filter(user=user)
    games_data = [
        {
            "id": game.id,
            "title": game.title,
            "result": game.result,
            "played_at": game.played_at,
        }
        for game in games
    ]
    return Response({"games": games_data}, status=status.HTTP_200_OK)

@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_games_view(request):
    """
    Fetch games specific to the logged-in user.
    """
    user = request.user  # Extract the logged-in user
    games = Game.objects.filter(player=user).order_by("-played_at")
    games_data = [
        {
            "id": game.id,
            "opponent": game.opponent,
            "result": game.result,
            "played_at": game.played_at,
            "opening_name": game.opening_name,
            "is_white": game.is_white,
        }
        for game in games
    ]
    return Response({"games": games_data}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(["GET"])
def all_games_view(request):
    """
    Fetch all available games (generic endpoint).
    """
    games = Game.objects.all().order_by("-played_at")  # Fetch all games
    games_data = [
        {
            "id": game.id,
            "title": game.title,
            "result": game.result,
            "played_at": game.played_at,
        }
        for game in games
    ]
    return Response({"games": games_data}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_credits(request):
    """Get the current user's credit balance."""
    try:
        profile = Profile.objects.get(user=request.user)
        return Response({'credits': profile.credits})
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deduct_credits(request):
    """Deduct credits from the user's balance."""
    try:
        amount = request.data.get('amount', 0)
        if not amount or amount <= 0:
            return Response({'error': 'Invalid amount'}, status=400)

        profile = Profile.objects.get(user=request.user)
        if profile.credits < amount:
            return Response({'error': 'Insufficient credits'}, status=400)

        profile.credits -= amount
        profile.save()

        return Response({
            'message': f'Successfully deducted {amount} credits',
            'remaining_credits': profile.credits
        })
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def purchase_credits(request):
    """Purchase credits using Stripe."""
    try:
        package_id = request.data.get('packageId')
        if not package_id:
            return Response({'error': 'Package ID is required'}, status=400)

        # Define credit packages
        packages = {
            'basic': {'credits': 10, 'price': 499},  # $4.99
            'pro': {'credits': 50, 'price': 1999},   # $19.99
            'unlimited': {'credits': 200, 'price': 4999}  # $49.99
        }

        if package_id not in packages:
            return Response({'error': 'Invalid package ID'}, status=400)

        package = packages[package_id]

        # Create Stripe payment intent
        intent = stripe.PaymentIntent.create(
            amount=package['price'],
            currency='usd',
            metadata={
                'user_id': request.user.id,
                'credits': package['credits']
            }
        )

        return Response({
            'clientSecret': intent.client_secret,
            'amount': package['price'],
            'credits': package['credits']
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_purchase(request):
    """Confirm credit purchase and add credits to user's account."""
    try:
        payment_intent_id = request.data.get('paymentIntentId')
        if not payment_intent_id:
            return Response({'error': 'Payment intent ID is required'}, status=400)

        # Verify payment intent
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        if intent.status != 'succeeded':
            return Response({'error': 'Payment not successful'}, status=400)

        # Add credits to user's account
        profile = Profile.objects.get(user=request.user)
        credits_to_add = int(intent.metadata['credits'])
        profile.credits += credits_to_add
        profile.save()

        return Response({
            'message': f'Successfully added {credits_to_add} credits',
            'newCredits': profile.credits
        })
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
def token_refresh_view(request):
    """Refresh the user's access token."""
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=400)

        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)

        return Response({
            'access': access_token
        })
    except Exception as e:
        return Response({'error': str(e)}, status=400)
