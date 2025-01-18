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
                opening_name = game.headers.get("Opening", "Unknown Opening")

            board = game.board()
            if not board:
                raise ValueError("Failed to initialize board from PGN")

            analysis_results = []
            last_score = None
            critical_positions = []
            time_controls = game.headers.get("TimeControl", "").split("+")
            initial_time = int(time_controls[0]) if time_controls and time_controls[0].isdigit() else 600
            increment = int(time_controls[1]) if len(time_controls) > 1 and time_controls[1].isdigit() else 0

            for move_number, node in enumerate(game.mainline(), start=1):
                move = node.move
                if not board.is_legal(move):
                    raise ValueError(f"Illegal move {move.uci()} encountered in position: {board.fen()}")
                
                # Time management analysis
                time_left = node.clock() if hasattr(node, "clock") else None
                time_spent = node.clock() - last_time if hasattr(node, "clock") and last_time is not None else None
                last_time = node.clock() if hasattr(node, "clock") else None

                board.push(move)
                info = engine.analyse(board, chess.engine.Limit(depth=depth))
                score = (
                    info["score"].white().score(mate_score=10000)
                    if player_color == "white"
                    else info["score"].black().score(mate_score=10000)
                )

                # Evaluate position criticality
                is_critical = False
                if last_score is not None:
                    score_diff = abs(score - last_score)
                    if score_diff > 200 or board.is_check() or board.is_capture(move):
                        is_critical = True
                        critical_positions.append(move_number)

                evaluation_trend = None
                if last_score is not None:
                    if score > last_score + 50:
                        evaluation_trend = "improving"
                    elif score < last_score - 50:
                        evaluation_trend = "worsening"
                    else:
                        evaluation_trend = "neutral"

                last_score = score

                # Enhanced move analysis
                analysis_results.append({
                    "move": board.san(move) if board.is_legal(move) else move.uci(),
                    "score": score,
                    "depth": depth,
                    "is_capture": board.is_capture(move),
                    "is_check": board.is_check(),
                    "is_critical": is_critical,
                    "move_number": move_number,
                    "evaluation_trend": evaluation_trend,
                    "time_spent": time_spent,
                    "time_left": time_left,
                    "piece_moved": board.piece_at(move.from_square).symbol() if board.piece_at(move.from_square) else None,
                    "position_complexity": len(list(board.legal_moves))
                })

            return analysis_results, opening_name
        except ValueError as ve:
            logger.error("Error analyzing single game (ValueError): %s", str(ve))
            raise
        except chess.engine.EngineError as e:
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
        """
        feedback = {
            "mistakes": 0,
            "blunders": 0,
            "inaccuracies": 0,
            "time_management": {
                "avg_time_per_move": 0,
                "critical_moments": [],
                "time_pressure_moves": [],
                "suggestion": ""
            },
            "opening": {
                "played_moves": [],
                "accuracy": 0,
                "suggestion": ""
            },
            "tactical_opportunities": [],
            "endgame": {
                "evaluation": "",
                "accuracy": 0,
                "suggestion": ""
            },
            "positional_play": {
                "piece_activity": 0,
                "pawn_structure": 0,
                "king_safety": 0,
                "suggestion": ""
            }
        }

        total_moves = len(game_analysis)
        move_scores = []
        total_time = 0
        critical_moments = []

        for move_data in game_analysis:
            move_scores.append(move_data["score"])
            
            # Time management analysis
            if move_data.get("time_spent"):
                total_time += move_data["time_spent"]
                if move_data.get("is_critical") and move_data["time_spent"] < 10:
                    feedback["time_management"]["critical_moments"].append(
                        f"Move {move_data['move_number']}: Quick move in critical position"
                    )
                if move_data.get("time_left") and move_data["time_left"] < 30:
                    feedback["time_management"]["time_pressure_moves"].append(move_data["move_number"])

            # Mistakes analysis
            if len(move_scores) > 1:
                score_diff = abs(move_scores[-1] - move_scores[-2])
                if score_diff > 200:
                    feedback["blunders"] += 1
                elif 100 < score_diff <= 200:
                    feedback["mistakes"] += 1
                elif 50 < score_diff <= 100:
                    feedback["inaccuracies"] += 1

            # Opening analysis
            if move_data["move_number"] <= 10:
                feedback["opening"]["played_moves"].append(move_data["move"])
                if move_data["score"] > 0:
                    feedback["opening"]["accuracy"] += 1

            # Tactical opportunities
            if move_data.get("is_critical"):
                critical_moments.append(move_data["move_number"])
                if len(move_scores) > 1 and abs(move_scores[-1] - move_scores[-2]) > 100:
                    feedback["tactical_opportunities"].append(
                        f"Missed tactical opportunity on move {move_data['move_number']}"
                    )

            # Endgame analysis
            if move_data["move_number"] > total_moves * 0.7:
                if move_data["score"] > 0:
                    feedback["endgame"]["accuracy"] += 1

            # Positional play analysis
            if move_data.get("position_complexity"):
                if move_data["position_complexity"] > 30:
                    feedback["positional_play"]["piece_activity"] += 1
                if move_data.get("is_check"):
                    feedback["positional_play"]["king_safety"] -= 1

        # Calculate averages and generate suggestions
        if total_moves > 0:
            feedback["time_management"]["avg_time_per_move"] = total_time / total_moves
            feedback["opening"]["accuracy"] = (feedback["opening"]["accuracy"] / min(10, total_moves)) * 100
            if feedback["endgame"]["accuracy"] > 0:
                feedback["endgame"]["accuracy"] = (feedback["endgame"]["accuracy"] / (total_moves * 0.3)) * 100
            
            # Normalize positional play scores
            feedback["positional_play"]["piece_activity"] = (feedback["positional_play"]["piece_activity"] / total_moves) * 100
            feedback["positional_play"]["king_safety"] = max(0, 100 + (feedback["positional_play"]["king_safety"] * 10))

        # Generate suggestions based on analysis
        feedback["time_management"]["suggestion"] = self._generate_time_management_suggestion(
            feedback["time_management"]
        )
        feedback["opening"]["suggestion"] = self._generate_opening_suggestion(
            feedback["opening"]
        )
        feedback["endgame"]["suggestion"] = self._generate_endgame_suggestion(
            feedback["endgame"]
        )
        feedback["positional_play"]["suggestion"] = self._generate_positional_suggestion(
            feedback["positional_play"]
        )

        return feedback

    def _generate_time_management_suggestion(self, time_data):
        avg_time = time_data["avg_time_per_move"]
        critical_moments = len(time_data["critical_moments"])
        time_pressure = len(time_data["time_pressure_moves"])

        if critical_moments > 3:
            return "You're making quick moves in critical positions. Take more time to evaluate complex positions."
        elif time_pressure > 5:
            return "You're getting into time trouble frequently. Try to manage your time better in the opening and middlegame."
        elif avg_time > 45:
            return "You're spending too much time on some moves. Try to make decisions more quickly in clear positions."
        else:
            return "Your time management is generally good. Keep balancing quick play with careful consideration in critical positions."

    def _generate_opening_suggestion(self, opening_data):
        accuracy = opening_data["accuracy"]
        if accuracy < 50:
            return "Your opening play needs improvement. Study common opening principles and popular lines in your repertoire."
        elif accuracy < 80:
            return "Your opening play is decent but could be more accurate. Focus on understanding the key ideas behind your chosen openings."
        else:
            return "Your opening play is strong. Consider expanding your repertoire with more complex variations."

    def _generate_endgame_suggestion(self, endgame_data):
        accuracy = endgame_data["accuracy"]
        if accuracy < 50:
            return "Your endgame technique needs work. Practice basic endgame positions and principles."
        elif accuracy < 80:
            return "Your endgame play is solid but could be more precise. Study typical endgame patterns and techniques."
        else:
            return "Your endgame technique is strong. Focus on maximizing your advantages in winning positions."

    def _generate_positional_suggestion(self, positional_data):
        """Generate suggestion based on positional play data."""
        piece_activity = positional_data["piece_activity"]
        king_safety = positional_data["king_safety"]
        
        if king_safety < 60:
            return "Focus on king safety and avoiding unnecessary checks. Consider castle timing and pawn structure around the king."
        elif piece_activity < 50:
            return "Work on piece coordination and activity. Look for opportunities to improve piece placement and control central squares."
        else:
            return "Your positional understanding is good. Continue focusing on piece coordination and maintaining a solid pawn structure."

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
