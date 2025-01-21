import pytest
from django.test import TestCase
from unittest.mock import patch, MagicMock
from core.cache_manager import CacheManager
import zlib
import json

class TestCacheManager(TestCase):
    def setUp(self):
        self.cache_manager = CacheManager()
        self.test_data = {
            'analysis': {'moves': [1, 2, 3], 'score': 0.5},
            'games': [{'id': 1, 'result': 'win'}, {'id': 2, 'result': 'loss'}]
        }

    def test_compression(self):
        """Test data compression and decompression."""
        compressed = self.cache_manager._compress_data(self.test_data['analysis'])
        decompressed = self.cache_manager._decompress_data(compressed)
        self.assertEqual(decompressed, self.test_data['analysis'])

    @patch('redis.Redis')
    def test_cache_analysis_redis(self, mock_redis):
        """Test caching analysis data with Redis."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        self.cache_manager.use_redis = True
        self.cache_manager.redis = mock_redis_instance

        # Test successful caching
        game_id = 1
        self.cache_manager.cache_analysis(game_id, self.test_data['analysis'])
        
        mock_redis_instance.setex.assert_called_once()
        key = f"chessmate:analysis:{game_id}"
        compressed_data = self.cache_manager._compress_data(self.test_data['analysis'])
        mock_redis_instance.setex.assert_called_with(key, 3600, compressed_data)

    def test_cache_analysis_django_cache(self):
        """Test caching analysis data with Django's cache."""
        self.cache_manager.use_redis = False
        game_id = 1
        
        # Test caching
        success = self.cache_manager.cache_analysis(game_id, self.test_data['analysis'])
        self.assertTrue(success)
        
        # Test retrieval
        cached_data = self.cache_manager.get_cached_analysis(game_id)
        self.assertEqual(cached_data, self.test_data['analysis'])

    @patch('redis.Redis')
    def test_cache_user_games_redis(self, mock_redis):
        """Test caching user games with Redis."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        self.cache_manager.use_redis = True
        self.cache_manager.redis = mock_redis_instance

        user_id = 1
        self.cache_manager.cache_user_games(user_id, self.test_data['games'])
        
        mock_redis_instance.setex.assert_called_once()
        key = f"chessmate:games:{user_id}"
        compressed_data = self.cache_manager._compress_data(self.test_data['games'])
        mock_redis_instance.setex.assert_called_with(key, 1800, compressed_data)

    def test_cache_user_games_django_cache(self):
        """Test caching user games with Django's cache."""
        self.cache_manager.use_redis = False
        user_id = 1
        
        # Test caching
        success = self.cache_manager.cache_user_games(user_id, self.test_data['games'])
        self.assertTrue(success)
        
        # Test retrieval
        cached_data = self.cache_manager.get_cached_user_games(user_id)
        self.assertEqual(cached_data, self.test_data['games'])

    @patch('redis.Redis')
    def test_clear_all_caches_redis(self, mock_redis):
        """Test clearing all caches with Redis."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        self.cache_manager.use_redis = True
        self.cache_manager.redis = mock_redis_instance

        success = self.cache_manager.clear_all_caches()
        self.assertTrue(success)
        mock_redis_instance.flushdb.assert_called_once()

    def test_clear_all_caches_django_cache(self):
        """Test clearing all caches with Django's cache."""
        self.cache_manager.use_redis = False
        success = self.cache_manager.clear_all_caches()
        self.assertTrue(success)

    def test_error_handling(self):
        """Test error handling in cache operations."""
        self.cache_manager.use_redis = True
        self.cache_manager.redis = None  # Simulate Redis connection failure
        
        # Test cache operations with failed Redis
        self.assertFalse(self.cache_manager.cache_analysis(1, {}))
        self.assertIsNone(self.cache_manager.get_cached_analysis(1))
        self.assertFalse(self.cache_manager.cache_user_games(1, []))
        self.assertIsNone(self.cache_manager.get_cached_user_games(1)) 