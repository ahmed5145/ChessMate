import os
import sys
import django
from django.conf import settings

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