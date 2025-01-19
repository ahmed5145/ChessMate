from django.test import TestCase
from django.contrib.auth.models import User
from .models import Game, Profile
from datetime import datetime
import uuid
import chess
from .game_analyzer import GameAnalyzer
from django.utils import timezone

class FeedbackTestCase(TestCase):
    def setUp(self):
        # Create a user first
        self.user = User.objects.create_user(
            username=f"test_user_{uuid.uuid4().hex[:8]}",
            password="test_pass",
            email="test@example.com"
        )
        # Delete any existing profile for this user
        Profile.objects.filter(user=self.user).delete()
        # Create a profile for the user
        Profile.objects.create(user=self.user, credits=10)
        # Create a game using the user
        self.game = Game.objects.create(
            user=self.user,
            platform='chess.com',
            game_id=uuid.uuid4().hex,
            white='testuser',
            black='test_opponent',
            result='win',
            pgn='1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7',
            date_played=timezone.now(),
            opening_name='Ruy Lopez',
            opponent='test_opponent'
        )

    def test_feedback_generation(self):
        try:
            analyzer = GameAnalyzer()
            analysis_results = analyzer.analyze_games([self.game])
            feedback = analyzer.generate_feedback(analysis_results[self.game.id])
            
            self.assertIsInstance(feedback, dict)
            self.assertIn('opening', feedback)
            self.assertIn('accuracy', feedback['opening'])
            self.assertIn('mistakes', feedback)
            self.assertIn('blunders', feedback)
            self.assertIn('time_management', feedback)
            self.assertIn('tactical_opportunities', feedback)
            self.assertIsInstance(feedback['tactical_opportunities'], list)
        except chess.engine.EngineTerminatedError:
            self.skipTest("Stockfish engine not available")
        finally:
            if analyzer:
                analyzer.close_engine()

