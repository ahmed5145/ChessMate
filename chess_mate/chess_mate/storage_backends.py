"""Custom storage backends for ChessMate."""
from storages.backends.s3boto3 import S3Boto3Storage

class MediaStorage(S3Boto3Storage):
    """Custom storage class for media files."""
    location = 'media'
    file_overwrite = False
    default_acl = 'private'
    custom_domain = False  # Use S3 domain for media files
    
    def get_accessed_time(self, name):
        """Get the last accessed time of the file."""
        return None
    
    def get_created_time(self, name):
        """Get the creation time of the file."""
        return None
    
    def get_modified_time(self, name):
        """Get the last modified time of the file."""
        return None 