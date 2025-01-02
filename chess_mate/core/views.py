from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import requests

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

# Function to fetch games from an archive
def fetch_games_from_archive(archive_url):
    headers = {
        "User-Agent": "ChessMate/1.0 (your_email@example.com)"
    }
    response = requests.get(archive_url, headers=headers)
    if response.status_code == 200:
        games = response.json().get("games", [])
        print(f"Games fetched: {len(games)} games.")
        return games
    elif response.status_code == 403:
        print("403 Forbidden: Ensure proper headers are included and access is allowed.")
    else:
        print(f"Failed to fetch games - Status: {response.status_code}")
    return []

# View to fetch and return games for a specific username
def fetch_games(request, username):
    archives = fetch_archives(username)
    all_games = []

    if archives:
        for archive in archives:
            games = fetch_games_from_archive(archive)
            all_games.extend(games)
    
    if all_games:
        return JsonResponse({"games": all_games}, safe=False)
    else:
        return JsonResponse({"message": "No games found for the specified user."}, status=404)
