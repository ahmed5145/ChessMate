"""
This module contains the views for the ChessMate application, including endpoints for fetching, 
analyzing, and providing feedback on chess games, as well as user authentication and registration.
"""

# Standard library imports
import os
import json
import logging
import httpx
import uuid
from datetime import datetime
from django.utils import timezone
from typing import Dict, Any, List, Optional

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
from django.db import models
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse

# Third-party imports
import requests
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import chess.engine
from openai import OpenAI
from django.contrib.auth.tokens import default_token_generator
from django.utils.html import strip_tags

# Local application imports
from .models import Game, GameAnalysis, Profile, Transaction
from .chess_services import ChessComService, LichessService, save_game
from .game_analyzer import GameAnalyzer
from .validators import validate_password_complexity
from .ai_feedback import AIFeedbackGenerator
from .decorators import rate_limit
from .payment import PaymentProcessor, CREDIT_PACKAGES
from .utils import generate_feedback_without_ai

STOCKFISH_PATH = os.getenv("STOCKFISH_PATH")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize stripe
try:
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
except ImportError:
    stripe = None
    logger.warning("Stripe package not installed. Payment features will be disabled.")

def get_openai_client():
    """Get OpenAI client with proper error handling."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OpenAI API key not set. AI features will be disabled.")
        return None
    return OpenAI(api_key=api_key)

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Initialize feedback generator with proper error handling
ai_feedback_generator = AIFeedbackGenerator(api_key=os.getenv("OPENAI_API_KEY"))

def index(request):
    """
    Render the index page.
    """
    return render(request, "index.html")

@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_saved_games(request):
    """
    Retrieve saved games for the logged-in user.
    """
    user = request.user
    games = Game.objects.filter(user=user).values(
        "id",
        "platform",
        "white",
        "black",
        "opponent",
        "result",
        "date_played",
        "opening_name",
        "analysis"
    ).order_by("-date_played")
    
    return Response(list(games), status=status.HTTP_200_OK)

class EmailVerificationToken:
    @staticmethod
    def generate_token():
        return str(uuid.uuid4())

    @staticmethod
    def is_valid(token, max_age_days=7):
        try:
            # Add token validation logic here if needed
            return True
        except Exception:
            return False

@rate_limit(endpoint_type='AUTH')
@api_view(['POST'])
def register_view(request):
    """
    Handle user registration with email verification.
    """
    data = request.data
    email = data.get("email")
    password = data.get("password")
    username = data.get("username")

    # Validate required fields
    if not email or not password or not username:
        return Response(
            {"error": "All fields are required.", "field": "all"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check for existing email
    if User.objects.filter(email=email).exists():
        return Response(
            {
                "error": "This email is already registered. Please use a different email or try logging in.",
                "field": "email"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check for existing username
    if User.objects.filter(username=username).exists():
        return Response(
            {
                "error": "This username is already taken. Please choose a different username.",
                "field": "username"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        validate_password_complexity(password)
    except ValidationError as e:
        return Response(
            {"error": str(e), "field": "password"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            # Create inactive user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_active=False
            )
            
            # Delete any existing profile for this user
            Profile.objects.filter(user=user).delete()
            
            # Create new profile with starter credits
            profile = Profile.objects.create(
                user=user,
                email_verification_token=EmailVerificationToken.generate_token(),
                email_verification_sent_at=timezone.now(),
                credits=10  # Give starter credits
            )
            
            # Send verification email
            try:
                send_verification_email(request, user, profile.email_verification_token)
            except Exception as e:
                logger.error(f"Error sending verification email: {str(e)}")
                # Don't fail registration if email fails, but log it
                pass
            
        return Response(
            {
                "message": "Registration successful! Please check your email to verify your account.",
                "email": email
            },
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return Response(
            {"error": "An unexpected error occurred during registration. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def send_verification_email(request, user, token):
    """
    Send verification email with activation link.
    """
    try:
        current_site = get_current_site(request)
        protocol = 'https' if request.is_secure() else 'http'
        verification_url = f"{protocol}://{current_site.domain}/verify-email/{urlsafe_base64_encode(force_bytes(user.pk))}/{token}"
        
        subject = "Verify Your Email - ChessMate"
        html_message = render_to_string('email/verify_email.html', {
            'user': user,
            'verification_url': verification_url,
            'domain': current_site.domain,
        })
        
        # Create plain text version
        text_message = f"""
        Hello {user.username},
        
        Thank you for registering with ChessMate. To complete your registration and activate your account, please visit:
        
        {verification_url}
        
        This verification link will expire in 7 days.
        
        If you did not create an account with ChessMate, please ignore this email.
        """
        
        logger.info(f"Attempting to send verification email to {user.email}")
        
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
            html_message=html_message
        )
        
        logger.info(f"Successfully sent verification email to {user.email}")
        
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}. Error: {str(e)}")
        logger.error(f"Email settings: HOST={settings.EMAIL_HOST}, PORT={settings.EMAIL_PORT}, USER={settings.EMAIL_HOST_USER}, FROM={settings.DEFAULT_FROM_EMAIL}")
        raise

@csrf_exempt
@api_view(["GET"])
def verify_email(request, uidb64, token):
    """
    Verify email and activate user account.
    """
    try:
        # First decode the uidb64 to get the user id
        from django.utils.encoding import force_str
        from django.utils.http import urlsafe_base64_decode
        
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        profile = Profile.objects.get(user=user)
        
        if profile.email_verification_token == token:
            if not EmailVerificationToken.is_valid(token):
                return render(request, 'verification_error.html', {
                    'error': 'Verification link has expired. Please request a new one.'
                }, status=400)
            
            user.is_active = True
            user.save()
            
            profile.email_verified = True
            profile.email_verified_at = timezone.now()
            profile.save()
            
            return render(request, 'verification_success.html', {
                'username': user.username
            })
        
        return render(request, 'verification_error.html', {
            'error': 'Invalid verification link.'
        }, status=400)
        
    except (TypeError, ValueError, OverflowError, User.DoesNotExist, Profile.DoesNotExist) as e:
        logger.error(f"Email verification error: {str(e)}")
        return render(request, 'verification_error.html', {
            'error': 'Invalid verification link.'
        }, status=400)

@rate_limit(endpoint_type='AUTH')
@api_view(['POST'])
def login_view(request):
    """
    Handle user login with email verification check.
    """
    try:
        data = request.data
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return Response(
                {"error": "Both email and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid email or password."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.is_active:
            return Response(
                {"error": "Please verify your email before logging in."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=user.username, password=password)
        if user is None:
            return Response(
                {"error": "Invalid email or password."},
                status=status.HTTP_400_BAD_REQUEST
            )

        tokens = get_tokens_for_user(user)
        return Response({
            "message": "Login successful!",
            "tokens": tokens,
            "user": {
                "username": user.username,
                "email": user.email
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return Response(
            {"error": "An error occurred during login."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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
    game_mode = data.get("game_mode", "all")
    num_games = int(data.get("num_games", 10))

    if not platform or not username:
        return Response(
            {"error": "Platform and username are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    allowed_game_modes = ["all", "bullet", "blitz", "rapid", "classical"]
    if game_mode not in allowed_game_modes:
        return Response(
            {"error": "Invalid game mode. Allowed modes: all, bullet, blitz, rapid, classical."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            profile = Profile.objects.select_for_update().get(user=user)
            required_credits = num_games
            
            if profile.credits < required_credits:
                return Response(
                    {"error": f"Not enough credits. Required: {required_credits}, Available: {profile.credits}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                if platform == "chess.com":
                    games = ChessComService.fetch_games(username, game_mode, limit=num_games)
                elif platform == "lichess":
                    games = LichessService.fetch_games(username, game_mode, limit=num_games)
                else:
                    return Response(
                        {"error": "Invalid platform. Use 'chess.com' or 'lichess'."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if not games:
                    return Response(
                        {"message": "No games found for the given username and criteria."},
                        status=status.HTTP_200_OK
                    )
                
                logger.info(f"Fetched {len(games)} games from {platform} for user {username}")
            except Exception as e:
                logger.error(f"Error fetching games from {platform}: {str(e)}")
                return Response(
                    {"error": f"Failed to fetch games from {platform}. Please try again later."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            saved_games = []
            saved_count = 0
            for game_data in games:
                try:
                    # Ensure game_id exists and is unique
                    game_id = game_data.get("game_id")
                    if not game_id:
                        logger.warning(f"Skipping game without game_id: {game_data}")
                        continue
                        
                    # Check if game already exists
                    if Game.objects.filter(user=user, platform=platform, game_id=game_id).exists():
                        logger.info(f"Game {game_id} already exists for user {user.username}")
                        continue

                    game = Game.objects.create(
                        user=user,
                        platform=platform,
                        game_id=game_id,
                        pgn=game_data.get("pgn", ""),
                        result=game_data.get("result", "unknown"),
                        white=game_data.get("white", ""),
                        black=game_data.get("black", ""),
                        opponent=game_data.get("opponent", "Unknown"),
                        opening_name=game_data.get("opening_name", "Unknown Opening"),
                        date_played=game_data.get("played_at") or datetime.now()
                    )
                    saved_count += 1
                    saved_games.append({
                        "id": game.id,
                        "platform": game.platform,
                        "white": game.white,
                        "black": game.black,
                        "opponent": game.opponent,
                        "result": game.result,
                        "date_played": game.date_played,
                        "opening_name": game.opening_name,
                        "game_id": game.game_id
                    })
                    
                    if saved_count >= num_games:
                        break
                except Exception as e:
                    logger.error(f"Error saving game: {str(e)}")
                    continue

            if saved_count > 0:
                profile.credits -= saved_count
                profile.save()

                Transaction.objects.create(
                    user=user,
                    transaction_type='usage',
                    credits=saved_count,
                    status='completed'
                )

                logger.info(f"Successfully saved {saved_count} games for user {user.username}")
                return Response(
                    {
                        "message": f"Successfully fetched and saved {saved_count} games!",
                        "games_saved": saved_count,
                        "credits_deducted": saved_count,
                        "credits_remaining": profile.credits,
                        "games": saved_games
                    },
                    status=status.HTTP_201_CREATED
                )
            else:
                logger.warning(f"No new games were saved for user {user.username}")
                return Response(
                    {
                        "message": "No new games were saved. They might already exist in your account.",
                        "games_saved": 0,
                        "credits_deducted": 0,
                        "credits_remaining": profile.credits,
                        "games": []
                    },
                    status=status.HTTP_200_OK
                )

    except Profile.DoesNotExist:
        logger.error(f"Profile not found for user {user.username}")
        return Response(
            {"error": "User profile not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error in fetch_games: {str(e)}")
        return Response(
            {"error": "Failed to fetch games. Please try again later."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_games_view(request):
    """
    Fetch games specific to the logged-in user.
    """
    user = request.user
    platform = request.query_params.get('platform', 'all')
    
    # Base query filtering by user
    games = Game.objects.filter(user=user)
    
    # Apply platform filter if specified
    if platform != 'all':
        games = games.filter(platform=platform)
    
    games = games.order_by("-date_played")
    
    games_data = [
        {
            "id": game.id,
            "white": game.white,
            "black": game.black,
            "result": game.result,
            "date_played": game.date_played,
            "platform": game.platform,
            "analysis": game.analysis
        }
        for game in games
    ]
    return Response({"games": games_data}, status=status.HTTP_200_OK)

@rate_limit(endpoint_type='ANALYSIS')
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_game(request, game_id):
    """
    Endpoint to analyze a specific game by its ID.
    """
    try:
        user = request.user
        depth = request.data.get("depth", 20) if request.method == "POST" else 20
        use_ai = request.data.get("use_ai", True) if request.method == "POST" else True

        # Fetch the game from the database
        try:
            game = Game.objects.get(id=game_id, user=user)
            
            # Check if game already has analysis and feedback
            if game.analysis:
                logger.info(f"Returning existing analysis for game {game_id}")
                return Response({
                    "message": "Analysis retrieved from cache",
                    "analysis": game.analysis,
                    "feedback": game.feedback if hasattr(game, 'feedback') else generate_feedback_without_ai(game.analysis)
                }, status=status.HTTP_200_OK)
                
        except Game.DoesNotExist:
            return Response({"error": "Game not found or unauthorized access."}, status=status.HTTP_404_NOT_FOUND)

        # Check if user has enough credits
        try:
            profile = Profile.objects.get(user=user)
            if profile.credits < 1:  # Analysis costs 1 credit
                return Response({
                    "error": "Insufficient credits. Please purchase more credits to analyze games.",
                    "credits": profile.credits
                }, status=status.HTTP_400_BAD_REQUEST)
        except Profile.DoesNotExist:
            return Response({"error": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)

        # Initialize GameAnalyzer
        analyzer = GameAnalyzer()
        analysis_results = {}

        try:
            logger.info("Analyzing game %s", game_id)
            start_time = datetime.utcnow()
            
            # Analyze the game
            analysis_results = analyzer.analyze_games([game], depth=depth)
            
            analysis_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info("Analysis completed in %.2f seconds", analysis_time)
            
            if not analysis_results or game_id not in analysis_results:
                return Response({"error": "Analysis failed to produce results."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Generate comprehensive feedback
            feedback = analyzer.generate_feedback(analysis_results[game_id])
            
            # Try AI feedback if requested
            if use_ai:
                try:
                    profile, _ = Profile.objects.get_or_create(
                        user=user,
                        defaults={
                            'rating': 1500,
                            'total_games': 0,
                            'preferred_openings': []
                        }
                    )
                    
                    # Generate AI feedback using the feedback generator
                    ai_feedback = ai_feedback_generator.generate_personalized_feedback(
                        game_analysis=analysis_results[game_id],
                        player_profile={
                            "username": user.username,
                            "rating": profile.rating,
                            "total_games": profile.total_games,
                            "preferred_openings": profile.preferred_openings
                        }
                    )
                    feedback["ai_suggestions"] = ai_feedback
                except Exception as e:
                    logger.warning("AI feedback generation failed, falling back to standard analysis: %s", str(e))
                    feedback["ai_suggestions"] = generate_feedback_without_ai(
                        analysis_results[game_id],
                        {
                            "average_accuracy": feedback.get("opening", {}).get("accuracy", 0),
                            "common_mistakes": {
                                "blunders": feedback.get("blunders", 0),
                                "mistakes": feedback.get("mistakes", 0),
                                "inaccuracies": feedback.get("inaccuracies", 0),
                                "time_pressure": len(feedback.get("time_management", {}).get("time_pressure_moves", []))
                            }
                        }
                    )
            else:
                feedback["ai_suggestions"] = generate_feedback_without_ai(
                    analysis_results[game_id],
                    {
                        "average_accuracy": feedback.get("opening", {}).get("accuracy", 0),
                        "common_mistakes": {
                            "blunders": feedback.get("blunders", 0),
                            "mistakes": feedback.get("mistakes", 0),
                            "inaccuracies": feedback.get("inaccuracies", 0),
                            "time_pressure": len(feedback.get("time_management", {}).get("time_pressure_moves", []))
                        }
                    }
                )

            # Update game with analysis results and feedback
            game.analysis = analysis_results[game_id]
            game.feedback = feedback  # Save feedback for future use
            game.save()

            # Deduct credits
            profile.credits -= 1
            profile.save()

            # Create transaction record
            Transaction.objects.create(
                user=user,
                transaction_type='analysis',
                credits=1,
                status='completed'
            )
            
            return Response({
                "message": "Analysis completed successfully!",
                "analysis": analysis_results[game_id],
                "feedback": feedback,
                "credits_remaining": profile.credits
            }, status=status.HTTP_200_OK)
        finally:
            try:
                analyzer.close_engine()
            except Exception as e:
                logger.error("Error closing engine: %s", str(e))
    except Exception as e:
        logger.error("Error in analyze_game_view: %s", str(e), exc_info=True)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@rate_limit(endpoint_type='ANALYSIS')
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def batch_analyze(request):
    """
    Endpoint to analyze a batch of games.
    """
    try:
        user = request.user
        num_games = int(request.data.get("num_games", 10))
        use_ai = request.data.get("use_ai", True)
        depth = request.data.get("depth", 20)

        # Validate num_games
        try:
            num_games = int(num_games)
            if num_games <= 0:
                return Response({"error": "Invalid number of games value."}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError):
            return Response({"error": "Invalid number of games value."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch games for the user
        games = Game.objects.filter(user=user).order_by("-date_played")[:num_games]
        
        # Return empty results if no games found
        if not games.exists():
            return Response({
                "message": "No games found for analysis.",
                "results": {
                    "individual_games": {},
                    "overall_stats": {
                        "total_games": 0,
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
                }
            }, status=status.HTTP_200_OK)

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
                # Calculate average accuracy based on good moves vs total moves
                total_good_moves = 0
                total_moves = 0
                for game_feedback in feedback_results.values():
                    moves = len(game_feedback.get("opening", {}).get("played_moves", []))
                    mistakes = (
                        game_feedback.get("blunders", 0) * 3 +  # Blunders count triple
                        game_feedback.get("mistakes", 0) * 2 +  # Mistakes count double
                        game_feedback.get("inaccuracies", 0)    # Inaccuracies count once
                    )
                    total_moves += moves
                    total_good_moves += max(0, moves - mistakes)
                
                overall_stats["average_accuracy"] = (total_good_moves / total_moves * 100) if total_moves > 0 else 0
                
                # Normalize mistake counts
                for mistake_type in overall_stats["common_mistakes"]:
                    overall_stats["common_mistakes"][mistake_type] /= num_analyzed_games

                # Generate improvement areas
                if overall_stats["common_mistakes"]["blunders"] > 0.5:
                    overall_stats["improvement_areas"].append({
                        "area": "Tactical Awareness",
                        "description": "Focus on reducing tactical oversights and blunders. Consider practicing tactical puzzles daily."
                    })
                if overall_stats["common_mistakes"]["mistakes"] > 1:
                    overall_stats["improvement_areas"].append({
                        "area": "Strategic Planning",
                        "description": "Work on positional understanding and long-term planning. Study master games in your preferred openings."
                    })
                if overall_stats["common_mistakes"]["time_pressure"] > 0.3:
                    overall_stats["improvement_areas"].append({
                        "area": "Time Management",
                        "description": "Improve time management, especially in critical positions. Practice playing games with increment."
                    })

                # Identify strengths
                if overall_stats["average_accuracy"] > 70:
                    overall_stats["strengths"].append({
                        "area": "Overall Accuracy",
                        "description": "Strong overall play with consistent move quality"
                    })
                if overall_stats["wins"] / num_analyzed_games > 0.5:
                    overall_stats["strengths"].append({
                        "area": "Competitive Performance",
                        "description": "Good win rate showing strong competitive ability"
                    })
                if overall_stats["common_mistakes"]["blunders"] < 0.3:
                    overall_stats["strengths"].append({
                        "area": "Tactical Solidity",
                        "description": "Strong tactical awareness with few major oversights"
                    })
                if overall_stats["common_mistakes"]["time_pressure"] < 0.2:
                    overall_stats["strengths"].append({
                        "area": "Time Management",
                        "description": "Excellent time management across games"
                    })

            # Generate feedback (with or without AI)
            if use_ai:
                try:
                    # Get or create user profile
                    profile, created = Profile.objects.get_or_create(
                        user=user,
                        defaults={
                            'rating': 1500,
                            'total_games': 0,
                            'preferred_openings': []
                        }
                    )
                    
                    # Generate AI feedback using the feedback generator
                    ai_feedback = ai_feedback_generator.generate_personalized_feedback(
                        game_analysis=analysis_results,
                        player_profile={
                            "username": user.username,
                            "rating": profile.rating,
                            "total_games": profile.total_games,
                            "preferred_openings": profile.preferred_openings
                        }
                    )
                    dynamic_feedback = ai_feedback
                except Exception as e:
                    logger.error("Error generating AI feedback: %s", str(e))
                    # Fall back to non-AI feedback
                    dynamic_feedback = generate_feedback_without_ai(analysis_results, overall_stats)
                    overall_stats["ai_error"] = "AI feedback unavailable - using standard analysis"
            else:
                # Use non-AI feedback by default
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
    use_ai = request.data.get("use_ai", True)

    games = Game.objects.filter(id__in=game_ids, player=user)
    if not games.exists():
        return Response({"error": "No valid games found."}, status=404)

    analyzer = GameAnalyzer()
    batch_feedback = {}

    try:
        for game in games:
            game_analysis = GameAnalysis.objects.filter(game=game)
            if game_analysis.exists():
                feedback = analyzer.generate_feedback(game_analysis)
                
                # Generate AI feedback if requested
                if use_ai and os.getenv("OPENAI_API_KEY"):
                    try:
                        ai_feedback = ai_feedback_generator.generate_personalized_feedback(
                            game_analysis=game_analysis,
                            player_profile={
                                "username": user.username,
                                "rating": getattr(user.profile, "rating", None),
                                "total_games": getattr(user.profile, "total_games", 0),
                                "preferred_openings": getattr(user.profile, "preferred_openings", [])
                            }
                        )
                        feedback["ai_suggestions"] = ai_feedback
                    except Exception as e:
                        logger.error("Error generating AI feedback: %s", str(e))
                
                batch_feedback[game.id] = feedback
    finally:
        analyzer.close_engine()

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
    Return user-specific games and statistics for the dashboard.
    """
    user = request.user
    games = Game.objects.filter(user=user)
    
    # Calculate statistics
    total_games = games.count()
    analyzed_games = games.exclude(analysis__isnull=True).count()
    unanalyzed_games = total_games - analyzed_games
    
    # Calculate win/loss/draw statistics
    wins = games.filter(result__iexact='win').count()
    losses = games.filter(result__iexact='loss').count()
    draws = games.filter(result__iexact='draw').count()
    
    # Get recent games
    recent_games = games.order_by('-date_played')[:5].values(
        'id',
        'platform',
        'white',
        'black',
        'opponent',
        'result',
        'date_played',
        'opening_name',
        'analysis'
    )
    
    response_data = {
        'total_games': total_games,
        'analyzed_games': analyzed_games,
        'unanalyzed_games': unanalyzed_games,
        'statistics': {
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'win_rate': round((wins / total_games * 100) if total_games > 0 else 0, 2)
        },
        'recent_games': list(recent_games)
    }
    
    return Response(response_data, status=status.HTTP_200_OK)

@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated])
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

@rate_limit(endpoint_type='CREDITS')
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_credits(request):
    """Get the current user's credit balance."""
    try:
        with transaction.atomic():
            profile = Profile.objects.select_for_update().get(user=request.user)
            logger.info(f"Retrieved credits for user {request.user.username}: {profile.credits}")
            return Response({'credits': profile.credits})
    except Profile.DoesNotExist:
        logger.error(f"Profile not found for user {request.user.username}")
        return Response({'error': 'Profile not found'}, status=404)
    except Exception as e:
        logger.error(f"Error getting credits for user {request.user.username}: {str(e)}")
        return Response({'error': str(e)}, status=500)

@rate_limit(endpoint_type='CREDITS')
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deduct_credits(request):
    """Deduct credits from the user's balance."""
    try:
        with transaction.atomic():
            amount = int(request.data.get('amount', 1))
            profile = Profile.objects.select_for_update().get(user=request.user)
            
            logger.info(f"Attempting to deduct {amount} credits from user {request.user.username} (current balance: {profile.credits})")
            
            if profile.credits < amount:
                logger.warning(f"Insufficient credits for user {request.user.username}: has {profile.credits}, needs {amount}")
                return Response({
                    'error': 'Insufficient credits',
                    'credits': profile.credits
                }, status=400)
            
            profile.credits -= amount
            profile.save()
            
            # Record the transaction
            Transaction.objects.create(
                user=request.user,
                transaction_type='usage',
                amount=0,
                credits=amount,
                status='completed'
            )
            
            logger.info(f"Successfully deducted {amount} credits. New balance: {profile.credits}")
            return Response({'credits': profile.credits})
    except Profile.DoesNotExist:
        logger.error(f"Profile not found for user {request.user.username}")
        return Response({'error': 'Profile not found'}, status=404)
    except ValueError:
        logger.error(f"Invalid amount provided: {request.data.get('amount')}")
        return Response({'error': 'Invalid amount'}, status=400)
    except Exception as e:
        logger.error(f"Error deducting credits: {str(e)}")
        return Response({'error': str(e)}, status=500)

@rate_limit(endpoint_type='CREDITS')
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def purchase_credits(request):
    """Create a checkout session for credit purchase."""
    try:
        package_id = request.data.get('package_id')
        logger.info(f"Attempting to create checkout session for package {package_id} for user {request.user.username}")
        
        if not package_id or package_id not in CREDIT_PACKAGES:
            logger.error(f"Invalid package ID: {package_id}")
            return Response({'error': f'Invalid package: {package_id}'}, status=400)
        
        if not settings.STRIPE_SECRET_KEY:
            logger.error("Stripe secret key not configured")
            return Response({'error': 'Payment processing is not configured'}, status=500)
        
        package = CREDIT_PACKAGES[package_id]
        try:
            checkout_session = PaymentProcessor.create_checkout_session(
                user_id=request.user.id,
                package_id=package_id,
                amount=package['price'],
                credits=package['credits']
            )
            
            logger.info(f"Successfully created checkout session for user {request.user.username}")
            return Response({
                'success': True,
                'checkout_url': checkout_session.url,
                'session_id': checkout_session.id
            })
        except Exception as e:
            logger.error(f"Error in PaymentProcessor: {str(e)}")
            return Response({
                'error': 'Error creating checkout session',
                'details': str(e)
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return Response({
            'error': 'Error processing request',
            'details': str(e)
        }, status=500)

@rate_limit(endpoint_type='CREDITS')
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_purchase(request):
    """Confirm a credit purchase and add credits to user's account."""
    session_id = request.data.get('session_id')
    logger.info(f"Confirming purchase for session {session_id} for user {request.user.username}")
    
    if not session_id:
        return Response({'error': 'Session ID required'}, status=400)
    
    try:
        # First check if this payment was already processed
        existing_transaction = Transaction.objects.filter(
            stripe_payment_id=session_id,
            status='completed'
        ).first()
        
        if existing_transaction:
            logger.warning(f"Payment {session_id} was already processed")
            profile = Profile.objects.get(user=request.user)
            return Response({
                'success': True,
                'credits': profile.credits,
                'added_credits': existing_transaction.credits,
                'already_processed': True
            })

        # Then verify the payment outside the transaction
        payment_data = PaymentProcessor.verify_payment(session_id)
        if not payment_data:
            logger.error(f"Invalid or expired session: {session_id}")
            return Response({'error': 'Invalid or expired session'}, status=400)

        # Finally, update credits in a transaction
        with transaction.atomic():
            profile = Profile.objects.select_for_update(nowait=True).get(user=request.user)
            old_credits = profile.credits
            profile.credits += payment_data['credits']
            profile.save()
            
            # Record the transaction
            new_transaction = Transaction.objects.create(
                user=request.user,
                transaction_type='purchase',
                amount=payment_data['amount'],
                credits=payment_data['credits'],
                status='completed',
                stripe_payment_id=session_id
            )
            
            logger.info(f"Purchase confirmed. Credits updated from {old_credits} to {profile.credits}")
            return Response({
                'success': True,
                'credits': profile.credits,
                'added_credits': payment_data['credits']
            })
            
    except Profile.DoesNotExist:
        logger.error(f"Profile not found for user {request.user.username}")
        return Response({'error': 'Profile not found'}, status=404)
    except transaction.TransactionManagementError as e:
        logger.error(f"Transaction error: {str(e)}")
        return Response({
            'error': 'Transaction error',
            'details': 'Please try again in a moment'
        }, status=500)
    except Exception as e:
        logger.error(f"Error confirming purchase: {str(e)}")
        return Response({
            'error': 'Error processing purchase',
            'details': str(e)
        }, status=500)

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

@rate_limit(endpoint_type='AUTH')
@api_view(['POST'])
def request_password_reset(request):
    """
    Handle password reset request.
    """
    try:
        email = request.data.get("email")
        if not email:
            return Response(
                {"error": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal that the user doesn't exist
            return Response(
                {"message": "If an account exists with this email, you will receive a password reset link."},
                status=status.HTTP_200_OK
            )

        # Generate password reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Build reset URL
        current_site = get_current_site(request)
        reset_url = f"http://{current_site.domain}/reset-password/{uid}/{token}/"
        
        # Send reset email
        try:
            send_password_reset_email(user, reset_url)
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            return Response(
                {"error": "Failed to send password reset email. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"message": "Password reset link has been sent to your email."},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        return Response(
            {"error": "An error occurred. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@csrf_exempt
@api_view(["POST"])
def reset_password(request):
    """
    Handle password reset with token.
    """
    try:
        uid = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not all([uid, token, new_password]):
            return Response(
                {"error": "All fields are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            uid = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"error": "invalid_token", "message": "Invalid reset link."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"error": "expired_token", "message": "Invalid or expired reset link."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate password complexity
        try:
            validate_password_complexity(new_password)
        except ValidationError as e:
            return Response(
                {"error": "complexity", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if new password is the same as old password
        if user.check_password(new_password):
            return Response(
                {"error": "same_password", "message": "New password cannot be the same as your old password."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password
        user.set_password(new_password)
        user.save()

        return Response(
            {"message": "Password has been reset successfully."},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        return Response(
            {"error": "server_error", "message": "An error occurred. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@csrf_exempt
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Handle user profile operations.
    """
    try:
        if request.method == "GET":
            profile = Profile.objects.get(user=request.user)
            return Response({
                "username": request.user.username,
                "email": request.user.email,
                "rating": profile.rating,
                "credits": profile.credits,
                "preferences": profile.preferences,
                "created_at": profile.created_at,
                "games_analyzed": Game.objects.filter(user=request.user).count(),
            })
        
        elif request.method == "PATCH":
            data = request.data
            user = request.user
            profile = Profile.objects.get(user=user)
            
            # Update username if provided and available
            new_username = data.get("username")
            if new_username and new_username != user.username:
                if User.objects.filter(username=new_username).exists():
                    return Response(
                        {"error": "Username already taken."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                user.username = new_username
            
            # Update preferences
            new_preferences = data.get("preferences")
            if new_preferences:
                profile.preferences = {
                    **profile.preferences,
                    **new_preferences
                }
            
            # Save changes
            user.save()
            profile.save()
            
            return Response({
                "message": "Profile updated successfully.",
                "username": user.username,
                "preferences": profile.preferences
            })
            
    except Profile.DoesNotExist:
        return Response(
            {"error": "Profile not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Profile operation error: {str(e)}")
        return Response(
            {"error": "An error occurred. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def send_password_reset_email(user, reset_url):
    """Send password reset email to user."""
    subject = "Reset your ChessMate password"
    html_message = render_to_string(
        "email/password_reset.html",
        {
            "user": user,
            "reset_url": reset_url
        }
    )
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )
