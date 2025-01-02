from django.test import TestCase

from django.test import TestCase
from .models import Game, Player
from .utils import analyze_game, generate_feedback
import tempfile

class FeedbackTestCase(TestCase):
    def setUp(self):
        player = Player.objects.create(username="test_user")
        self.game = Game.objects.create(
            player=player,
            game_url="https://example.com/game",
            played_at="2025-01-01T12:00:00Z",
            opponent="test_opponent",
            result="win",
            pgn="1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7",
            is_white=True
        )
        self.pgn_content = """
        [Event "Test Game"]
        [Site "Example.com"]
        [Date "2025.01.01"]
        [Round "1"]
        [White "Player1"]
        [Black "Player2"]
        [Result "1-0"]

        1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 1-0
        """

    def test_feedback_generation(self):
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
            tmp.write(self.pgn_content)
            tmp.seek(0)
            analysis, _ = analyze_game(tmp)
            feedback = generate_feedback(analysis, self.game.is_white)
            self.assertIn('opening', feedback)
            self.assertIn('inaccuracies', feedback)

