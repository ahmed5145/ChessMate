from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
import requests
from .models import *
from .utils import analyze_game
from io import StringIO

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
    archives = fetch_archives(username)
    all_games = []

    if archives:
        for archive in archives:
            games = fetch_games_from_archive_by_type(archive, game_type)
            all_games.extend(games)
    
    if all_games:
        return JsonResponse({"games": all_games}, safe=False)
    else:
        return JsonResponse({"message": f"No {game_type} games found for the specified user."}, status=404)

def analyze_game_view(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    pgn = StringIO(game.pgn)  # Treat PGN as a file-like object
    analysis = analyze_game(pgn)  # Pass the file-like object directly
    
    # Save the analysis results to the database
    for move_analysis in analysis:
        GameAnalysis.objects.create(
            game=game,
            move=move_analysis['move'],
            score=move_analysis['score'],
            depth=move_analysis['depth']
        )
    
    return JsonResponse({'status': 'success', 'analysis': analysis})

def bulk_analyze_view(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    games = player.games.all()
    bulk_analysis = {}

    for game in games:
        pgn = StringIO(game.pgn)  # Treat PGN as a file-like object
        analysis = analyze_game(pgn)  # Pass the file-like object directly
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
