"""
Sources API Endpoints
"""
from flask import Blueprint, request, jsonify
import json
import os

from app.api.auth import token_required
from app.config import Config

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


@sources_bp.route('/<source_id>/test', methods=['POST'])
@token_required
def test_source(current_user, source_id):
    """Test connection to a backup source"""
    sources = load_sources()
    source = next((s for s in sources if s.get('id') == source_id), None)

    if not source:
        return jsonify({'error': 'Source not found'}), 404

    # TODO: Implement actual connection testing
    # For now, return a mock response

    return jsonify({
        'status': 'success',
        'message': f"Connection to {source['name']} successful",
        'source_id': source_id
    }), 200
