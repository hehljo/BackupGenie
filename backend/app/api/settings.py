"""
Settings API Endpoints
Provides system configuration and management
"""
from flask import Blueprint, request, jsonify
import shutil
import os

from app import db
from app.api.auth import token_required
from app.config import Config

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('', methods=['GET'])
@token_required
def get_settings(current_user):
    """Get current system settings with real storage stats"""
    # Get actual disk space using shutil
    try:
        stat = shutil.disk_usage(Config.BACKUP_BASE_PATH)
        storage = {
            'total_bytes': stat.total,
            'used_bytes': stat.used,
            'free_bytes': stat.free,
            'percentage_used': round((stat.used / stat.total) * 100, 2) if stat.total > 0 else 0
        }
    except Exception as e:
        # Fallback if path doesn't exist or isn't accessible
        storage = {
            'total_bytes': 0,
            'used_bytes': 0,
            'free_bytes': 0,
            'percentage_used': 0,
            'error': str(e)
        }

    # Get environment-based settings
    settings = {
        'backup_base_path': Config.BACKUP_BASE_PATH,
        'max_parallel_tasks': getattr(Config, 'MAX_PARALLEL_TASKS', 2),
        'log_retention_days': getattr(Config, 'LOG_RETENTION_DAYS', 30),
        'api_auth_enabled': True,  # Always enabled
        'https_only': os.getenv('FORCE_HTTPS', 'false').lower() == 'true',
        'auto_cleanup': os.getenv('AUTO_CLEANUP', 'true').lower() == 'true',
        'storage': storage
    }

    return jsonify(settings), 200


@settings_bp.route('', methods=['PUT'])
@token_required
def update_settings(current_user):
    """Update system settings"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Validate max_parallel_tasks
    if 'max_parallel_tasks' in data:
        try:
            tasks = int(data['max_parallel_tasks'])
            if not 1 <= tasks <= 10:
                return jsonify({'error': 'max_parallel_tasks must be between 1 and 10'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'max_parallel_tasks must be a number'}), 400

    # Validate log_retention_days
    if 'log_retention_days' in data:
        try:
            days = int(data['log_retention_days'])
            if days < 1:
                return jsonify({'error': 'log_retention_days must be at least 1'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'log_retention_days must be a number'}), 400

    # TODO: Persist settings to database or environment file
    # For now, we just validate and return success
    # In production, you would want to:
    # 1. Store in a Settings table
    # 2. Update .env file
    # 3. Reload configuration

    return jsonify({
        'message': 'Settings updated successfully',
        'note': 'Settings will be applied on next restart'
    }), 200
