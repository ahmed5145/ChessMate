from functools import wraps
from typing import Callable, Any, Optional
from django.http import JsonResponse
from django.core.exceptions import ImproperlyConfigured
from .rate_limiter import RateLimiter
import logging

logger = logging.getLogger(__name__)

try:
    rate_limiter = RateLimiter()
except ImproperlyConfigured as e:
    logger.error(f"Failed to initialize rate limiter: {str(e)}")
    rate_limiter = None

def rate_limit(endpoint_type: str = 'DEFAULT') -> Callable:
    """
    Rate limiting decorator for views.
    
    Args:
        endpoint_type: Type of endpoint to get rate limit config for (e.g., 'AUTH', 'ANALYSIS')
        
    Returns:
        Decorated view function
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request: Any, *args: Any, **kwargs: Any) -> Any:
            if not rate_limiter:
                logger.warning("Rate limiter not initialized, skipping rate limit check")
                return view_func(request, *args, **kwargs)

            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            
            # Create a unique key for this user and endpoint
            rate_limit_key = f"rate_limit:{request.user.id}:{request.path}"
            
            # Check if rate limited
            try:
                if rate_limiter.is_rate_limited(rate_limit_key, endpoint_type):
                    remaining_time = rate_limiter.get_reset_time(rate_limit_key)
                    logger.warning(f"Rate limit exceeded for user {request.user.id} on endpoint {request.path}")
                    return JsonResponse({
                        'error': 'Rate limit exceeded',
                        'message': f'Please try again in {remaining_time} seconds',
                        'reset_time': remaining_time
                    }, status=429)
            except Exception as e:
                logger.error(f"Error checking rate limit: {str(e)}")
                # Continue with the request on rate limit errors
                return view_func(request, *args, **kwargs)
            
            try:
                # Get the response from the view
                response = view_func(request, *args, **kwargs)
                
                # Add rate limit headers to response
                remaining = rate_limiter.get_remaining_requests(rate_limit_key, endpoint_type)
                reset_time = rate_limiter.get_reset_time(rate_limit_key)
                
                config = rate_limiter.get_rate_limit_config(endpoint_type)
                response['X-RateLimit-Limit'] = str(config['MAX_REQUESTS'])
                response['X-RateLimit-Remaining'] = str(remaining)
                response['X-RateLimit-Reset'] = str(reset_time)
                
                return response
            except Exception as e:
                logger.error(f"Error in rate limited view: {str(e)}")
                return view_func(request, *args, **kwargs)
                
        return _wrapped_view
    return decorator 