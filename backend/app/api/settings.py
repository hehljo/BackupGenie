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
    'backup_retention_count': {'type': 'int', 'default': 10, 'min': 1, 'max': 1000},
    'auto_cleanup': {'type': 'bool', 'default': True},
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
        'backup_retention_count': 'BACKUP_RETENTION_COUNT',
        'auto_cleanup': 'AUTO_CLEANUP',
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
        name: Legacy credential key (e.g. 'github_token') or provider.field (e.g. 'github.token')
        profile: Optional profile name. If None, returns first available.
    """
    # Resolve provider-based key: convert legacy names to provider.field
    legacy_to_provider = {}
    for provider, meta in CREDENTIAL_PROVIDERS.items():
        for field, legacy_key in meta['legacy_map'].items():
            legacy_to_provider[legacy_key] = f'{provider}.{field}'

    provider_key = legacy_to_provider.get(name, name)

    if profile:
        db_val = Setting.get(f'credential.{provider_key}.{profile}')
        if db_val:
            return db_val
    else:
        # Try legacy single-key format (backward compat)
        db_val = Setting.get(f'credential.{name}')
        if db_val:
            return db_val
        # Try provider-based keys
        db_val = Setting.get(f'credential.{provider_key}')
        if db_val:
            return db_val
        # Try first available profile
        all_settings = Setting.query.filter(
            Setting.key.like(f'credential.{provider_key}.%')
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


def get_provider_profiles(provider):
    """Get all profiles for a provider (e.g. 'supabase').

    Returns:
        list of dicts with profile name and which fields are configured.
    """
    meta = CREDENTIAL_PROVIDERS.get(provider)
    if not meta:
        return []

    # Collect all profile names from DB
    profile_names = set()
    for field in meta['fields']:
        key_prefix = f'credential.{provider}.{field}.'
        settings = Setting.query.filter(Setting.key.like(key_prefix + '%')).all()
        for s in settings:
            profile_name = s.key.split(key_prefix, 1)[1]
            profile_names.add(profile_name)

    # Check legacy single-key entries
    has_legacy = False
    for field, legacy_key in meta['legacy_map'].items():
        if Setting.query.filter_by(key=f'credential.{legacy_key}').first():
            has_legacy = True
            break

    profiles = []
    if has_legacy:
        fields_status = {}
        for field, legacy_key in meta['legacy_map'].items():
            fields_status[field] = bool(Setting.get(f'credential.{legacy_key}'))
        profiles.append({
            'profile': 'default',
            'source': 'database',
            'fields': fields_status
        })

    for pname in sorted(profile_names):
        fields_status = {}
        for field in meta['fields']:
            val = Setting.get(f'credential.{provider}.{field}.{pname}')
            fields_status[field] = bool(val)
        profiles.append({
            'profile': pname,
            'source': 'database',
            'fields': fields_status
        })

    # Env fallback
    if not profiles:
        has_env = False
        fields_status = {}
        for field, env_key in meta['env_map'].items():
            val = os.environ.get(env_key, '')
            fields_status[field] = bool(val)
            if val:
                has_env = True
        if has_env:
            profiles.append({
                'profile': 'default',
                'source': 'environment',
                'fields': fields_status
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
        'backup_retention_count': int(get_setting('backup_retention_count', 10)),
        'api_auth_enabled': True,
        'https_only': os.getenv('FORCE_HTTPS', 'false').lower() == 'true',
        'auto_cleanup': str(get_setting('auto_cleanup', 'true')).lower() == 'true',
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
        elif meta['type'] == 'bool':
            value = str(value).lower() in ('true', '1', 'yes', 'on')

        Setting.set(key, str(value))
        updated.append(key)

    return jsonify({
        'message': 'Settings updated successfully',
        'updated': updated
    }), 200


# --- Global Credentials ---

# Credential providers with their fields
CREDENTIAL_PROVIDERS = {
    'github': {
        'fields': ['token'],
        'legacy_map': {'token': 'github_token'},
        'env_map': {'token': 'GITHUB_TOKEN'},
    },
    'nas': {
        'fields': ['password'],
        'legacy_map': {'password': 'nas_password_1'},
        'env_map': {'password': 'NAS_PASSWORD_1'},
    },
    'supabase': {
        'fields': ['connection_string', 'db_password', 'service_role_key'],
        'legacy_map': {'connection_string': 'supabase_connection_string', 'db_password': 'supabase_db_password', 'service_role_key': 'supabase_service_role_key'},
        'env_map': {'connection_string': 'SUPABASE_CONNECTION_STRING', 'db_password': 'SUPABASE_DB_PASSWORD', 'service_role_key': 'SUPABASE_SERVICE_ROLE_KEY'},
    },
    'smtp': {
        'fields': ['password'],
        'legacy_map': {'password': 'smtp_password'},
        'env_map': {'password': 'SMTP_PASSWORD'},
    },
    'telegram': {
        'fields': ['bot_token'],
        'legacy_map': {'bot_token': 'telegram_bot_token'},
        'env_map': {'bot_token': 'TELEGRAM_BOT_TOKEN'},
    },
    'gdrive': {
        'fields': ['token'],
        'legacy_map': {'token': 'rclone_gdrive_token'},
        'env_map': {'token': 'RCLONE_CONFIG_GDRIVE_TOKEN'},
    },
}

# Flat list for backward compat
CREDENTIAL_TYPES = [
    'github_token', 'nas_password_1',
    'supabase_db_password', 'supabase_service_role_key',
    'smtp_password', 'telegram_bot_token', 'rclone_gdrive_token'
]


@settings_bp.route('/credentials', methods=['GET'])
@token_required
def get_credentials(current_user):
    """Get all credential providers with their profiles (never returns actual values)"""
    credentials = {}
    for provider, meta in CREDENTIAL_PROVIDERS.items():
        profiles = get_provider_profiles(provider)
        credentials[provider] = {
            'fields': meta['fields'],
            'profiles': profiles,
            'configured': len(profiles) > 0
        }

    return jsonify(credentials), 200


@settings_bp.route('/credentials', methods=['PUT'])
@token_required
def update_credentials(current_user):
    """Legacy: Update credentials with flat key-value format"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    updated = []
    for key, value in data.items():
        if key not in CREDENTIAL_TYPES:
            continue
        if isinstance(value, str) and value.strip():
            Setting.set(f'credential.{key}', value.strip())
            updated.append(key)

    return jsonify({
        'message': 'Credentials updated',
        'updated': updated
    }), 200


@settings_bp.route('/credentials/profile', methods=['POST'])
@token_required
def add_credential_profile(current_user):
    """Add or update a credential profile for a provider"""
    data = request.get_json()
    provider = data.get('provider', '').strip()
    profile = data.get('profile', '').strip()
    values = data.get('values', {})

    if not provider or provider not in CREDENTIAL_PROVIDERS:
        return jsonify({'error': 'Invalid provider'}), 400
    if not profile:
        return jsonify({'error': 'Profile name is required'}), 400
    if not values:
        return jsonify({'error': 'At least one field value is required'}), 400

    meta = CREDENTIAL_PROVIDERS[provider]

    # Sanitize profile name
    profile = profile.lower().replace(' ', '_')
    if len(profile) > 50:
        return jsonify({'error': 'Profile name too long (max 50 chars)'}), 400

    saved_fields = []
    for field, value in values.items():
        if field not in meta['fields']:
            continue
        if value and value.strip():
            Setting.set(f'credential.{provider}.{field}.{profile}', value.strip())
            saved_fields.append(field)

    if not saved_fields:
        return jsonify({'error': 'No valid fields provided'}), 400

    return jsonify({
        'message': f'Profile "{profile}" saved for {provider}',
        'profile': profile,
        'fields': saved_fields
    }), 200


@settings_bp.route('/credentials/profile', methods=['DELETE'])
@token_required
def delete_credential_profile(current_user):
    """Delete a credential profile (all fields)"""
    data = request.get_json()
    provider = data.get('provider', '').strip()
    profile = data.get('profile', '').strip()

    if not provider or provider not in CREDENTIAL_PROVIDERS:
        return jsonify({'error': 'Invalid provider'}), 400
    if not profile:
        return jsonify({'error': 'Profile name is required'}), 400

    meta = CREDENTIAL_PROVIDERS[provider]
    deleted = 0

    # Delete all fields for this profile
    for field in meta['fields']:
        key = f'credential.{provider}.{field}.{profile}'
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            db.session.delete(setting)
            deleted += 1

    # Also check legacy keys if profile is 'default'
    if profile == 'default':
        for field, legacy_key in meta['legacy_map'].items():
            setting = Setting.query.filter_by(key=f'credential.{legacy_key}').first()
            if setting:
                db.session.delete(setting)
                deleted += 1

    if deleted == 0:
        return jsonify({'error': 'Profile not found'}), 404

    db.session.commit()
    return jsonify({'message': f'Profile "{profile}" deleted ({deleted} fields)'}), 200


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
