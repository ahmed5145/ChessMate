from django.shortcuts import render
from django.http import JsonResponse
import requests
from django.core.exceptions import ObjectDoesNotExist
from .models import Game, GameAnalysis, Profile
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .chess_services import ChessComService, LichessService, save_game
from .game_analyzer import GameAnalyzer


STOCKFISH_PATH = "/path/to/stockfish"

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
        return Response({"error": "Invalid game type. Allowed types: bullet, blitz, rapid, classical."},
                        status=status.HTTP_400_BAD_REQUEST)

    if not platform or not username:
        return Response({"error": "Platform and username are required."}, 
                        status=status.HTTP_400_BAD_REQUEST)

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
    except Exception as e:
        print(f"Error fetching games: {str(e)}")
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

        # Fetch the game from the database
        game = Game.objects.filter(id=game_id, player=user).first()

        if not game:
            return JsonResponse({"error": "Game is missing."}, status=404)

        # Initialize GameAnalyzer
        analyzer = GameAnalyzer(stockfish_path=STOCKFISH_PATH)

        # Perform analysis
        try:
            results = analyzer.analyze_games(game, depth=depth)
            return Response({"message": "Game analyzed successfully!", "results": results}, status=200)
        finally:
            analyzer.close_engine()

    except Game.DoesNotExist:
        return JsonResponse({"error": "Game not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def analyze_batch_games_view(request):
    """
    Analyze a batch of games for the authenticated user.
    """
    user = request.user
    depth = request.data.get("depth", 20)

    # Fetch games for the user
    games = Game.objects.filter(player=user)
    if not games.exists():
        return Response({"error": "No games found for analysis."}, status=404)

    analyzer = GameAnalyzer(STOCKFISH_PATH)
    try:
        results = analyzer.analyze_games(games, depth=depth)
        return Response({"message": "Batch analysis completed!", "results": results}, status=200)
    finally:
        analyzer.close_engine()

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
        return Response({"error": "Game not found."}, status=404)
    
    game_analysis = GameAnalysis.objects.filter(game=game)
    if not game_analysis.exists():
        return Response({"error": "Analysis not found for this game."}, status=404)
    
    analyzer = GameAnalyzer()
    feedback = analyzer.generate_feedback(game_analysis)

    return Response({"feedback": feedback}, status=200)

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
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from .validators import validate_password_complexity
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django_ratelimit.decorators import ratelimit
from django.db import transaction
import json


# Helper function to generate tokens for a user
def get_tokens_for_user(user):
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
        return Response({"error": f"Failed to register user due to validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"Unexpected error during registration: {str(e)}")
        return Response({"error": "Failed to register user due to an unexpected error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "User registered successfully! Please confirm your email."},
                    status=status.HTTP_201_CREATED)

# Helper function to send a confirmation email
def send_confirmation_email(user):
    subject = "Confirm Your Email"
    message = f"Hi {user.username},\n\nPlease confirm your email address to activate your account."
    recipient_list = [user.email]
    try:
        send_mail(subject, message, "your-email@example.com", recipient_list)
    except Exception as e:
        print(f"Error sending confirmation email: {str(e)}")  # Log the specific error
        raise ValidationError("Failed to send confirmation email. Please check your email settings and try again.") from e


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


from django.db.models import Q

@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_games_view(request):
    """
    Fetch games specific to the logged-in user.
    """
    user = request.user  # Extract the logged-in user
    games = Game.objects.filter(player=user).order_by("-played_at")  # Filter games by the player field
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
