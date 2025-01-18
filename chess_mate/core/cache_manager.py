import redis
import json
from typing import Dict, Any, Optional, List
import logging
from django.conf import settings
import hashlib

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True
        )
        self.default_ttl = 3600  # 1 hour default TTL

    def _generate_key(self, prefix: str, identifier: str) -> str:
        """Generate a unique cache key."""
        return f"chessmate:{prefix}:{identifier}"

    def _hash_position(self, fen: str) -> str:
        """Generate a hash for a chess position."""
        return hashlib.md5(fen.encode()).hexdigest()

    def cache_analysis(self, game_id: int, analysis_data: Dict[str, Any], ttl: int = None) -> bool:
        """Cache game analysis results."""
        try:
            key = self._generate_key('analysis', str(game_id))
            return self.redis_client.setex(
                key,
                ttl or self.default_ttl,
                json.dumps(analysis_data)
            )
        except Exception as e:
            logger.error(f"Error caching analysis: {str(e)}")
            return False

    def get_cached_analysis(self, game_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve cached game analysis."""
        try:
            key = self._generate_key('analysis', str(game_id))
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error retrieving cached analysis: {str(e)}")
            return None

    def cache_position_evaluation(self, fen: str, evaluation: Dict[str, Any], ttl: int = None) -> bool:
        """Cache evaluation for a specific position."""
        try:
            key = self._generate_key('position', self._hash_position(fen))
            return self.redis_client.setex(
                key,
                ttl or self.default_ttl,
                json.dumps(evaluation)
            )
        except Exception as e:
            logger.error(f"Error caching position evaluation: {str(e)}")
            return False

    def get_cached_position_evaluation(self, fen: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached position evaluation."""
        try:
            key = self._generate_key('position', self._hash_position(fen))
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error retrieving cached position: {str(e)}")
            return None

    def cache_user_games(self, user_id: int, games: List[Dict[str, Any]], ttl: int = None) -> bool:
        """Cache user's games list."""
        try:
            key = self._generate_key('games', str(user_id))
            return self.redis_client.setex(
                key,
                ttl or self.default_ttl,
                json.dumps(games)
            )
        except Exception as e:
            logger.error(f"Error caching user games: {str(e)}")
            return False

    def get_cached_user_games(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached user games."""
        try:
            key = self._generate_key('games', str(user_id))
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error retrieving cached games: {str(e)}")
            return None

    def invalidate_analysis_cache(self, game_id: int) -> bool:
        """Invalidate cached analysis for a game."""
        try:
            key = self._generate_key('analysis', str(game_id))
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Error invalidating analysis cache: {str(e)}")
            return False

    def invalidate_user_games_cache(self, user_id: int) -> bool:
        """Invalidate cached games for a user."""
        try:
            key = self._generate_key('games', str(user_id))
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Error invalidating games cache: {str(e)}")
            return False

    def clear_all_caches(self) -> bool:
        """Clear all ChessMate related caches."""
        try:
            keys = self.redis_client.keys("chessmate:*")
            if keys:
                return bool(self.redis_client.delete(*keys))
            return True
        except Exception as e:
            logger.error(f"Error clearing all caches: {str(e)}")
            return False

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        try:
            analysis_keys = len(self.redis_client.keys("chessmate:analysis:*"))
            position_keys = len(self.redis_client.keys("chessmate:position:*"))
            games_keys = len(self.redis_client.keys("chessmate:games:*"))
            
            return {
                "analysis_count": analysis_keys,
                "position_count": position_keys,
                "games_count": games_keys,
                "total_keys": analysis_keys + position_keys + games_keys
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {
                "analysis_count": 0,
                "position_count": 0,
                "games_count": 0,
                "total_keys": 0
            } 