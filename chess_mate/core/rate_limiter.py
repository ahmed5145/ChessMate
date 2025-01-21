import redis
from typing import Optional, Dict, Any
from datetime import datetime
import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter implementation using Redis with fallback to Django cache."""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize rate limiter with Redis connection or fallback to Django cache."""
        self.use_redis = True
        try:
            url = redis_url or settings.REDIS_URL
            logger.info(f"Connecting to Redis at {url.split('@')[-1]}")  # Log only host:port, not credentials
            self.redis = redis.Redis.from_url(url, decode_responses=True)
            # Test connection
            self.redis.ping()
            logger.info("Successfully connected to Redis")
        except (redis.ConnectionError, redis.ResponseError) as e:
            logger.warning(f"Redis not available, falling back to Django cache: {str(e)}")
            self.use_redis = False
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {str(e)}")
            self.use_redis = False

    def _get_cache(self):
        """Get the appropriate cache backend."""
        if self.use_redis:
            try:
                self.redis.ping()
                return self.redis
            except Exception as e:
                logger.error(f"Redis connection lost, falling back to Django cache: {str(e)}")
                self.use_redis = False
        return cache

    def get_rate_limit_config(self, endpoint_type: str) -> Dict[str, int]:
        """Get rate limit configuration for endpoint type."""
        try:
            return settings.RATE_LIMIT.get(
                endpoint_type.upper(),
                settings.RATE_LIMIT['DEFAULT']
            )
        except (AttributeError, KeyError):
            logger.warning(f"Rate limit configuration not found for {endpoint_type}, using defaults")
            return {'MAX_REQUESTS': 100, 'TIME_WINDOW': 60}

    def is_rate_limited(self, key: str, endpoint_type: str = 'DEFAULT') -> bool:
        """Check if the request should be rate limited."""
        try:
            config = self.get_rate_limit_config(endpoint_type)
            max_requests = config['MAX_REQUESTS']
            time_window = config['TIME_WINDOW']

            current_time = datetime.utcnow().timestamp()
            window_key = f"{key}:{int(current_time / time_window)}"
            
            if self.use_redis:
                pipe = self.redis.pipeline()
                pipe.incr(window_key, 1)
                pipe.expire(window_key, time_window)
                current_requests = pipe.execute()[0]
            else:
                # Using Django's cache
                current_requests = cache.get(window_key, 0) + 1
                cache.set(window_key, current_requests, time_window)
            
            return current_requests > max_requests
        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}")
            return False  # Fail open

    def get_remaining_requests(self, key: str, endpoint_type: str = 'DEFAULT') -> int:
        """Get the number of remaining requests allowed."""
        try:
            config = self.get_rate_limit_config(endpoint_type)
            max_requests = config['MAX_REQUESTS']
            time_window = config['TIME_WINDOW']

            current_time = datetime.utcnow().timestamp()
            window_key = f"{key}:{int(current_time / time_window)}"
            
            if self.use_redis:
                current_requests = int(self.redis.get(window_key) or 0)
            else:
                current_requests = cache.get(window_key, 0)
            
            return max(0, max_requests - current_requests)
        except Exception as e:
            logger.error(f"Error getting remaining requests: {str(e)}")
            return 0

    def get_reset_time(self, key: str) -> int:
        """Get the time in seconds until the rate limit resets."""
        try:
            window_key = f"{key}:window"
            counter_key = f"{key}:counter"
            
            if self.use_redis:
                # Get TTL of both keys and return the higher value
                window_ttl = int(self.redis.ttl(window_key) or 0)
                counter_ttl = int(self.redis.ttl(counter_key) or 0)
                ttl = max(window_ttl, counter_ttl)
            else:
                # Django cache doesn't provide TTL, estimate based on key pattern
                current_time = datetime.utcnow().timestamp()
                time_window = 60  # Default window
                next_window = (int(current_time / time_window) + 1) * time_window
                ttl = int(next_window - current_time)
            
            return max(0, ttl)
        except Exception as e:
            logger.error(f"Error getting reset time: {str(e)}")
            return 0 