from functools import wraps
from typing import Callable, Any
from django.http import JsonResponse
from .rate_limiter import RateLimiter

rate_limiter = RateLimiter()

def rate_limit(max_requests: int, time_window: int) -> Callable:
    """
    Rate limiting decorator for views.
    
    Args:
        max_requests: Maximum number of requests allowed in the time window
        time_window: Time window in seconds
        
    Returns:
        Decorated view function
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request: Any, *args: Any, **kwargs: Any) -> Any:
            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            
            # Create a unique key for this user and endpoint
            rate_limit_key = f"rate_limit:{request.user.id}:{request.path}"
            
            # Check if rate limited
            if rate_limiter.is_rate_limited(rate_limit_key, max_requests, time_window):
                remaining_time = rate_limiter.get_reset_time(rate_limit_key)
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'message': f'Please try again in {remaining_time} seconds',
                    'reset_time': remaining_time
                }, status=429)
            
            # Add rate limit headers to response
            response = view_func(request, *args, **kwargs)
            remaining = rate_limiter.get_remaining_requests(rate_limit_key, max_requests, time_window)
            reset_time = rate_limiter.get_reset_time(rate_limit_key)
            
            response['X-RateLimit-Limit'] = str(max_requests)
            response['X-RateLimit-Remaining'] = str(remaining)
            response['X-RateLimit-Reset'] = str(reset_time)
            
            return response
        return _wrapped_view
    return decorator 