"""
This module provides functionality for analyzing chess games using the Stockfish engine.
It includes classes and methods to analyze single or multiple games, save analysis results to the
database, and generate feedback based on the analysis.
"""

import os
import io
import logging
import chess
import chess.engine
import chess.pgn
from django.db import DatabaseError
from .models import Game

logger = logging.getLogger(__name__)

STOCKFISH_PATH = os.getenv("STOCKFISH_PATH")

class GameAnalyzer:
    """
    Handles game analysis using Stockfish or external APIs.
    """

    def __init__(self, stockfish_path=STOCKFISH_PATH):
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        except (chess.engine.EngineError, ValueError) as e:
            logger.error("Failed to initialize Stockfish engine: %s", str(e))
            raise

    def analyze_games(self, games, depth=20):
        """
        Analyze one or multiple games.

        Args:
            games (Union[Game, QuerySet]): A single Game object or a QuerySet of Game objects.
            depth (int): Analysis depth.

        Returns:
            Dict: Mapping of game IDs to their analysis results.
        """
        if isinstance(games, Game):
            games = [games]

        analysis_results = {}
        try:
            with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
                engine.configure({"Threads": 2, "Hash": 128})
                for game in games:
                    if not game.pgn:
                        logger.warning("Game %s has no PGN. Skipping.", game.id)
                        continue

                    if game.analysis:
                        logger.info(
                            "Analysis for game %s already exists. Returning existing analysis.",
                            game.id
                        )
                        analysis_results[game.id] = game.analysis
                        continue

                    try:
                        player_color = "white" if game.is_white else "black"
                        results, opening_name = self._analyze_single_game(game.pgn, player_color, depth, engine)
                        game.opening_name = opening_name  # Save the opening name
                        self.save_analysis_to_db(game, results)
                        analysis_results[game.id] = results
                    except (ValueError, chess.engine.EngineError) as e:
                        logger.error("Error analyzing game %s: %s", game.id, str(e))
                        continue
        except (chess.engine.EngineError, ValueError) as e:
            logger.error("Error initializing Stockfish engine: %s", str(e))
            raise
        finally:
            self.close_engine()  # Ensure the engine is closed after analysis
        return analysis_results

    def _analyze_single_game(self, game_pgn, player_color="white", depth=20, engine=None):
        """
        Analyze a single game from PGN format.

        Args:
            game_pgn (str): The game's PGN string.
            depth (int): Analysis depth.
            engine (chess.engine.SimpleEngine): The Stockfish engine instance.

        Returns:
            List[dict]: List of analysis results for each move.
        """
        try:
            game_pgn = game_pgn.strip().replace("\r\n", "\n")
            pgn_stream = io.StringIO(game_pgn)
            game = chess.pgn.read_game(pgn_stream)
            if not game:
                raise ValueError("Invalid PGN format")

            # Extract and format opening from PGN headers
            opening_url = game.headers.get("ECOUrl", "Unknown Opening")
            if "openings/" in opening_url:
                opening_name = opening_url.split("openings/")[1].replace("-", " ")
            else:
                opening_name = "Unknown Opening"

            board = game.board()
            if not board:
                raise ValueError("Failed to initialize board from PGN")

            analysis_results = []
            last_score = None
            for move_number, move in enumerate(game.mainline_moves(), start=1):
                # Ensure move legality
                if not board.is_legal(move):
                    raise ValueError(
                        f"Illegal move {move.uci()} encountered in position: {board.fen()}"
                    )
                board.push(move)
                info = engine.analyse(board, chess.engine.Limit(depth=depth))
                score = (
                    info["score"].white().score(mate_score=10000)
                    if player_color == "white"
                    else info["score"].black().score(mate_score=10000)
                )
                evaluation_trend = None
                if last_score is not None:
                    if score > last_score:
                        evaluation_trend = "improving"
                    elif score < last_score:
                        evaluation_trend = "worsening"
                    else:
                        evaluation_trend = "neutral"
                last_score = score
                analysis_results.append({
                    "move": board.san(move) if board.is_legal(move) else move.uci(),
                    "score": score,
                    "depth": depth,
                    "is_capture": board.is_capture(move),
                    "move_number": move_number,
                    "evaluation_trend": evaluation_trend
                })
            return analysis_results, opening_name
        except ValueError as ve:
            logger.error("Error analyzing single game (ValueError): %s", str(ve))
            raise
        except (chess.engine.EngineError) as e:
            logger.error("Error analyzing single game: %s", str(e))
            raise

    def save_analysis_to_db(self, game, analysis_results):
        """
        Save analysis results to the database.

        Args:
            game (Game): The Game object.
            analysis_results (List[dict]): The analysis results.
        """
        try:
            game.analysis = analysis_results  # Store the analysis results as JSON
            game.save()
        except (DatabaseError, ValueError) as e:
            logger.error("Error saving analysis to database: %s", str(e))

    def generate_feedback(self, game_analysis):
        """
        Generate comprehensive feedback based on the game analysis.

        Args:
            game_analysis (QuerySet): QuerySet of GameAnalysis objects for a game.

        Returns:
            Dict: Feedback details for the game.
        """
        feedback = {
            "mistakes": 0,
            "blunders": 0,
            "inaccuracies": 0,
            "time_management": {},
            "opening": {},
            "tactical_opportunities": [],
            "endgame": {},
            "capitalization": {},
            "consistency": {}
        }

        total_moves = len(game_analysis)
        move_scores = []
        last_score = None

        for analysis in game_analysis:
            move_scores.append(analysis.score)

            # Mistakes, blunders, inaccuracies
            if last_score is not None:
                score_diff = abs(analysis.score - last_score)
                if score_diff > 200:
                    feedback["blunders"] += 1
                elif 100 < score_diff <= 200:
                    feedback["mistakes"] += 1
                elif 50 < score_diff <= 100:
                    feedback["inaccuracies"] += 1
            last_score = analysis.score

        # Consistency
        feedback["consistency"]["average_score"] = (
            sum(move_scores) / total_moves if total_moves else 0
        )
        # Time management (extract from GameAnalysis if available)
        times = [analysis.time_spent for analysis in game_analysis if analysis.time_spent]
        if times:
            avg_time = sum(times) / len(times)
            feedback["time_management"] = {
                "avg_time_per_move": avg_time,
                "suggestion": "Balance your time usage to avoid spending too much time on certain moves."
            }

        # Opening evaluation
        opening_moves = [analysis.move for analysis in game_analysis[:5]]
        feedback["opening"] = {
            "played_moves": opening_moves,
            "suggestion": "Review your opening for better preparation."
        }

        # Tactical opportunities
        feedback["tactical_opportunities"] = ["Detected tactical issue on move X."]  # Placeholder for actual tactics

        # Endgame
        feedback["endgame"] = {
            "evaluation": "Your endgame positioning was solid. Focus on pawn promotion techniques.",
            "suggestion": "Practice common endgame patterns like king and pawn vs king."
        }

        return feedback

    def close_engine(self):
        """Closes the Stockfish engine."""
        if self.engine:
            self.engine.quit()

# Placeholder for future enhancement to support asynchronous analysis using Celery
# from celery import shared_task

# @shared_task
# def analyze_games_async(game_ids, depth=20):
#     """
#     Asynchronously analyze multiple games.
#
#     Args:
#         game_ids (List[int]): List of game IDs to analyze.
#         depth (int): Analysis depth.
#
#     Returns:
#         Dict: Mapping of game IDs to their analysis results.
#     """
#     games = Game.objects.filter(id__in=game_ids)
#     analyzer = GameAnalyzer()
#     results = analyzer.analyze_games(games, depth=depth)
#     return results
