import os
import sys
import django
from django.conf import settings
import pytest
from unittest.mock import MagicMock, patch
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chess_mate.settings')
os.environ['TESTING'] = 'True'
django.setup()

# Configure test settings
def pytest_configure():
    settings.DEBUG = False
    settings.TESTING = True
    settings.DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:'
        }
    }
    
    # Set required environment variables for testing
    os.environ.setdefault('OPENAI_API_KEY', 'test-key')
    os.environ.setdefault('STRIPE_SECRET_KEY', 'test-stripe-secret-key')
    os.environ.setdefault('STRIPE_PUBLIC_KEY', 'test-stripe-public-key')
    os.environ.setdefault('STOCKFISH_PATH', '/mock/path/to/stockfish')
    os.environ.setdefault('SECRET_KEY', 'test-django-secret-key')
    os.environ.setdefault('DEBUG', 'True')

# Create a mock OpenAI response
@pytest.fixture
def mock_openai_response():
    message = ChatCompletionMessage(
        content="Test feedback content",
        role="assistant",
        function_call=None,
        tool_calls=None
    )
    choice = Choice(
        finish_reason="stop",
        index=0,
        message=message,
        logprobs=None
    )
    return ChatCompletion(
        id="test_id",
        choices=[choice],
        created=1234567890,
        model="gpt-3.5-turbo",
        object="chat.completion",
        system_fingerprint=None,
        usage=None
    )

# Mock the OpenAI client
@pytest.fixture(autouse=True)
def mock_openai(mock_openai_response):
    with patch("openai.OpenAI") as mock_client:
        # Create a mock instance
        mock_instance = MagicMock()
        
        # Mock the chat.completions.create method
        mock_instance.chat.completions.create.return_value = mock_openai_response
        
        # Make the mock client return our mock instance
        mock_client.return_value = mock_instance
        
        yield mock_client 