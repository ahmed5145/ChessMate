"""
This module provides services for interacting with external chess platforms such as Chess.com 
and Lichess. It includes classes and methods to fetch game data, filter games by type, and 
save game details to the database.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from django.utils.timezone import make_aware, get_current_timezone
import requests
import ndjson  # type: ignore

from .models import Game

class ChessComService:
    """
    Service class to interact with Chess.com API.
    """
    BASE_URL = "https://api.chess.com/pub/player"

    @staticmethod
    def fetch_archives(username: str) -> List[str]:
        """
        Fetch the list of archives for a given username.
        """
        headers = {
            "User-Agent": "ChessMate/1.0 (your_email@example.com)"
        }
        url = f"{ChessComService.BASE_URL}/{username}/games/archives"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            archives = response.json().get("archives", [])
            print(f"Archives fetched: {archives}")
            return archives
        print(f"Failed to fetch archives - Status: {response.status_code}")
        return []

    @staticmethod
    def fetch_games(username: str, game_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch games for a given username and game type.
        
        Args:
            username: The username to fetch games for
            game_type: The type of games to fetch (bullet, blitz, rapid, classical, or all)
            limit: Maximum number of games to fetch (default: 10)
        """
        archives = ChessComService.fetch_archives(username)
        games = []
        for archive_url in archives:
            new_games = ChessComService.fetch_games_from_archive(archive_url, game_type)
            games.extend(new_games)
            if len(games) >= limit:
                break
        return games[:limit]  # Ensure we don't return more than the limit

    @staticmethod
    def fetch_games_from_archive(archive_url: str, game_type: str) -> List[Dict[str, Any]]:
        """
        Fetch games from a specific archive URL and filter by game type.
        """
        headers = {
            "User-Agent": "ChessMate/1.0 (your_email@example.com)"
        }
        response = requests.get(archive_url, headers=headers, timeout=10)
        if response.status_code == 200:
            games = response.json().get("games", [])
            if game_type == "all":
                filtered_games = games
            else:
                filtered_games = [game for game in games if game.get("time_class") == game_type]
            print(f"Games fetched: {len(filtered_games)} {game_type} games.")
            return filtered_games
        elif response.status_code == 403:
            print("403 Forbidden: Ensure proper headers are included and access is allowed.")
        else:
            print(f"Failed to fetch games - Status: {response.status_code}")
        return []

class LichessService:
    """
    Service class to interact with Lichess API.
    """
    BASE_URL = "https://lichess.org/api"

    @staticmethod
    def fetch_games(username: str, game_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch games for a given username and game type.
        
        Args:
            username: The username to fetch games for
            game_type: The type of games to fetch (bullet, blitz, rapid, classical, or all)
            limit: Maximum number of games to fetch (default: 10)
        """
        url = f"{LichessService.BASE_URL}/games/user/{username}"
        params = {
            "max": limit,  # Set the limit in the API request
            "perfType": LichessService.map_game_type(game_type) if game_type != "all" else None
        }
        # Remove None values from params
        params = {k: str(v) for k, v in params.items() if v is not None}
        
        headers = {"Accept": "application/x-ndjson"}

        response = requests.get(url,
                              headers=headers,
                              params=params,
                              timeout=10)
        response.raise_for_status()

        games = []
        for line in response.iter_lines():
            if line:  # Skip empty lines
                game_data = ndjson.loads(line.decode('utf-8'))
                if isinstance(game_data, list):
                    games.extend(game_data)
                else:
                    games.append(game_data)
            if len(games) >= limit:  # Stop once we have enough games
                break
        return games[:limit]  # Ensure we don't return more than the limit

    @staticmethod
    def map_game_type(chess_com_type: str) -> str:
        """
        Map Chess.com game types to Lichess variants.
        """
        mapping = {
            "bullet": "bullet",
            "blitz": "blitz",
            "rapid": "rapid",
            "classical": "classical"
        }
        return mapping.get(chess_com_type, "rapid")

def save_game(game: Dict[str, Any], username: str, user) -> Optional[Game]:
    """
    Save a game to the database.
    """
    try:
        end_time = game.get("end_time")
        played_at = None

        if isinstance(end_time, (int, str)):
            naive_datetime = (
                datetime.fromtimestamp(end_time)
                if isinstance(end_time, int)
                else datetime.fromisoformat(end_time)
            )
            played_at = make_aware(naive_datetime, timezone=get_current_timezone())

        game_url = game.get("url")
        if not game_url or Game.objects.filter(game_url=game_url).exists():
            return None

        white_player = game.get("white", {}).get("username", "").lower()
        black_player = game.get("black", {}).get("username", "").lower()

        is_white = username.lower() == white_player
        if not is_white and username.lower() != black_player:
            return None

        result = (
            game.get("white" if is_white else "black", {})
            .get("result", "unknown")
        )

        final_result = (
            "Win" if result == "win"
            else "Loss" if result in ["checkmated", "timeout"]
            else "Draw"
        )

        opponent = black_player if is_white else white_player

        if Game.objects.filter(game_url=game_url).exists():
            print(f"Game with URL {game_url} already exists. Skipping.")
            return None

        return Game.objects.create(
            player=user,
            opponent=opponent or "Unknown",
            result=final_result,
            played_at=played_at,
            opening_name=game.get("opening", {}).get("name"),
            pgn=game.get("pgn"),
            game_url=game_url,
            is_white=is_white,
        )

    except (ValueError, TypeError, KeyError, requests.RequestException) as e:
        print(f"Error saving game: {str(e)}")
        return None
