from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
import requests
from .models import Player, Game, GameAnalysis
from .utils import analyze_game, generate_feedback
from io import StringIO
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes

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

# View to fetch and return games for a specific username and game type
def fetch_games(request, username, game_type):
    player, _ = Player.objects.get_or_create(username=username)
    archives = fetch_archives(username)
    all_games = []

    if archives:
        for archive in archives:
            games = fetch_games_from_archive_by_type(archive, game_type)
            for game_data in games:
                is_white = game_data['white']['username'] == username
                game, created = Game.objects.get_or_create(
                    player=player,
                    game_url=game_data['url'],
                    played_at=game_data['end_time'],  # Adjust time format
                    opponent=game_data['black']['username'] if is_white else game_data['white']['username'],
                    result=game_data['white']['result'] if is_white else game_data['black']['result'],
                    pgn=game_data['pgn'],
                    is_white=is_white
                )
                if created:
                    all_games.append(game_data)
    
    if all_games:
        return JsonResponse({"games": all_games}, safe=False)
    else:
        return JsonResponse({"message": f"No {game_type} games found for the specified user."}, status=404)

def analyze_game_view(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    pgn = StringIO(game.pgn)  # Treat PGN as a file-like object
    analysis, opening_name = analyze_game(pgn)  # Pass the file-like object directly
    
    # Save the opening name if not already set
    if not game.opening_name:
        game.opening_name = opening_name
        game.save()
        
    # Save the analysis results to the database
    for move_analysis in analysis:
        GameAnalysis.objects.create(
            game=game,
            move=move_analysis['move'],
            score=move_analysis['score'],
            depth=move_analysis['depth']
        )
    
    return JsonResponse({'status': 'success', 'analysis': analysis, 'opening': opening_name})

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

    user = User.objects.create_user(username=username, email=email, password=password)
    return Response({"message": "User registered successfully!"}, status=status.HTTP_201_CREATED)

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
