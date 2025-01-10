from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
import requests
from .models import Player, Game, GameAnalysis, Profile
from .utils import analyze_game, generate_feedback
from io import StringIO
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import ndjson
from datetime import datetime
from django.utils.timezone import make_aware, get_current_timezone

# Base URL for Chess.com API
BASE_URL = "https://api.chess.com/pub/player"

# Homepage view
def index(request):
    return HttpResponse("Welcome to ChessMate!")

# Function to fetch archives
def fetch_archives(username):
    headers = {
        "User-Agent": "ChessMate/1.0 (your_email@example.com)"
    }
    url = f"{BASE_URL}/{username}/games/archives"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        archives = response.json().get("archives", [])
        print(f"Archives fetched: {archives}")
        return archives
    else:
        print(f"Failed to fetch archives - Status: {response.status_code}")
        return []

# Function to fetch games from an archive by game type
def fetch_games_from_archive_by_type(archive_url, game_type):
    headers = {
        "User-Agent": "ChessMate/1.0 (your_email@example.com)"
    }
    response = requests.get(archive_url, headers=headers)
    if response.status_code == 200:
        games = response.json().get("games", [])
        filtered_games = [game for game in games if game.get("time_class") == game_type]
        print(f"Games fetched: {len(filtered_games)} {game_type} games.")
        return filtered_games
    elif response.status_code == 403:
        print("403 Forbidden: Ensure proper headers are included and access is allowed.")
    else:
        print(f"Failed to fetch games - Status: {response.status_code}")
    return []


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
        return Response({"error": "Platform and username are required."}, status=status.HTTP_400_BAD_REQUEST)

    games = []
    try:
        if platform == "chess.com":
            archives = fetch_archives(username)
            for archive_url in archives:
                games.extend(fetch_games_from_archive_by_type(archive_url, game_type))
        elif platform == "lichess": #TODO: Debug Lichess API fetching and implement game_type-specific fetching logic
            url = f"https://lichess.org/api/games/user/{username}?max=10"
            response = requests.get(url, headers={"Accept": "application/x-ndjson"})
            response.raise_for_status()  # Raise HTTP errors
            ndjson_parser = ndjson.Reader(response.iter_lines())
            games = list(ndjson_parser)

        # Save games in the database
        for game in games:
            try:
                end_time = game.get("end_time", None)
                played_at = None
                if isinstance(end_time, int):
                    naive_datetime = datetime.fromtimestamp(end_time)
                    played_at = make_aware(naive_datetime, timezone=get_current_timezone())
                elif isinstance(end_time, str):
                    naive_datetime = datetime.fromisoformat(end_time)
                    played_at = make_aware(naive_datetime, timezone=get_current_timezone())
                    
                game_url = game.get("url", None)
                
                white_player = game.get("white", {}).get("username", "").lower()
                black_player = game.get("black", {}).get("username", "").lower()
                
                is_white = username.lower() == white_player
                if not is_white and username.lower() != black_player:
                    print(f"Username {username} does not match white or black player. Skipping game.")
                    continue
                
                if is_white:
                    result = game.get("white", {}).get("result", "unknown")
                else:
                    result = game.get("black", {}).get("result", "unknown")
                
                if result == "win":
                    final_result = "Win"
                elif result in ["checkmated", "timeout"]:
                    final_result = "Loss"
                else:
                    final_result = "Draw"
                    
                opponent = black_player if is_white else white_player

                if not Game.objects.filter(game_url=game_url).exists():
                    # Save the game
                    Game.objects.create(
                        player=user,
                        opponent=opponent or "Unknown",
                        result=final_result,
                        played_at=played_at,
                        opening_name=game.get("opening", {}).get("name", None),
                        pgn=game.get("pgn", None),
                        game_url=game_url,
                        is_white=is_white,
                    )

                else:
                    print(f"Game with URL {game_url} already exists. Skipping.")
            except Exception as e:
                print(f"Error saving game: {str(e)}")
        return Response({"message": "Games successfully fetched and saved!"}, status=status.HTTP_201_CREATED)
    except requests.exceptions.HTTPError as http_err:
        return Response({"error": f"HTTP error: {http_err}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"Error fetching games: {str(e)}")
        return JsonResponse({"error": "Failed to fetch games. Please try again later."}, status=500)    

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
    Analyze a specific game for the logged-in user.
    """
    user = request.user
    try:
        game = Game.objects.get(id=game_id, player=user)
    except Game.DoesNotExist:
        return Response({"error": "Game not found."}, status=status.HTTP_404_NOT_FOUND)

    # Mock analysis (replace with actual logic or API calls)
    analysis = [
        {"move": "e4", "score": 0.3},
        {"move": "e5", "score": 0.2},
        {"move": "Nf3", "score": 0.5},
    ]
    game_analysis = GameAnalysis.objects.create(game=game, analysis_data=analysis)
    return Response({"message": "Game analyzed successfully!", "analysis": analysis}, status=status.HTTP_201_CREATED)

@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def bulk_analyze_view(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    games = player.games.all()
    bulk_analysis = {}

    for game in games:
        pgn = StringIO(game.pgn)  # Treat PGN as a file-like object
        analysis, _ = analyze_game(pgn)  # Pass the file-like object directly
        bulk_analysis[game.id] = analysis

        # Save the analysis results to the database
        for move_analysis in analysis:
            GameAnalysis.objects.create(
                game=game,
                move=move_analysis['move'],
                score=move_analysis['score'],
                depth=move_analysis['depth']
            )

    return JsonResponse({'status': 'success', 'analysis': bulk_analysis})

@csrf_exempt  # Add this decorato
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def game_feedback_view(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    analyses = GameAnalysis.objects.filter(game=game).order_by('id')
    
    # Convert analyses to a list of dicts
    analysis_data = [
        {'move': a.move, 'score': a.score, 'depth': a.depth} 
        for a in analyses
    ]
    
    feedback = generate_feedback(analysis_data, game.is_white)
    return JsonResponse({'feedback': feedback})


#==================================Login Logic==================================
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework.decorators import api_view
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
    Handle user registration
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
        raise ValidationError("Failed to send confirmation email. Please check your email settings and try again.")


@csrf_exempt
@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def login_view(request):
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
            except User.DoesNotExist:
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
    Return user-specific games
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
    Fetch games specific to the logged-in user
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
    Fetch all available games (generic endpoint)
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
