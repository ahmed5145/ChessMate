import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from unittest.mock import patch, MagicMock
from core.rate_limiter import RateLimiter
from core.models import Profile  # type: ignore
from django.db import models
from typing import Type, cast
import redis
import time

UserModel = get_user_model()

class TestRateLimiter(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create test user once for all tests
        cls.user = UserModel.objects.create_user(  # type: ignore
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def setUp(self):
        self.client = Client()
        self.rate_limiter = RateLimiter()
        # Use objects manager directly from model class
        Profile.objects.filter(user=self.user).delete()  # type: ignore
        self.profile = Profile.objects.create(user=self.user)  # type: ignore

    def tearDown(self):
        # Clean up after each test
        if hasattr(self, 'rate_limiter') and hasattr(self.rate_limiter, 'redis'):
            self.rate_limiter.redis.flushdb()

    def test_rate_limiter_initialization(self):
        """Test that rate limiter initializes correctly."""
        self.assertIsNotNone(self.rate_limiter.redis)
        self.assertTrue(self.rate_limiter.redis.ping())

    def test_rate_limit_config(self):
        """Test that rate limit config is retrieved correctly."""
        auth_config = self.rate_limiter.get_rate_limit_config('AUTH')
        self.assertEqual(auth_config['MAX_REQUESTS'], settings.RATE_LIMIT['AUTH']['MAX_REQUESTS'])
        self.assertEqual(auth_config['TIME_WINDOW'], settings.RATE_LIMIT['AUTH']['TIME_WINDOW'])

    def test_rate_limit_exceeded(self):
        """Test that rate limiting works when limit is exceeded."""
        key = 'test:rate:limit'
        endpoint_type = 'AUTH'
        config = self.rate_limiter.get_rate_limit_config(endpoint_type)
        
        # Make requests up to the limit
        for _ in range(config['MAX_REQUESTS']):
            self.assertFalse(self.rate_limiter.is_rate_limited(key, endpoint_type))
        
        # Next request should be rate limited
        self.assertTrue(self.rate_limiter.is_rate_limited(key, endpoint_type))

    def test_remaining_requests(self):
        """Test that remaining requests are calculated correctly."""
        key = 'test:remaining:requests'
        endpoint_type = 'AUTH'
        config = self.rate_limiter.get_rate_limit_config(endpoint_type)
        
        # Initial remaining should be max requests
        self.assertEqual(
            self.rate_limiter.get_remaining_requests(key, endpoint_type),
            config['MAX_REQUESTS']
        )
        
        # Make some requests
        for i in range(3):
            self.rate_limiter.is_rate_limited(key, endpoint_type)
            self.assertEqual(
                self.rate_limiter.get_remaining_requests(key, endpoint_type),
                config['MAX_REQUESTS'] - (i + 1)
            )

    def test_reset_time(self):
        """Test that reset time is calculated correctly."""
        key = 'test:reset:time'
        endpoint_type = 'AUTH'
        window = settings.RATE_LIMIT[endpoint_type]['TIME_WINDOW']
        
        # Set initial window time to 30 seconds ago
        current_time = int(time.time())
        past_time = current_time - 30  # Set window start to 30 seconds ago
        window_key = f"{key}:window"
        counter_key = f"{key}:counter"
        
        # Clear any existing keys
        self.rate_limiter.redis.delete(window_key)
        self.rate_limiter.redis.delete(counter_key)
        
        # Set window expiry and counter
        self.rate_limiter.redis.setex(window_key, window, str(past_time))
        self.rate_limiter.redis.setex(counter_key, window, "1")
        
        # Get reset time
        reset_time = self.rate_limiter.get_reset_time(key)
        
        # The reset time should be the remaining time in the window
        # which should be between window - 30 and window seconds
        self.assertGreater(reset_time, 0)
        self.assertLessEqual(reset_time, window)
        self.assertGreater(reset_time, window - 35)  # Allow 5 seconds tolerance

    @patch('redis.Redis')
    def test_rate_limiter_redis_error(self, mock_redis):
        """Test that rate limiter handles Redis errors gracefully."""
        mock_redis.return_value.incr.side_effect = redis.RedisError("Test error")
        
        # Rate limiter should fail open (allow requests) on Redis errors
        self.assertFalse(
            self.rate_limiter.is_rate_limited('test:error', 'AUTH')
        )

class TestRateLimitDecorator(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create test user once for all tests
        cls.user = UserModel.objects.create_user(  # type: ignore
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def setUp(self):
        self.client = Client()
        self.rate_limiter = RateLimiter()
        # Use objects manager directly from model class
        Profile.objects.filter(user=self.user).delete()  # type: ignore
        self.profile = Profile.objects.create(user=self.user)  # type: ignore
        # Login the user
        self.client.login(username='testuser', password='testpass123')

    def tearDown(self):
        # Clean up Redis after each test
        if hasattr(self.rate_limiter, 'redis'):
            self.rate_limiter.redis.flushdb()

    def test_login_rate_limit(self):
        """Test rate limiting on login endpoint."""
        url = reverse('login')
        data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }

        # Make requests up to the limit
        for _ in range(settings.RATE_LIMIT['AUTH']['MAX_REQUESTS']):
            response = self.client.post(url, data, content_type='application/json')
            self.assertNotEqual(response.status_code, 429)

        # Next request should be rate limited
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 429)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('reset_time', response_data)

    def test_rate_limit_headers(self):
        """Test that rate limit headers are included in responses."""
        url = reverse('login')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, content_type='application/json')

        # Headers should be present regardless of authentication success
        self.assertIn('X-RateLimit-Limit', response.headers)
        self.assertIn('X-RateLimit-Remaining', response.headers)
        self.assertIn('X-RateLimit-Reset', response.headers)

        # Verify header values are correct
        config = settings.RATE_LIMIT['AUTH']
        self.assertEqual(response.headers['X-RateLimit-Limit'], str(config['MAX_REQUESTS']))
        remaining = int(response.headers['X-RateLimit-Remaining'])
        self.assertGreaterEqual(remaining, 0)
        self.assertLessEqual(remaining, config['MAX_REQUESTS'])

    def test_unauthenticated_requests_not_rate_limited(self):
        """Test that unauthenticated requests are not rate limited."""
        self.client.logout()
        url = reverse('register')
        
        # Make many requests
        for _ in range(settings.RATE_LIMIT['AUTH']['MAX_REQUESTS'] + 1):
            response = self.client.post(url, {
                'username': f'user{_}',
                'email': f'user{_}@example.com',
                'password': 'testpass123'
            })
            self.assertNotEqual(response.status_code, 429) 