#!/usr/bin/env python
import os
import sys
import time
import subprocess
from datetime import datetime
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Configuration
DB_NAME = os.getenv('DB_NAME', 'chessmate')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

# Backup Configuration
BACKUP_DIR = Path(__file__).resolve().parent.parent.parent / 'backups'
BACKUP_RETENTION_DAYS = 30

def create_backup():
    """Create a PostgreSQL database backup."""
    # Create backup directory if it doesn't exist
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = BACKUP_DIR / f'backup_{DB_NAME}_{timestamp}.sql'
    
    try:
        # Set PostgreSQL password environment variable
        os.environ['PGPASSWORD'] = DB_PASSWORD
        
        # Create backup command
        command = [
            'pg_dump',
            '-h', DB_HOST,
            '-p', DB_PORT,
            '-U', DB_USER,
            '-F', 'c',  # Custom format
            '-b',  # Include large objects
            '-v',  # Verbose
            '-f', str(backup_file),
            DB_NAME
        ]
        
        # Execute backup
        subprocess.run(command, check=True)
        logger.info(f"Database backup created: {backup_file}")
        return backup_file
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Database backup failed: {str(e)}")
        raise
    finally:
        # Clear PostgreSQL password
        os.environ['PGPASSWORD'] = ''

def cleanup_old_backups():
    """Remove backups older than BACKUP_RETENTION_DAYS."""
    try:
        current_time = time.time()
        
        # Check each backup file
        for backup_file in BACKUP_DIR.glob('backup_*.sql'):
            # Calculate file age in days
            file_age_days = (current_time - backup_file.stat().st_mtime) / (24 * 3600)
            
            # Delete if older than retention period
            if file_age_days > BACKUP_RETENTION_DAYS:
                backup_file.unlink()
                logger.info(f"Deleted old backup: {backup_file}")
                
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise

def main():
    """Main backup routine."""
    try:
        # Create backup
        backup_file = create_backup()
        
        # Cleanup old backups
        cleanup_old_backups()
        
        logger.info("Backup process completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Backup process failed: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 