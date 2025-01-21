"""AWS configuration for ChessMate."""
import os
import boto3
from botocore.config import Config

# AWS Credentials
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_BACKUP_BUCKET')
AWS_S3_REGION_NAME = os.getenv('AWS_REGION', 'us-east-2')

# S3 Configuration
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',  # 24 hours
}

# Static and Media Files
AWS_LOCATION = 'static'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
DEFAULT_FILE_STORAGE = 'chess_mate.storage_backends.MediaStorage'

# Security
AWS_DEFAULT_ACL = 'private'
AWS_S3_ENCRYPTION = True
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = True

# Performance
AWS_S3_TRANSFER_CONFIG = {
    'max_concurrency': 10,
    'use_threads': True
}

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_S3_REGION_NAME,
    config=Config(
        retries={'max_attempts': 3},
        connect_timeout=5,
        read_timeout=10
    )
) 