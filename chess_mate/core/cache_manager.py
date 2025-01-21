import zlib
import json
from typing import Dict, Any, Optional, List, Union
from django.core.cache import cache
import redis
from django.conf import settings
import logging
import hashlib

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        """Initialize cache manager with Redis connection if available."""
        self.use_redis = bool(settings.REDIS_URL)
        if self.use_redis:
            try:
                self.redis = redis.from_url(settings.REDIS_URL)
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                self.use_redis = False
        self.default_ttl = 3600  # 1 hour default TTL

    def _compress_data(self, data: Any) -> bytes:
        """Compress data using zlib."""
        return zlib.compress(json.dumps(data).encode())

    def _decompress_data(self, data: bytes) -> Any:
        """Decompress data using zlib."""
        return json.loads(zlib.decompress(data).decode())

    def _generate_key(self, prefix: str, identifier: str) -> str:
        """Generate a cache key."""
        return f"chessmate:{prefix}:{identifier}"

    def _hash_position(self, fen: str) -> str:
        """Generate a hash for a chess position."""
        return hashlib.md5(fen.encode()).hexdigest()

    def cache_analysis(self, game_id: int, analysis_data: Dict[str, Any], ttl: Optional[int] = 3600) -> bool:
        """Cache game analysis results with 1 hour TTL."""
        try:
            key = self._generate_key('analysis', str(game_id))
            compressed_data = self._compress_data(analysis_data)
            
            if self.use_redis:
                return bool(self.redis.setex(key, ttl or self.default_ttl, compressed_data))
            else:
                cache.set(key, compressed_data, timeout=ttl)
                return True
        except Exception as e:
            logger.error(f"Error caching analysis: {str(e)}")
            return False

    def get_cached_analysis(self, game_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve cached analysis results."""
        try:
            key = self._generate_key('analysis', str(game_id))
            
            if self.use_redis:
                data = self.redis.get(key)
            else:
                data = cache.get(key)
                
            if data:
                return self._decompress_data(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached analysis: {str(e)}")
            return None

    def cache_position_evaluation(self, fen: str, evaluation: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache evaluation for a specific position."""
        try:
            key = self._generate_key('position', self._hash_position(fen))
            compressed_data = self._compress_data(evaluation)
            
            if self.use_redis:
                return bool(self.redis.setex(key, ttl or self.default_ttl, compressed_data))
            else:
                cache.set(key, compressed_data, timeout=ttl or self.default_ttl)
                return True
        except Exception as e:
            logger.error(f"Error caching position evaluation: {str(e)}")
            return False

    def get_cached_position_evaluation(self, fen: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached position evaluation."""
        try:
            key = self._generate_key('position', self._hash_position(fen))
            
            if self.use_redis:
                data = self.redis.get(key)
            else:
                data = cache.get(key)
                
            if data:
                return self._decompress_data(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached position: {str(e)}")
            return None

    def cache_user_games(self, user_id: int, games: List[Dict[str, Any]], ttl: Optional[int] = 1800) -> bool:
        """Cache user's games list with 30 minutes TTL."""
        try:
            key = self._generate_key('games', str(user_id))
            compressed_data = self._compress_data(games)
            
            if self.use_redis:
                return bool(self.redis.setex(key, ttl or self.default_ttl, compressed_data))
            else:
                cache.set(key, compressed_data, timeout=ttl)
                return True
        except Exception as e:
            logger.error(f"Error caching user games: {str(e)}")
            return False

    def get_cached_user_games(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached user games."""
        try:
            key = self._generate_key('games', str(user_id))
            
            if self.use_redis:
                data = self.redis.get(key)
            else:
                data = cache.get(key)
                
            if data:
                return self._decompress_data(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached user games: {str(e)}")
            return None

    def invalidate_analysis_cache(self, game_id: int) -> bool:
        """Invalidate cached analysis for a game."""
        try:
            key = self._generate_key('analysis', str(game_id))
            if self.use_redis:
                return bool(self.redis.delete(key))
            else:
                cache.delete(key)
                return True
        except Exception as e:
            logger.error(f"Error invalidating analysis cache: {str(e)}")
            return False

    def invalidate_user_games_cache(self, user_id: int) -> bool:
        """Invalidate cached games for a user."""
        try:
            key = self._generate_key('games', str(user_id))
            if self.use_redis:
                return bool(self.redis.delete(key))
            else:
                cache.delete(key)
                return True
        except Exception as e:
            logger.error(f"Error invalidating games cache: {str(e)}")
            return False

    def clear_all_caches(self) -> bool:
        """Clear all caches."""
        try:
            if self.use_redis:
                self.redis.flushdb()
            else:
                cache.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing caches: {str(e)}")
            return False

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        try:
            if not self.use_redis:
                return {
                    "analysis_count": 0,
                    "position_count": 0,
                    "games_count": 0,
                    "total_keys": 0
                }
                
            analysis_keys = len(self.redis.keys("chessmate:analysis:*"))
            position_keys = len(self.redis.keys("chessmate:position:*"))
            games_keys = len(self.redis.keys("chessmate:games:*"))
            
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