"""
Configuration Module
"""
import os
from datetime import timedelta


def _get_int_env(name, default):
    value = os.environ.get(name, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', '')
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

    @staticmethod
    def validate():
        """Validate critical configuration at startup"""
        if not Config.SECRET_KEY or Config.SECRET_KEY == 'dev-secret-key-change-in-production':
            raise RuntimeError(
                "FATAL: SECRET_KEY is not set or uses the insecure default. "
                "Set a strong, random SECRET_KEY environment variable. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )

    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:////data/backupgenie.db')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Backup Configuration
    BACKUP_BASE_PATH = os.environ.get('BACKUP_BASE_PATH', '/mnt/backup')
    MAX_PARALLEL_TASKS = _get_int_env('MAX_PARALLEL_TASKS', 2)
    LOG_RETENTION_DAYS = _get_int_env('LOG_RETENTION_DAYS', 30)

    # API Configuration
    API_PORT = _get_int_env('API_PORT', 5000)
    API_HOST = os.environ.get('API_HOST', '0.0.0.0')

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # Sources Configuration
    SOURCES_CONFIG_PATH = os.environ.get('SOURCES_CONFIG_PATH', '/app/config/sources.json')
    RCLONE_CONFIG_PATH = os.environ.get('RCLONE_CONFIG_PATH', '/app/config/rclone.conf')

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', '/var/log/backupgenie/app.log')
