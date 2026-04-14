"""
Settings API Endpoints
Provides system configuration and management
All settings are persisted in the database.
"""
from flask import Blueprint, request, jsonify
import shutil
import os
import subprocess

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


def get_credential(name, profile=None):
    """Get credential from DB, fall back to env var.

    Args:
        name: Credential type (e.g. 'github_token')
        profile: Optional profile name. If None, returns first available.
    """
    if profile:
        # Specific profile requested
        db_val = Setting.get(f'credential.{name}.{profile}')
        if db_val:
            return db_val
    else:
        # Try legacy single-key format first (backward compat)
        db_val = Setting.get(f'credential.{name}')
        if db_val:
            return db_val
        # Try first available profile
        all_settings = Setting.query.filter(
            Setting.key.like(f'credential.{name}.%')
        ).first()
        if all_settings:
            from app.crypto import decrypt_value
            decrypted = decrypt_value(all_settings.value)
            if decrypted:
                return decrypted

    # Env fallback
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


def get_credential_profiles(name):
    """Get all profiles for a credential type.

    Returns:
        list of dicts: [{'profile': 'privat', 'configured': True, 'source': 'database'}, ...]
    """
    profiles = []
    # Check legacy single-key
    legacy = Setting.query.filter_by(key=f'credential.{name}').first()
    if legacy:
        profiles.append({
            'profile': 'default',
            'configured': True,
            'source': 'database'
        })
    # Check profiled keys
    profiled = Setting.query.filter(
        Setting.key.like(f'credential.{name}.%')
    ).all()
    for s in profiled:
        profile_name = s.key.split(f'credential.{name}.', 1)[1]
        profiles.append({
            'profile': profile_name,
            'configured': True,
            'source': 'database'
        })
    # Check env fallback
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
    if env_key and os.environ.get(env_key):
        # Only add env profile if no DB profiles exist
        if not profiles:
            profiles.append({
                'profile': 'default',
                'configured': True,
                'source': 'environment'
            })
    return profiles


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

CREDENTIAL_TYPES = [
    'github_token', 'nas_password_1',
    'supabase_db_password', 'supabase_service_role_key',
    'smtp_password', 'telegram_bot_token', 'rclone_gdrive_token'
]


@settings_bp.route('/credentials', methods=['GET'])
@token_required
def get_credentials(current_user):
    """Get all credential profiles per type (never returns actual values)"""
    credentials = {}
    for name in CREDENTIAL_TYPES:
        profiles = get_credential_profiles(name)
        credentials[name] = {
            'profiles': profiles,
            'configured': len(profiles) > 0
        }

    return jsonify(credentials), 200


@settings_bp.route('/credentials', methods=['PUT'])
@token_required
def update_credentials(current_user):
    """Update credentials - supports legacy flat format and new profile format"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    updated = []
    for key, value in data.items():
        if key not in CREDENTIAL_TYPES:
            continue
        # Legacy format: flat value string → save as default profile
        if isinstance(value, str) and value.strip():
            Setting.set(f'credential.{key}.default', value.strip())
            # Remove legacy single-key if exists
            legacy = Setting.query.filter_by(key=f'credential.{key}').first()
            if legacy:
                db.session.delete(legacy)
                db.session.commit()
            updated.append(key)

    return jsonify({
        'message': 'Credentials updated',
        'updated': updated
    }), 200


@settings_bp.route('/credentials/profile', methods=['POST'])
@token_required
def add_credential_profile(current_user):
    """Add a new credential profile"""
    data = request.get_json()
    cred_type = data.get('type')
    profile = data.get('profile', '').strip()
    value = data.get('value', '').strip()

    if not cred_type or cred_type not in CREDENTIAL_TYPES:
        return jsonify({'error': 'Invalid credential type'}), 400
    if not profile:
        return jsonify({'error': 'Profile name is required'}), 400
    if not value:
        return jsonify({'error': 'Value is required'}), 400

    # Sanitize profile name
    profile = profile.lower().replace(' ', '_')
    if len(profile) > 50:
        return jsonify({'error': 'Profile name too long (max 50 chars)'}), 400

    Setting.set(f'credential.{cred_type}.{profile}', value)

    return jsonify({
        'message': f'Profile "{profile}" saved for {cred_type}',
        'profile': profile
    }), 200


@settings_bp.route('/credentials/profile', methods=['DELETE'])
@token_required
def delete_credential_profile(current_user):
    """Delete a credential profile"""
    data = request.get_json()
    cred_type = data.get('type')
    profile = data.get('profile', '').strip()

    if not cred_type or cred_type not in CREDENTIAL_TYPES:
        return jsonify({'error': 'Invalid credential type'}), 400
    if not profile:
        return jsonify({'error': 'Profile name is required'}), 400

    key = f'credential.{cred_type}.{profile}'
    setting = Setting.query.filter_by(key=key).first()
    if not setting:
        return jsonify({'error': 'Profile not found'}), 404

    db.session.delete(setting)
    db.session.commit()

    return jsonify({'message': f'Profile "{profile}" deleted'}), 200


# --- System Logs ---

@settings_bp.route('/logs', methods=['GET'])
@token_required
def get_logs(current_user):
    """Get system log file contents"""
    lines = request.args.get('lines', 200, type=int)
    lines = min(lines, 2000)  # Cap at 2000

    log_file = Config.LOG_FILE
    if not os.path.isfile(log_file):
        return jsonify({'logs': '', 'lines': 0, 'file': log_file}), 200

    try:
        # Use tail for efficient reading of last N lines
        result = subprocess.run(
            ['tail', '-n', str(lines), log_file],
            capture_output=True, text=True, timeout=5
        )
        content = result.stdout
        line_count = content.count('\n')
        return jsonify({
            'logs': content,
            'lines': line_count,
            'file': log_file
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to read logs: {str(e)}'}), 500


@settings_bp.route('/logs/clear', methods=['POST'])
@token_required
def clear_logs(current_user):
    """Clear the log file"""
    log_file = Config.LOG_FILE
    if os.path.isfile(log_file):
        try:
            with open(log_file, 'w') as f:
                f.write('')
            return jsonify({'message': 'Logs cleared'}), 200
        except Exception as e:
            return jsonify({'error': f'Failed to clear logs: {str(e)}'}), 500
    return jsonify({'message': 'No log file found'}), 200
