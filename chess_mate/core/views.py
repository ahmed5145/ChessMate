from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
import requests
from .models import Player, Game, GameAnalysis, Profile
from .utils import analyze_game, generate_feedback
from io import StringIO
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

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

import requests

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def fetch_games(request):
    """
    Fetch games from Chess.com or Lichess APIs based on the username and platform provided.
    """
    user = request.user
    platform = request.data.get("platform")  # "chess.com" or "lichess"
    username = request.data.get("username")

    if not platform or not username:
        return Response({"error": "Platform and username are required."}, status=status.HTTP_400_BAD_REQUEST)

    games = []
    try:
        if not username:
            return JsonResponse({"error": "Username is required."}, status=400)
        
        if platform == "chess.com":
            url = f"https://api.chess.com/pub/player/{username}/games"
            response = requests.get(url)
            if response.status_code == 200:
                games = response.json().get("games", [])
        elif platform == "lichess":
            url = f"https://lichess.org/api/games/user/{username}?max=10"
            response = requests.get(url, headers={"Accept": "application/x-ndjson"})
            if response.status_code == 200:
                games = [game for game in response.iter_lines()]

        # Save games in the database
        for game in games:
            Game.objects.create(
                player=user,
                opponent=game.get("opponent", {}).get("username", "Unknown"),
                result=game.get("result", "Unknown"),
                played_at=game.get("end_time", None),
                opening_name=game.get("opening", {}).get("name", None),
                pgn=game.get("pgn", None),
                game_url=game.get("url", None),
                is_white=game.get("white", {}).get("username", "") == username,
            )
        return Response({"message": "Games successfully fetched and saved!"}, status=status.HTTP_201_CREATED)
    except Exception as e:
        print(f"Error fetching games: {str(e)}")
        return JsonResponse({"error": "Failed to fetch games. Please try again later."}, status=500)    

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
from django.contrib.auth.models import User
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


# Helper function to generate tokens for a user
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }

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

    # Ensure password complexity is validated
    try:
        validate_password_complexity(password)
    except ValidationError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            user = User.objects.create_user(username=username, email=email, password=password)
            Profile.objects.create(user=user)
        send_confirmation_email(user)
    except ValidationError:
        return Response({"error": "Failed to register user due to validation error."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response({"error": "Failed to register user due to an unexpected error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "User registered successfully! Please confirm your email."},
                    status=status.HTTP_201_CREATED)

# Helper function to send a confirmation email
def send_confirmation_email(user):
    subject = "Confirm Your Email"
    message = f"Hi {user.username},\n\nPlease confirm your email address to activate your account."
    recipient_list = [user.email]
    send_mail(subject, message, "your-email@example.com", recipient_list)


@ratelimit(key="ip", rate="5/m", method="POST", block=True)
@api_view(["POST"])
def login_view(request):
    """
    Handle user login
    """
    data = request.data
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return Response({"error": "Both email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"error": "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=user.username, password=password)
    if user is None:
        return Response({"error": "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST)

    tokens = get_tokens_for_user(user)
    return Response({"message": "Login successful!", "tokens": tokens}, status=status.HTTP_200_OK)



#================================== Testing Data ==================================
def games_view(request):
    games = [
        {"id": 1, "opponent": "Player1", "result": "Win"},
        {"id": 2, "opponent": "Player2", "result": "Loss"},
        {"id": 3, "opponent": "Player3", "result": "Draw"},
    ]
    return JsonResponse({"games": games})

def game_analysis_view(request, game_id):
    analysis = [
        {"move": "e4", "score": 0.3},
        {"move": "e5", "score": 0.2},
        {"move": "Nf3", "score": 0.5},
    ]
    return JsonResponse({"game_id": game_id, "analysis": analysis})

#================================== Dashboard ==================================
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
        }
        for game in games
    ]
    return Response({"games": games_data}, status=status.HTTP_200_OK)


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
