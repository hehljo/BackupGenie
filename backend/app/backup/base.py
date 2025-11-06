"""
Base class for backup handlers
"""
from abc import ABC, abstractmethod
import logging
import os

logger = logging.getLogger(__name__)


class BackupHandler(ABC):
    """Abstract base class for backup handlers"""

    def __init__(self, source_config, dest_path):
        """
        Initialize backup handler

        Args:
            source_config: Configuration dict for the source
            dest_path: Destination path for backups
        """
        self.source_config = source_config
        self.dest_path = dest_path
        self.logs = []

    @abstractmethod
    def backup(self):
        """
        Execute backup operation

        Returns:
            dict: {
                'files_synced': int,
                'size_synced': int,
                'logs': str
            }
        """
        pass

    def log(self, message):
        """Add a log message"""
        self.logs.append(message)
        logger.info(message)

    def get_logs(self):
        """Get all logs as a string"""
        return '\n'.join(self.logs)

    def _get_directory_size(self, path):
        """Get total size of directory"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except:
                    pass
        return total_size

    def _get_file_size(self, path):
        """Get size of a single file"""
        try:
            return os.path.getsize(path)
        except:
            return 0

    def _get_env_credential(self, key, required=True):
        """Get credential from environment variable"""
        value = os.environ.get(key, '')
        if required and not value:
            raise Exception(f"Required environment variable not found: {key}")
        return value
