"""
Configuration Module
"""
import os
from datetime import timedelta


class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:////data/backupgenie.db')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Backup Configuration
    BACKUP_BASE_PATH = os.environ.get('BACKUP_BASE_PATH', '/mnt/backup')
    MAX_PARALLEL_TASKS = int(os.environ.get('MAX_PARALLEL_TASKS', 2))
    LOG_RETENTION_DAYS = int(os.environ.get('LOG_RETENTION_DAYS', 30))

    # API Configuration
    API_PORT = int(os.environ.get('API_PORT', 5000))
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
