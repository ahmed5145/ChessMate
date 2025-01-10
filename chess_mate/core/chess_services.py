from datetime import datetime
from django.utils.timezone import make_aware, get_current_timezone
import requests
import ndjson
from typing import List, Dict, Any, Optional
from .models import Game

class ChessComService:
    BASE_URL = "https://api.chess.com/pub/player"
    
    @staticmethod
    def fetch_archives(username: str) -> List[str]:
        headers = {
            "User-Agent": "ChessMate/1.0 (your_email@example.com)"
        }
        url = f"{ChessComService.BASE_URL}/{username}/games/archives"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            archives = response.json().get("archives", [])
            print(f"Archives fetched: {archives}")
            return archives
        print(f"Failed to fetch archives - Status: {response.status_code}")
        return []

    @staticmethod
    def fetch_games(username: str, game_type: str) -> List[Dict[str, Any]]:
        archives = ChessComService.fetch_archives(username)
        games = []
        for archive_url in archives:
            games.extend(ChessComService.fetch_games_from_archive(archive_url, game_type))
        return games

    @staticmethod
    def fetch_games_from_archive(archive_url: str, game_type: str) -> List[Dict[str, Any]]:
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

class LichessService:
    BASE_URL = "https://lichess.org/api"
    
    @staticmethod
    def fetch_games(username: str, game_type: str) -> List[Dict[str, Any]]:
        url = f"{LichessService.BASE_URL}/games/user/{username}"
        params = {
            "max": 10,
            "perfType": LichessService.map_game_type(game_type)
        }
        headers = {"Accept": "application/x-ndjson"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        games = []
        for line in response.iter_lines():
            if line:  # Skip empty lines
                game_data = ndjson.loads(line.decode('utf-8'))
                if isinstance(game_data, list):
                    games.extend(game_data)
                else:
                    games.append(game_data)
        return games

    @staticmethod
    def map_game_type(chess_com_type: str) -> str:
        # Map Chess.com game types to Lichess variants
        mapping = {
            "bullet": "bullet",
            "blitz": "blitz",
            "rapid": "rapid",
            "classical": "classical"
        }
        return mapping.get(chess_com_type, "rapid")

def save_game(game: Dict[str, Any], username: str, user, platform: str) -> Optional[Game]:
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
        
    except Exception as e:
        print(f"Error saving game: {str(e)}")
        return None