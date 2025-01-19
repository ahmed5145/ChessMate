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
from datetime import datetime
from typing import List, Dict, Any

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

    def analyze_move(self, board, move, depth=20):
        """Analyze a single move and return the evaluation."""
        try:
            start_time = datetime.utcnow()
            result = self.engine.analyse(board, chess.engine.Limit(depth=depth))
            time_spent = (datetime.utcnow() - start_time).total_seconds()
            
            # Get the score, using PovScore for proper initialization
            score_obj = result.get("score", chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE))
            score = score_obj.relative.score()
            is_mate = score_obj.relative.is_mate()
            
            return {
                "move": move.uci(),
                "score": score if not is_mate else (20000 if score > 0 else -20000),
                "depth": result.get("depth", 0),
                "time_spent": time_spent,
                "is_mate": is_mate,
                "is_capture": board.is_capture(move),
                "move_number": board.fullmove_number
            }
        except Exception as e:
            logger.error("Error analyzing move: %s", str(e))
            return None

    def analyze_games(self, games: List[Game], depth: int = 20) -> Dict[int, List[Dict[str, Any]]]:
        """
        Analyze a list of games.
        
        Args:
            games: List of Game objects to analyze
            depth: Depth of analysis (default: 20)
            
        Returns:
            Dictionary mapping game IDs to their analysis results
            
        Raises:
            ValueError: If no games are provided or if any game has invalid PGN data
        """
        if not games:
            raise ValueError("No games provided for analysis")
            
        results = {}
        for game in games:
            try:
                results[game.id] = self.analyze_single_game(game, depth)
            except Exception as e:
                logger.error(f"Error analyzing game {game.id}: {str(e)}")
                continue
        return results

    def analyze_single_game(self, game: Game, depth: int = 20) -> List[Dict[str, Any]]:
        """
        Analyze a single game.
        
        Args:
            game: Game object to analyze
            depth: Depth of analysis (default: 20)
            
        Returns:
            List of dictionaries containing analysis data for each move
            
        Raises:
            ValueError: If the game has no PGN data or if PGN is invalid
        """
        if not game.pgn:
            raise ValueError("No PGN data provided for analysis")

        board = chess.Board()
        moves = []
        analysis = []
        last_score = 0
        
        # Parse moves from PGN
        try:
            pgn = chess.pgn.read_game(io.StringIO(game.pgn))
            if not pgn:
                raise ValueError("Invalid PGN data: Could not parse game")
                    
            # Collect moves
            while pgn.next():
                moves.append(pgn.next().move)
                pgn = pgn.next()
            
            if not moves:
                raise ValueError("Invalid PGN data: No moves found")
        except Exception as e:
            raise ValueError(f"Invalid PGN data: {str(e)}")
        
        # Analyze each move
        for move in moves:
            move_analysis = self.analyze_move(board, move, depth)
            if move_analysis:
                # Calculate evaluation drop and mark critical moves
                current_score = move_analysis["score"]
                eval_drop = last_score - current_score
                
                move_analysis.update({
                    "evaluation_drop": eval_drop,
                    "is_mistake": eval_drop > 200,  # More than 2 pawns drop
                    "is_blunder": eval_drop > 400,  # More than 4 pawns drop
                    "is_critical": abs(current_score) > 150 or abs(eval_drop) > 150
                })
                
                analysis.append(move_analysis)
                last_score = current_score
            
            board.push(move)
        
        return analysis

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
            
            # Calculate opening accuracy based on move quality
            good_moves = total_moves - (feedback["blunders"] * 3 + feedback["mistakes"] * 2 + feedback["inaccuracies"])
            feedback["opening"]["accuracy"] = (good_moves / total_moves) * 100 if total_moves > 0 else 0
            
            # Calculate endgame accuracy similarly
            if feedback["endgame"]["accuracy"] > 0:
                endgame_moves = total_moves * 0.3
                endgame_good_moves = endgame_moves - (
                    feedback["blunders"] + feedback["mistakes"] + feedback["inaccuracies"]
                )
                feedback["endgame"]["accuracy"] = (endgame_good_moves / endgame_moves) * 100 if endgame_moves > 0 else 0
            
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
