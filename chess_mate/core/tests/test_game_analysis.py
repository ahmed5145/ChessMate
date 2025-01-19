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
from unittest.mock import MagicMock, patch
import os

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
    return Game.objects.create(
        user=user,
        platform='chess.com',
        game_id=uuid.uuid4().hex,
        white='testuser',
        black='opponent1',
        result='1-0',
        pgn='1. e4 e5 2. Nf3 Nc6 3. Bb5',
        date_played=datetime.now(),
        opening_name='Ruy Lopez',
        opponent='opponent1'
    )

@pytest.fixture
def mock_stockfish_engine():
    """Mock the Stockfish engine for testing."""
    mock_engine = MagicMock()
    mock_engine.analyse.return_value = {
        "score": chess.engine.PovScore(chess.engine.Cp(50), chess.WHITE),
        "depth": 20,
        "time": 0.1,
        "nodes": 1000,
        "nps": 10000,
        "multipv": 1
    }
    return mock_engine

@pytest.fixture(scope='function')
def game_analyzer(mock_stockfish_engine):
    """Create a GameAnalyzer with a mock Stockfish engine."""
    with patch('chess.engine.SimpleEngine.popen_uci', return_value=mock_stockfish_engine):
        analyzer = GameAnalyzer(stockfish_path="/mock/path/to/stockfish")
        yield analyzer
        try:
            analyzer.engine.quit()
        except:
            pass

@pytest.fixture
def mock_analysis_results():
    """Create mock analysis results for testing."""
    return [{
        "move": "e4",
        "score": 50,
        "depth": 20,
        "time_spent": 0.1,
        "is_mate": False,
        "is_capture": False,
        "move_number": 1,
        "evaluation_drop": 0,
        "is_mistake": False,
        "is_blunder": False,
        "is_critical": True
    }]

@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI response."""
    return {
        "choices": [{
            "message": {
                "content": "Test feedback content"
            }
        }]
    }

@pytest.fixture
def mock_openai_client(mock_openai_response):
    """Create a mock OpenAI client."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_openai_response
    return mock_client

@pytest.fixture(autouse=True)
def mock_openai(mock_openai_client):
    """Mock the OpenAI client initialization."""
    with patch('core.ai_feedback.OpenAI', return_value=mock_openai_client):
        yield mock_openai_client

@pytest.mark.django_db(transaction=True)
class TestGameAnalysis:
    def test_analyze_game_view_unauthorized(self, api_client, game):
        url = reverse('analyze_game', args=[game.id])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.skip(reason="OpenAI mock integration needs to be fixed")
    def test_analyze_game_view_authorized(self, api_client, user, game, mock_openai_client, mock_stockfish_engine, mock_analysis_results):
        api_client.force_authenticate(user=user)
        url = reverse('analyze_game', args=[game.id])
        
        mock_feedback = {
            "mistakes": 1,
            "blunders": 0,
            "inaccuracies": 2,
            "time_management": {
                "avg_time_per_move": 15,
                "critical_moments": [],
                "time_pressure_moves": [],
                "suggestion": "Good time management"
            },
            "opening": {
                "played_moves": ["e4", "e5", "Nf3"],
                "accuracy": 85.5,
                "suggestion": "Good opening play"
            },
            "tactical_opportunities": ["Missed fork on move 15"],
            "endgame": {
                "evaluation": "Equal position",
                "accuracy": 80.0,
                "suggestion": "Practice rook endgames"
            },
            "positional_play": {
                "piece_activity": 75,
                "pawn_structure": 80,
                "king_safety": 90,
                "suggestion": "Good piece coordination"
            },
            "ai_suggestions": {
                "strengths": ["Tactical awareness", "Time management"],
                "areas_for_improvement": ["Opening preparation", "Endgame technique"]
            }
        }
        
        with patch('chess.engine.SimpleEngine.popen_uci', return_value=mock_stockfish_engine), \
             patch('core.game_analyzer.GameAnalyzer.analyze_single_game', return_value=mock_analysis_results), \
             patch('core.ai_feedback.AIFeedbackGenerator.generate_personalized_feedback', return_value=mock_feedback):
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK
            
            # Check response structure
            assert isinstance(response.data, dict)
            assert 'analysis' in response.data
            assert 'feedback' in response.data
            
            # Check feedback structure
            feedback = response.data['feedback']
            assert 'opening' in feedback
            assert 'accuracy' in feedback['opening']
            assert 'mistakes' in feedback
            assert 'blunders' in feedback
            assert 'time_management' in feedback
            assert 'tactical_opportunities' in feedback
            assert 'endgame' in feedback
            assert 'positional_play' in feedback
            assert 'ai_suggestions' in feedback

    def test_analyze_game_view_not_found(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('analyze_game', args=[999])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_analyze_game_view_insufficient_credits(self, api_client, user, game, mock_stockfish_engine):
        with transaction.atomic():
            profile = Profile.objects.get(user=user)
            profile.credits = 0
            profile.save()

            api_client.force_authenticate(user=user)
            url = reverse('analyze_game', args=[game.id])
            
            with patch('chess.engine.SimpleEngine.popen_uci', return_value=mock_stockfish_engine):
                response = api_client.post(url)
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert 'error' in response.data
                assert 'insufficient credits' in response.data['error'].lower()

    @pytest.mark.skip(reason="OpenAI mock integration needs to be fixed")
    def test_analyze_batch_games_view(self, api_client, user, game, mock_openai_client, mock_stockfish_engine, mock_analysis_results):
        api_client.force_authenticate(user=user)
        url = reverse('batch_analyze_games')
        
        mock_feedback = {
            "mistakes": 1,
            "blunders": 0,
            "inaccuracies": 2,
            "time_management": {
                "avg_time_per_move": 15,
                "critical_moments": [],
                "time_pressure_moves": [],
                "suggestion": "Good time management"
            },
            "opening": {
                "played_moves": ["e4", "e5", "Nf3"],
                "accuracy": 85.5,
                "suggestion": "Good opening play"
            },
            "tactical_opportunities": ["Missed fork on move 15"],
            "endgame": {
                "evaluation": "Equal position",
                "accuracy": 80.0,
                "suggestion": "Practice rook endgames"
            },
            "positional_play": {
                "piece_activity": 75,
                "pawn_structure": 80,
                "king_safety": 90,
                "suggestion": "Good piece coordination"
            }
        }
        
        with patch('chess.engine.SimpleEngine.popen_uci', return_value=mock_stockfish_engine), \
             patch('core.game_analyzer.GameAnalyzer.analyze_single_game', return_value=mock_analysis_results), \
             patch('core.ai_feedback.AIFeedbackGenerator.generate_personalized_feedback', return_value=mock_feedback):
            response = api_client.post(url, {'num_games': 1})
            assert response.status_code == status.HTTP_200_OK
            
            # Check response structure
            assert isinstance(response.data, dict)
            assert 'message' in response.data
            assert 'results' in response.data
            
            # Check results structure
            results = response.data['results']
            assert 'individual_games' in results
            assert isinstance(results['individual_games'], dict)
            
            assert 'overall_stats' in results
            overall_stats = results['overall_stats']
            assert 'total_games' in overall_stats
            assert 'wins' in overall_stats
            assert 'losses' in overall_stats
            assert 'draws' in overall_stats
            assert 'average_accuracy' in overall_stats
            assert 'common_mistakes' in overall_stats
            assert 'improvement_areas' in overall_stats
            assert 'strengths' in overall_stats
            
            # Check dynamic feedback
            assert 'dynamic_feedback' in results
            
            # Verify OpenAI was called
            assert mock_openai_client.chat.completions.create.called
            
            # Verify the feedback contains the mock response
            assert "Test feedback content" in str(response.data)

    def test_game_analyzer_initialization(self, game_analyzer):
        assert game_analyzer is not None
        assert game_analyzer.engine is not None

    def test_game_analyzer_feedback_generation(self, game_analyzer, game, mock_analysis_results):
        analysis_results = {game.id: mock_analysis_results}
        feedback = game_analyzer.generate_feedback(analysis_results[game.id])
        
        assert isinstance(feedback, dict)
        assert 'opening' in feedback
        assert 'accuracy' in feedback['opening']
        assert 'mistakes' in feedback
        assert 'blunders' in feedback
        assert 'time_management' in feedback
        assert 'tactical_opportunities' in feedback
        assert isinstance(feedback['tactical_opportunities'], list)

    def test_game_analyzer_error_handling(self, game_analyzer):
        # Test with empty list
        with pytest.raises(ValueError, match="No games provided for analysis"):
            game_analyzer.analyze_games([])

        # Test with invalid PGN
        test_user = User.objects.create_user(username=f'testuser_{uuid.uuid4().hex[:8]}')
        invalid_game = Game.objects.create(
            user=test_user,
            platform='chess.com',
            game_id=uuid.uuid4().hex,
            white='testuser',
            black='opponent1',
            result='unknown',
            pgn='invalid pgn',
            date_played=datetime.now(),
            opening_name='Unknown Opening',
            opponent='opponent1'
        )
        with pytest.raises(ValueError, match="Invalid PGN data: No moves found"):
            game_analyzer.analyze_single_game(invalid_game) 