"""
Base notification channel interface
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Optional, List
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(Enum):
    """Notification event types"""
    BACKUP_STARTED = "backup_started"
    BACKUP_COMPLETED = "backup_completed"
    BACKUP_FAILED = "backup_failed"
    BACKUP_PARTIAL = "backup_partial"
    SOURCE_FAILED = "source_failed"
    SYSTEM_WARNING = "system_warning"
    SYSTEM_ERROR = "system_error"


class NotificationChannel(ABC):
    """Abstract base class for notification channels"""

    def __init__(self, config: Dict):
        """
        Initialize notification channel

        Args:
            config: Channel-specific configuration
        """
        self.config = config
        self.enabled = config.get('enabled', True)
        self.name = config.get('name', self.__class__.__name__)
        self.retry_count = config.get('retry_count', 3)
        self.retry_delay = config.get('retry_delay', 2)  # seconds
        self.timeout = config.get('timeout', 10)  # seconds

    @abstractmethod
    def send(self,
             title: str,
             message: str,
             priority: NotificationPriority = NotificationPriority.NORMAL,
             notification_type: NotificationType = NotificationType.BACKUP_COMPLETED,
             data: Optional[Dict] = None) -> bool:
        """
        Send notification

        Args:
            title: Notification title
            message: Notification message body
            priority: Priority level
            notification_type: Type of notification
            data: Additional contextual data

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    def send_with_retry(self,
                        title: str,
                        message: str,
                        priority: NotificationPriority = NotificationPriority.NORMAL,
                        notification_type: NotificationType = NotificationType.BACKUP_COMPLETED,
                        data: Optional[Dict] = None) -> bool:
        """
        Send notification with retry logic

        Args:
            title: Notification title
            message: Notification message body
            priority: Priority level
            notification_type: Type of notification
            data: Additional contextual data

        Returns:
            bool: True if successful, False otherwise
        """
        import time

        for attempt in range(self.retry_count):
            try:
                if self.send(title, message, priority, notification_type, data):
                    logger.info(f"Notification sent via {self.name} (attempt {attempt + 1})")
                    return True
            except Exception as e:
                logger.warning(f"Notification failed via {self.name} (attempt {attempt + 1}/{self.retry_count}): {e}")

            if attempt < self.retry_count - 1:
                # Exponential backoff
                sleep_time = self.retry_delay * (2 ** attempt)
                time.sleep(sleep_time)

        logger.error(f"Notification failed via {self.name} after {self.retry_count} attempts")
        return False

    def is_enabled(self) -> bool:
        """Check if channel is enabled"""
        return self.enabled

    def format_duration(self, seconds: int) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"

    def format_size(self, bytes_size: int) -> str:
        """Format bytes in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"

    def validate_config(self) -> tuple[bool, Optional[str]]:
        """
        Validate channel configuration

        Returns:
            tuple: (is_valid, error_message)
        """
        return True, None
