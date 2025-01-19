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
import httpx
import logging

from .models import Game

logger = logging.getLogger(__name__)

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
    def _extract_pgn_info(pgn: str) -> Dict[str, Any]:
        """Extract information from PGN headers."""
        info = {}
        try:
            # Extract UTC date and time
            utc_date = None
            utc_time = None
            opening_name = None
            
            for line in pgn.split('\n'):
                if line.startswith('[UTCDate'):
                    utc_date = line.split('"')[1]
                elif line.startswith('[UTCTime'):
                    utc_time = line.split('"')[1]
                elif line.startswith('[ECOUrl'):
                    eco_url = line.split('"')[1]
                    if 'openings/' in eco_url:
                        opening_name = eco_url.split('openings/')[1].replace('-', ' ')
            
            if utc_date and utc_time:
                info['datetime'] = f"{utc_date} {utc_time}"
            if opening_name:
                info['opening_name'] = opening_name
                
        except Exception as e:
            logger.error(f"Error extracting PGN info: {str(e)}")
            
        return info

    @staticmethod
    def fetch_games(username: str, game_type: str = "all", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch games from Chess.com API.
        """
        try:
            # First get the archives
            archives_url = f"https://api.chess.com/pub/player/{username}/games/archives"
            with httpx.Client() as client:
                archives_response = client.get(archives_url)
                archives_response.raise_for_status()
                archives = archives_response.json().get("archives", [])
                
                logger.info(f"Archives fetched: {archives}")
                
                if not archives:
                    logger.warning(f"No archives found for user {username}")
                    return []

                # Process archives in reverse order (newest first)
                formatted_games = []
                for archive_url in reversed(archives):
                    try:
                        games_response = client.get(archive_url)
                        games_response.raise_for_status()
                        games_data = games_response.json().get("games", [])
                        
                        logger.info(f"Processing archive {archive_url}, found {len(games_data)} games")
                        
                        # Filter and format games
                        for game in games_data:
                            # Skip if not the requested game type
                            if game_type != "all" and game.get("time_class") != game_type:
                                continue
                            
                            # Extract PGN info
                            pgn_info = ChessComService._extract_pgn_info(game.get("pgn", ""))
                            
                            # Determine opponent
                            white_username = game.get("white", {}).get("username", "Unknown")
                            black_username = game.get("black", {}).get("username", "Unknown")
                            opponent = black_username if username.lower() == white_username.lower() else white_username
                            
                            # Format the game data
                            formatted_game = {
                                "game_id": game.get("url", "").split("/")[-1],
                                "platform": "chess.com",
                                "white": white_username,
                                "black": black_username,
                                "opponent": opponent,
                                "result": ChessComService._format_result(
                                    game.get("white" if username.lower() == white_username.lower() else "black", {}).get("result", ""),
                                    username
                                ),
                                "pgn": game.get("pgn", ""),
                                "played_at": (
                                    datetime.strptime(pgn_info['datetime'], "%Y.%m.%d %H:%M:%S")
                                    if 'datetime' in pgn_info
                                    else make_aware(datetime.fromtimestamp(game.get("end_time", 0)), timezone=get_current_timezone())
                                ),
                                "opening_name": (
                                    pgn_info.get('opening_name')
                                    or game.get("opening", {}).get("name")
                                    or game.get("opening", {}).get("eco", {}).get("name", "Unknown Opening")
                                )
                            }
                            
                            logger.info(f"Formatted game: {formatted_game}")
                            formatted_games.append(formatted_game)
                            
                            if len(formatted_games) >= limit:
                                logger.info(f"Reached limit of {limit} games")
                                return formatted_games
                    except Exception as e:
                        logger.error(f"Error processing archive {archive_url}: {str(e)}")
                        continue
                
                logger.info(f"Total games fetched: {len(formatted_games)} {game_type} games")
                return formatted_games

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching games from Chess.com: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error fetching games from Chess.com: {str(e)}")
            raise

    @staticmethod
    def _format_result(result: str, username: str) -> str:
        """Format the game result."""
        if result == "win":
            return "win"
        elif result == "checkmated" or result == "resigned" or result == "timeout" or result == "abandoned":
            return "loss"
        elif result == "stalemate" or result == "agreed" or result == "repetition" or result == "insufficient":
            return "draw"
        else:
            return "unknown"

class LichessService:
    """
    Service class to interact with Lichess API.
    """
    BASE_URL = "https://lichess.org/api"

    @staticmethod
    def fetch_games(username: str, game_type: str = "all", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch games from Lichess API.
        """
        try:
            url = f"https://lichess.org/api/games/user/{username}"
            params = {
                "max": limit,
                "perfType": game_type if game_type != "all" else None,
                "opening": True,
                "clocks": True,
                "evals": True,
                "moves": True
            }
            
            with httpx.Client() as client:
                response = client.get(url, params={k: v for k, v in params.items() if v is not None})
                response.raise_for_status()
                
                games = response.json()
                formatted_games = []
                
                for game in games:
                    white_username = game.get("players", {}).get("white", {}).get("user", {}).get("name", "Unknown")
                    black_username = game.get("players", {}).get("black", {}).get("user", {}).get("name", "Unknown")
                    opponent = black_username if username.lower() == white_username.lower() else white_username
                    
                    formatted_game = {
                        "game_id": game.get("id"),
                        "platform": "lichess",
                        "white": white_username,
                        "black": black_username,
                        "opponent": opponent,
                        "result": LichessService._format_result(game.get("winner"), username),
                        "pgn": game.get("moves", ""),
                        "played_at": make_aware(datetime.fromtimestamp(game.get("createdAt", 0) / 1000), timezone=get_current_timezone()),
                        "opening_name": game.get("opening", {}).get("name") or game.get("opening", {}).get("eco", {}).get("name", "Unknown Opening")
                    }
                    formatted_games.append(formatted_game)
                    
                    if len(formatted_games) >= limit:
                        break
                
                return formatted_games

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching games from Lichess: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error fetching games from Lichess: {str(e)}")
            raise

    @staticmethod
    def _format_result(winner: Optional[str], username: str) -> str:
        """Format the game result."""
        if winner is None:
            return "draw"
        elif winner == username:
            return "win"
        else:
            return "loss"

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
