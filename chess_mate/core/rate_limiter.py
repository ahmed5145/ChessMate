import redis
from typing import Optional
from datetime import datetime, timedelta
import os

class RateLimiter:
    """Rate limiter implementation using Redis."""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize rate limiter with Redis connection."""
        self.redis = redis.Redis.from_url(
            redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            decode_responses=True
        )

    def is_rate_limited(self, key: str, max_requests: int, time_window: int) -> bool:
        """
        Check if the request should be rate limited.
        
        Args:
            key: Unique identifier for the rate limit (e.g., "user_id:endpoint")
            max_requests: Maximum number of requests allowed in the time window
            time_window: Time window in seconds
            
        Returns:
            bool: True if rate limited, False otherwise
        """
        current_time = datetime.utcnow().timestamp()
        window_key = f"{key}:{int(current_time / time_window)}"
        
        # Use pipeline to ensure atomic operations
        pipe = self.redis.pipeline()
        pipe.incr(window_key, 1)
        pipe.expire(window_key, time_window)
        current_requests = pipe.execute()[0]
        
        return current_requests > max_requests

    def get_remaining_requests(self, key: str, max_requests: int, time_window: int) -> int:
        """Get the number of remaining requests allowed."""
        current_time = datetime.utcnow().timestamp()
        window_key = f"{key}:{int(current_time / time_window)}"
        
        current_requests = int(self.redis.get(window_key) or 0)
        return max(0, max_requests - current_requests)

    def get_reset_time(self, key: str) -> int:
        """Get the time in seconds until the rate limit resets."""
        ttl = self.redis.ttl(key)
        return max(0, ttl) 