import chess
import chess.pgn
import chess.engine
from django.http import JsonResponse
from django.conf import settings

def analyze_game(pgn):
    # Initialize the chess engine
    engine = chess.engine.SimpleEngine.popen_uci(settings.STOCKFISH_PATH)
    # Parse the PGN
    try:
        game = chess.pgn.read_game(pgn)
        if not game:
            raise ValueError("Invalid PGN format.")
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    board = game.board()

    analysis = []
    opening_name = None

    # Iterate through all moves in the game
    for move in game.mainline_moves():
        board.push(move)
        # Check if the game has an opening name
        if not opening_name:
            # Extract the opening name if available
            opening_name = board.opening().name if board.opening() else "Unknown Opening"
            
        # Analyze the current position
        info = engine.analyse(board, chess.engine.Limit(time=0.1))
        analysis.append({
            'move': move.uci(),
            'score': info['score'].relative.score(),  # Centipawn score
            'depth': info['depth'],
            'color': "white" if board.turn else "black"
        })

    engine.quit()
    return analysis, opening_name

def generate_feedback(analysis, is_white):
    opening_score = sum([move['score'] for move in analysis[:5]]) / 5
    inaccuracies = len([move for move in analysis if abs(move['score']) < 50])
    blunders = len([move for move in analysis if abs(move['score']) > 300])
    
    feedback = {
        'opening': "Strong opening play" if opening_score > 50 else "Needs improvement in openings.",
        'inaccuracies': f"{inaccuracies} inaccuracies. Try to maintain focus in tactical positions.",
        'blunders': f"{blunders} blunders. Consider reviewing blundered moves in-depth.",
        'play_as_white': "Solid play as White" if is_white else "Solid play as Black",
    }
    return feedback

def generate_feedback_without_ai(analysis_data, stats):
    """
    Generate structured feedback without using AI.
    
    Args:
        analysis_data (dict): Analysis data from the game
        stats (dict): Statistics about the game
        
    Returns:
        str: Formatted feedback string
    """
    template = """
Opening Analysis:
• Based on your opening moves, {opening_feedback}
• Key suggestion: {opening_suggestion}

Middlegame Strategy:
• Your positional play shows {middlegame_feedback}
• Focus areas: {middlegame_areas}

Tactical Awareness:
• Statistics show {tactical_feedback}
• Recommendation: {tactical_suggestion}

Time Management:
• Analysis indicates {time_feedback}
• Key improvement: {time_suggestion}

Endgame Technique:
• Your endgame play {endgame_feedback}
• Practice suggestion: {endgame_suggestion}
"""
    
    # Opening feedback
    if stats["common_mistakes"].get("mistakes", 0) > 1:
        opening_feedback = "you might benefit from deeper opening preparation"
        opening_suggestion = "study the main lines of your chosen openings"
    else:
        opening_feedback = "you have a good grasp of opening principles"
        opening_suggestion = "consider expanding your opening repertoire"

    # Middlegame feedback
    if stats.get("average_accuracy", 0) < 70:
        middlegame_feedback = "room for improvement in positional understanding"
        middlegame_areas = "piece coordination and pawn structure management"
    else:
        middlegame_feedback = "good strategic understanding"
        middlegame_areas = "complex position evaluation and long-term planning"

    # Tactical feedback
    blunders = stats["common_mistakes"].get("blunders", 0)
    if blunders > 0.5:
        tactical_feedback = f"an average of {blunders:.1f} blunders per game"
        tactical_suggestion = "practice tactical puzzles daily"
    else:
        tactical_feedback = "good tactical awareness"
        tactical_suggestion = "work on finding more advanced tactical opportunities"

    # Time management
    time_pressure = stats["common_mistakes"].get("time_pressure", 0)
    if time_pressure > 0.3:
        time_feedback = "you often get into time trouble"
        time_suggestion = "practice better time allocation in the opening and middlegame"
    else:
        time_feedback = "generally good time management"
        time_suggestion = "fine-tune your time usage in critical positions"

    # Endgame feedback
    if stats.get("average_accuracy", 0) > 80:
        endgame_feedback = "shows strong technical understanding"
        endgame_suggestion = "study more complex endgame positions"
    else:
        endgame_feedback = "could benefit from more practice"
        endgame_suggestion = "focus on basic endgame principles and common patterns"

    return template.format(
        opening_feedback=opening_feedback,
        opening_suggestion=opening_suggestion,
        middlegame_feedback=middlegame_feedback,
        middlegame_areas=middlegame_areas,
        tactical_feedback=tactical_feedback,
        tactical_suggestion=tactical_suggestion,
        time_feedback=time_feedback,
        time_suggestion=time_suggestion,
        endgame_feedback=endgame_feedback,
        endgame_suggestion=endgame_suggestion
    )

