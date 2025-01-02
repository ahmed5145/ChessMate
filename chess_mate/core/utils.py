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

