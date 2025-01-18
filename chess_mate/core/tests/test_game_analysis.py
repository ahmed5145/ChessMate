import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Game, Profile
from core.game_analyzer import GameAnalyzer
from datetime import datetime
import uuid
from django.db import transaction
import chess.engine

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
@pytest.mark.django_db(transaction=True)
def user():
    with transaction.atomic():
        username = f'testuser_{uuid.uuid4().hex[:8]}'
        user = User.objects.create_user(
            username=username,
            password='testpass123',
            email=f'{username}@test.com'
        )
        # Delete any existing profile for this user
        Profile.objects.filter(user=user).delete()
        # Create new profile
        Profile.objects.create(user=user, credits=10)
        return user

@pytest.fixture
@pytest.mark.django_db(transaction=True)
def game(user):
    with transaction.atomic():
        return Game.objects.create(
            player=user,  # Using User instance directly
            game_url=f'https://chess.com/game/{uuid.uuid4().hex}',
            played_at=datetime.now(),
            opponent='opponent1',
            result='win',
            pgn='1. e4 e5 2. Nf3 Nc6 3. Bb5',
            is_white=True,
            opening_name='Ruy Lopez'
        )

@pytest.fixture(scope='function')
def game_analyzer():
    analyzer = GameAnalyzer()
    yield analyzer
    try:
        analyzer.close_engine()
    except:
        pass

@pytest.mark.django_db(transaction=True)
class TestGameAnalysis:
    def test_analyze_game_view_unauthorized(self, api_client, game):
        url = reverse('analyze_game', args=[game.id])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_analyze_game_view_authorized(self, api_client, user, game):
        api_client.force_authenticate(user=user)
        url = reverse('analyze_game', args=[game.id])
        try:
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK
            assert 'analysis' in response.data
            assert 'feedback' in response.data
        except chess.engine.EngineTerminatedError:
            pytest.skip("Stockfish engine not available")

    def test_analyze_game_view_not_found(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('analyze_game', args=[999])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_analyze_game_view_insufficient_credits(self, api_client, user, game):
        with transaction.atomic():
            profile = Profile.objects.get(user=user)
            profile.credits = 0
            profile.save()

            api_client.force_authenticate(user=user)
            url = reverse('analyze_game', args=[game.id])
            try:
                response = api_client.post(url)
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert 'error' in response.data
                assert 'insufficient credits' in response.data['error'].lower()
            except chess.engine.EngineTerminatedError:
                pytest.skip("Stockfish engine not available")

    def test_analyze_batch_games_view(self, api_client, user, game):
        api_client.force_authenticate(user=user)
        url = reverse('batch_analyze_games')
        try:
            response = api_client.post(url, {'num_games': 1})
            assert response.status_code == status.HTTP_200_OK
            assert 'results' in response.data
            assert 'individual_games' in response.data['results']
            assert 'overall_stats' in response.data['results']
            
            # Check empty results structure
            overall_stats = response.data['results']['overall_stats']
            assert 'total_games' in overall_stats
            assert 'wins' in overall_stats
            assert 'losses' in overall_stats
            assert 'draws' in overall_stats
            assert 'average_accuracy' in overall_stats
            assert 'common_mistakes' in overall_stats
            assert 'improvement_areas' in overall_stats
            assert 'strengths' in overall_stats
            
            # Verify common_mistakes structure
            common_mistakes = overall_stats['common_mistakes']
            assert 'blunders' in common_mistakes
            assert 'mistakes' in common_mistakes
            assert 'inaccuracies' in common_mistakes
            assert 'time_pressure' in common_mistakes
        except chess.engine.EngineTerminatedError:
            pytest.skip("Stockfish engine not available")

    def test_game_analyzer_initialization(self, game_analyzer):
        assert game_analyzer is not None

    def test_game_analyzer_feedback_generation(self, game_analyzer, game):
        try:
            analysis_results = game_analyzer.analyze_games([game])
            feedback = game_analyzer.generate_feedback(analysis_results[game.id])
            
            assert isinstance(feedback, dict)
            assert 'opening' in feedback
            assert 'accuracy' in feedback['opening']
            assert 'mistakes' in feedback
            assert 'blunders' in feedback
            assert 'time_management' in feedback
            assert 'tactical_opportunities' in feedback
            assert isinstance(feedback['tactical_opportunities'], list)
        except chess.engine.EngineTerminatedError:
            pytest.skip("Stockfish engine not available")

    def test_game_analyzer_error_handling(self, game_analyzer):
        try:
            # Test with empty list
            with pytest.raises(ValueError, match="No games provided for analysis"):
                game_analyzer.analyze_games([])

            # Test with invalid PGN
            invalid_game = Game(
                player=User.objects.create_user(username=f'testuser_{uuid.uuid4().hex[:8]}'),
                game_url=f'https://chess.com/game/{uuid.uuid4().hex}',
                played_at=datetime.now(),
                opponent='opponent1',
                result='win',
                pgn='invalid pgn',
                is_white=True
            )
            with pytest.raises(ValueError, match="Invalid PGN data: No moves found"):
                game_analyzer.analyze_single_game(invalid_game)
        except chess.engine.EngineTerminatedError:
            pytest.skip("Stockfish engine not available") 