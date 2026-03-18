"""
Configuration Export/Import API Endpoints
"""
from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
import json
import os
import tempfile

from app.api.auth import token_required
from app.api.sources import load_sources, save_sources
from app.config import Config

config_bp = Blueprint('config', __name__)


@config_bp.route('/export', methods=['GET'])
@token_required
def export_config(current_user):
    """Export all configuration as JSON"""
    try:
        # Load sources and strip credentials
        sources = load_sources()
        # Remove credential values from export (only keep env references)
        for source in sources:
            creds = source.get('credentials', {})
            for key in list(creds.keys()):
                if key.endswith('_env'):
                    continue  # Keep env var name references
                if 'token' in key.lower() or 'password' in key.lower() or 'key' in key.lower():
                    creds[key] = '***REDACTED***'

        # Get system settings
        settings = {
            'backup_base_path': Config.BACKUP_BASE_PATH,
            'max_parallel_tasks': Config.MAX_PARALLEL_TASKS,
            'log_retention_days': Config.LOG_RETENTION_DAYS,
        }

        # Create export data
        export_data = {
            'version': '1.0',
            'exported_at': datetime.utcnow().isoformat() + 'Z',
            'sources': sources,
            'settings': settings,
            'metadata': {
                'user': current_user.username,
                'total_sources': len(sources)
            }
        }

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            delete=False,
            suffix='.json',
            prefix='backupgenie_config_'
        )

        # Write to file
        json.dump(export_data, temp_file, indent=2)
        temp_file.close()

        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f'backupgenie_config_{timestamp}.json'

        # Send file and schedule cleanup
        response = send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )

        # Clean up temp file after response is sent
        @response.call_on_close
        def cleanup():
            try:
                os.unlink(temp_file.name)
            except OSError:
                pass

        return response

    except Exception as e:
        return jsonify({'error': 'Export failed'}), 500


@config_bp.route('/import', methods=['POST'])
@token_required
def import_config(current_user):
    """Import configuration from JSON"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No configuration data provided'}), 400

        # Validate schema
        if not isinstance(data, dict):
            return jsonify({'error': 'Invalid configuration format'}), 400

        if 'version' not in data:
            return jsonify({'error': 'Missing version field'}), 400

        # Validate version compatibility
        if data['version'] != '1.0':
            return jsonify({'error': f'Unsupported configuration version: {data["version"]}'}), 400

        # Get import options from query params
        merge = request.args.get('merge', 'false').lower() == 'true'

        # Import sources
        imported_sources = 0
        if 'sources' in data and isinstance(data['sources'], list):
            if merge:
                # Merge with existing sources
                existing_sources = load_sources()
                existing_ids = {s.get('id') for s in existing_sources}

                for source in data['sources']:
                    if source.get('id') not in existing_ids:
                        existing_sources.append(source)
                        imported_sources += 1

                save_sources(existing_sources)
            else:
                # Replace all sources
                save_sources(data['sources'])
                imported_sources = len(data['sources'])

        # Import settings (if provided)
        # Note: For now, we just validate them since Config uses environment variables
        # In the future, this could write to a persistent settings file
        imported_settings = 0
        if 'settings' in data and isinstance(data['settings'], dict):
            imported_settings = len(data['settings'])

        return jsonify({
            'message': 'Configuration imported successfully',
            'summary': {
                'sources_imported': imported_sources,
                'settings_imported': imported_settings,
                'merge_mode': merge,
                'imported_at': datetime.utcnow().isoformat() + 'Z',
                'imported_by': current_user.username
            }
        }), 200

    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON format'}), 400
    except Exception as e:
        return jsonify({'error': f'Import failed: {str(e)}'}), 500


@config_bp.route('/validate', methods=['POST'])
@token_required
def validate_config(current_user):
    """Validate configuration file without importing"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No configuration data provided'}), 400

        errors = []
        warnings = []

        # Check version
        if 'version' not in data:
            errors.append('Missing version field')
        elif data['version'] != '1.0':
            errors.append(f'Unsupported version: {data["version"]}')

        # Validate sources
        if 'sources' in data:
            if not isinstance(data['sources'], list):
                errors.append('Sources must be an array')
            else:
                for i, source in enumerate(data['sources']):
                    if not isinstance(source, dict):
                        errors.append(f'Source {i} is not an object')
                        continue

                    # Check required fields
                    if 'id' not in source:
                        warnings.append(f'Source {i} missing ID (will be auto-generated)')
                    if 'name' not in source:
                        errors.append(f'Source {i} missing name')
                    if 'type' not in source:
                        errors.append(f'Source {i} missing type')

        # Validate settings
        if 'settings' in data:
            if not isinstance(data['settings'], dict):
                errors.append('Settings must be an object')

        # Check for duplicate source IDs
        if 'sources' in data and isinstance(data['sources'], list):
            source_ids = [s.get('id') for s in data['sources'] if s.get('id')]
            if len(source_ids) != len(set(source_ids)):
                errors.append('Duplicate source IDs detected')

        is_valid = len(errors) == 0

        return jsonify({
            'valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'summary': {
                'total_sources': len(data.get('sources', [])),
                'has_settings': 'settings' in data,
                'version': data.get('version', 'unknown')
            }
        }), 200 if is_valid else 400

    except json.JSONDecodeError:
        return jsonify({
            'valid': False,
            'errors': ['Invalid JSON format'],
            'warnings': []
        }), 400
    except Exception as e:
        return jsonify({
            'valid': False,
            'errors': [f'Validation failed: {str(e)}'],
            'warnings': []
        }), 500
