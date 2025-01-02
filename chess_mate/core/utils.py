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

    # Iterate through all moves in the game
    for move in game.mainline_moves():
        board.push(move)
        # Analyze the current position
        info = engine.analyse(board, chess.engine.Limit(time=0.1))
        analysis.append({
            'move': move.uci(),
            'score': info['score'].relative.score(),  # Centipawn score
            'depth': info['depth']
        })

    engine.quit()
    return analysis

# Remove the example usage code
# with open("game.pgn") as pgn_file:
#     pgn = pgn_file.read()
#     analysis = analyze_game(pgn)
#     for move_analysis in analysis:
#         print(move_analysis)
