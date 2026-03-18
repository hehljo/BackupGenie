"""
Settings API Endpoints
Provides system configuration and management
All settings are persisted in the database.
"""
from flask import Blueprint, request, jsonify
import shutil
import os

from app import db
from app.api.auth import token_required
from app.config import Config
from app.models.backup import Setting

settings_bp = Blueprint('settings', __name__)

# Settings that can be configured via UI
CONFIGURABLE_SETTINGS = {
    'backup_base_path': {'type': 'string', 'default': '/mnt/backup'},
    'max_parallel_tasks': {'type': 'int', 'default': 2, 'min': 1, 'max': 10},
    'log_retention_days': {'type': 'int', 'default': 30, 'min': 1},
}


def get_setting(key, default=None):
    """Get setting from DB, fall back to env, then default"""
    db_val = Setting.get(key)
    if db_val is not None:
        return db_val
    # Env fallback
    env_map = {
        'backup_base_path': 'BACKUP_BASE_PATH',
        'max_parallel_tasks': 'MAX_PARALLEL_TASKS',
        'log_retention_days': 'LOG_RETENTION_DAYS',
    }
    env_key = env_map.get(key)
    if env_key:
        env_val = os.environ.get(env_key)
        if env_val:
            return env_val
    return default


def get_credential(name):
    """Get credential from DB, fall back to env var"""
    db_val = Setting.get(f'credential.{name}')
    if db_val:
        return db_val
    env_map = {
        'github_token': 'GITHUB_TOKEN',
        'nas_password_1': 'NAS_PASSWORD_1',
        'supabase_db_password': 'SUPABASE_DB_PASSWORD',
        'supabase_service_role_key': 'SUPABASE_SERVICE_ROLE_KEY',
        'smtp_password': 'SMTP_PASSWORD',
        'telegram_bot_token': 'TELEGRAM_BOT_TOKEN',
        'rclone_gdrive_token': 'RCLONE_CONFIG_GDRIVE_TOKEN',
    }
    env_key = env_map.get(name)
    if env_key:
        return os.environ.get(env_key, '')
    return ''


@settings_bp.route('', methods=['GET'])
@token_required
def get_settings(current_user):
    """Get current system settings with real storage stats"""
    backup_path = get_setting('backup_base_path', Config.BACKUP_BASE_PATH)

    try:
        stat = shutil.disk_usage(backup_path)
        storage = {
            'total_bytes': stat.total,
            'used_bytes': stat.used,
            'free_bytes': stat.free,
            'percentage_used': round((stat.used / stat.total) * 100, 2) if stat.total > 0 else 0
        }
    except Exception as e:
        storage = {
            'total_bytes': 0,
            'used_bytes': 0,
            'free_bytes': 0,
            'percentage_used': 0,
            'error': str(e)
        }

    settings = {
        'backup_base_path': backup_path,
        'max_parallel_tasks': int(get_setting('max_parallel_tasks', 2)),
        'log_retention_days': int(get_setting('log_retention_days', 30)),
        'api_auth_enabled': True,
        'https_only': os.getenv('FORCE_HTTPS', 'false').lower() == 'true',
        'auto_cleanup': os.getenv('AUTO_CLEANUP', 'true').lower() == 'true',
        'storage': storage
    }

    return jsonify(settings), 200


@settings_bp.route('', methods=['PUT'])
@token_required
def update_settings(current_user):
    """Update system settings - persisted in database"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    updated = []

    for key, meta in CONFIGURABLE_SETTINGS.items():
        if key not in data:
            continue

        value = data[key]

        if meta['type'] == 'int':
            try:
                value = int(value)
                if 'min' in meta and value < meta['min']:
                    return jsonify({'error': f'{key} must be at least {meta["min"]}'}), 400
                if 'max' in meta and value > meta['max']:
                    return jsonify({'error': f'{key} must be at most {meta["max"]}'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': f'{key} must be a number'}), 400

        Setting.set(key, str(value))
        updated.append(key)

    return jsonify({
        'message': 'Settings updated successfully',
        'updated': updated
    }), 200


# --- Global Credentials ---

@settings_bp.route('/credentials', methods=['GET'])
@token_required
def get_credentials(current_user):
    """Get which credentials are configured (never returns actual values)"""
    credentials = {}
    cred_names = [
        'github_token', 'nas_password_1',
        'supabase_db_password', 'supabase_service_role_key',
        'smtp_password', 'telegram_bot_token', 'rclone_gdrive_token'
    ]
    for name in cred_names:
        val = get_credential(name)
        credentials[name] = {
            'configured': bool(val),
            'source': 'database' if Setting.get(f'credential.{name}') else ('environment' if val else 'not set')
        }

    return jsonify(credentials), 200


@settings_bp.route('/credentials', methods=['PUT'])
@token_required
def update_credentials(current_user):
    """Update global credentials - stored in database"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    allowed = [
        'github_token', 'nas_password_1',
        'supabase_db_password', 'supabase_service_role_key',
        'smtp_password', 'telegram_bot_token', 'rclone_gdrive_token'
    ]

    updated = []
    for key, value in data.items():
        if key not in allowed:
            continue
        Setting.set(f'credential.{key}', value)
        updated.append(key)

    return jsonify({
        'message': 'Credentials updated',
        'updated': updated
    }), 200
