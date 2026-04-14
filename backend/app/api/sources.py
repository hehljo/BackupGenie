"""
Sources API Endpoints
"""
from flask import Blueprint, request, jsonify
import json
import logging
import os

from app.api.auth import token_required
from app import limiter
from app.config import Config
from app.services.github_discovery import discover_all

logger = logging.getLogger(__name__)

sources_bp = Blueprint('sources', __name__)


def load_sources():
    """Load sources from configuration file"""
    try:
        with open(Config.SOURCES_CONFIG_PATH, 'r') as f:
            config = json.load(f)
            return config.get('backup_sources', [])
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def save_sources(sources):
    """Save sources to configuration file"""
    config = {'backup_sources': sources}
    os.makedirs(os.path.dirname(Config.SOURCES_CONFIG_PATH), exist_ok=True)
    with open(Config.SOURCES_CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)


@sources_bp.route('', methods=['GET'])
@token_required
def get_sources(current_user):
    """Get all backup sources"""
    sources = load_sources()
    return jsonify({'sources': sources}), 200


@sources_bp.route('/<source_id>', methods=['GET'])
@token_required
def get_source(current_user, source_id):
    """Get a specific source"""
    sources = load_sources()
    source = next((s for s in sources if s.get('id') == source_id), None)

    if not source:
        return jsonify({'error': 'Source not found'}), 404

    return jsonify(source), 200


@sources_bp.route('', methods=['POST'])
@token_required
def create_source(current_user):
    """Create a new backup source"""
    data = request.get_json()

    if not data or not data.get('name') or not data.get('type'):
        return jsonify({'error': 'Missing required fields: name, type'}), 400

    sources = load_sources()

    # Generate ID if not provided
    if not data.get('id'):
        import uuid
        data['id'] = f"{data['type']}-{str(uuid.uuid4())[:8]}"

    # Check for duplicate ID
    if any(s.get('id') == data['id'] for s in sources):
        return jsonify({'error': 'Source ID already exists'}), 400

    # Set defaults
    data.setdefault('enabled', True)
    data.setdefault('priority', len(sources) + 1)

    sources.append(data)
    save_sources(sources)

    return jsonify({
        'message': 'Source created successfully',
        'source': data
    }), 201


@sources_bp.route('/<source_id>', methods=['PUT'])
@token_required
def update_source(current_user, source_id):
    """Update a backup source"""
    data = request.get_json()
    sources = load_sources()

    source_index = next((i for i, s in enumerate(sources) if s.get('id') == source_id), None)

    if source_index is None:
        return jsonify({'error': 'Source not found'}), 404

    # Update source
    sources[source_index].update(data)
    sources[source_index]['id'] = source_id  # Ensure ID doesn't change

    save_sources(sources)

    return jsonify({
        'message': 'Source updated successfully',
        'source': sources[source_index]
    }), 200


@sources_bp.route('/<source_id>', methods=['DELETE'])
@token_required
def delete_source(current_user, source_id):
    """Delete a backup source"""
    sources = load_sources()
    sources = [s for s in sources if s.get('id') != source_id]

    save_sources(sources)

    return jsonify({'message': 'Source deleted successfully'}), 200


@sources_bp.route('/github/discover', methods=['GET'])
@token_required
@limiter.limit("5 per hour")
def discover_github_repos(current_user):
    """Discover all GitHub repositories accessible with the configured token"""
    from app.api.settings import get_credential
    token = get_credential('github_token')

    if not token:
        return jsonify({'error': 'GitHub Token not configured. Set it in Settings → Credentials.'}), 400

    try:
        result = discover_all(token)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"GitHub discovery failed: {e}")
        return jsonify({'error': 'GitHub API request failed'}), 502


@sources_bp.route('/<source_id>/test', methods=['POST'])
@token_required
def test_source(current_user, source_id):
    """Test connection to a backup source"""
    sources = load_sources()
    source = next((s for s in sources if s.get('id') == source_id), None)

    if not source:
        return jsonify({'error': 'Source not found'}), 404

    source_type = source.get('type')
    source_name = source.get('name')

    # Real connection testing based on source type
    try:
        if source_type == 'local':
            # Test local directory access with path traversal protection
            import os
            path = source.get('config', {}).get('path', '')
            if not path:
                return jsonify({'error': 'Path not configured'}), 400
            # Resolve to absolute and check for traversal
            resolved = os.path.realpath(path)
            allowed_prefixes = ['/mnt/', '/data/', '/backup/', '/home/', '/opt/']
            if not any(resolved.startswith(p) for p in allowed_prefixes):
                return jsonify({'error': 'Path not in allowed directory'}), 403
            if not os.path.exists(resolved):
                return jsonify({'error': 'Path does not exist'}), 400
            if not os.access(resolved, os.R_OK):
                return jsonify({'error': 'No read permission'}), 403
            return jsonify({
                'status': 'success',
                'message': 'Local directory accessible',
                'source_id': source_id
            }), 200

        elif source_type == 'nas' or source_type == 'nfs':
            # Test network share connectivity
            host = source.get('config', {}).get('host', '')
            if not host:
                return jsonify({'error': 'Host not configured'}), 400

            # Simple network connectivity test
            import socket
            try:
                socket.create_connection((host, 445 if source_type == 'nas' else 2049), timeout=5)
                return jsonify({
                    'status': 'success',
                    'message': f'Connection to {host} successful',
                    'source_id': source_id
                }), 200
            except (socket.timeout, socket.error) as e:
                return jsonify({'error': f'Cannot connect to {host}: {str(e)}'}), 503

        elif source_type == 'github':
            # Test GitHub API access
            token = source.get('config', {}).get('token', '')
            repo = source.get('config', {}).get('repo', '')
            if not token or not repo:
                return jsonify({'error': 'Token or repository not configured'}), 400

            import requests
            headers = {'Authorization': f'token {token}'}
            response = requests.get(f'https://api.github.com/repos/{repo}', headers=headers, timeout=10)

            if response.status_code == 200:
                return jsonify({
                    'status': 'success',
                    'message': f'GitHub repository {repo} accessible',
                    'source_id': source_id
                }), 200
            elif response.status_code == 401:
                return jsonify({'error': 'Invalid GitHub token'}), 401
            elif response.status_code == 404:
                return jsonify({'error': f'Repository {repo} not found'}), 404
            else:
                return jsonify({'error': f'GitHub API error: {response.status_code}'}), 503

        else:
            # For other source types, return informative message
            return jsonify({
                'status': 'info',
                'message': f'Connection test for {source_type} not yet implemented. Source will be tested during actual backup.',
                'source_id': source_id
            }), 200

    except Exception as e:
        return jsonify({'error': f'Connection test failed: {str(e)}'}), 500


@sources_bp.route('/supabase/test', methods=['POST'])
@token_required
def test_supabase_connection(current_user):
    """Test Supabase database connection using pg_dump/psql"""
    import subprocess
    data = request.get_json() or {}

    project_ref = data.get('project_ref', '')
    region = data.get('region', 'aws-0-us-east-1')

    if not project_ref:
        return jsonify({'error': 'Project Ref ist erforderlich'}), 400

    # 1. Check if pg_dump is available
    try:
        result = subprocess.run(
            ['pg_dump', '--version'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return jsonify({'error': 'pg_dump nicht verfügbar im Container'}), 500
        pg_version = result.stdout.strip()
    except FileNotFoundError:
        return jsonify({'error': 'pg_dump nicht installiert'}), 500
    except Exception as e:
        return jsonify({'error': f'pg_dump Check fehlgeschlagen: {str(e)}'}), 500

    # 2. Get DB password from credentials
    from app.api.settings import get_credential
    db_password = get_credential('supabase_db_password')

    if not db_password:
        return jsonify({
            'error': 'Supabase DB Password nicht konfiguriert. Bitte unter Settings → Credentials eintragen.'
        }), 400

    # 3. Build connection string and test
    connection_string = (
        f"postgresql://postgres.{project_ref}:{db_password}"
        f"@{region}.pooler.supabase.com:5432/postgres"
    )

    try:
        result = subprocess.run(
            ['psql', connection_string, '-c', 'SELECT 1;'],
            capture_output=True, text=True, timeout=15
        )

        if result.returncode == 0:
            return jsonify({
                'status': 'success',
                'message': f'Verbindung erfolgreich! ({pg_version})',
            }), 200
        else:
            error_msg = result.stderr.strip()
            if 'password authentication failed' in error_msg.lower():
                return jsonify({'error': 'DB Password falsch. Prüfe Settings → Credentials.'}), 401
            elif 'could not translate host name' in error_msg.lower():
                return jsonify({'error': f'Region oder Project Ref falsch: {region}'}), 400
            else:
                return jsonify({'error': f'Verbindung fehlgeschlagen: {error_msg}'}), 503

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Verbindung Timeout (15s) - prüfe Region und Project Ref'}), 504
    except Exception as e:
        return jsonify({'error': f'Verbindungstest fehlgeschlagen: {str(e)}'}), 500

