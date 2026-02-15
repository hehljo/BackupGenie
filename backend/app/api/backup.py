"""
Backup API Endpoints
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
import threading

from app import db
from app.models.backup import Backup, BackupSourceResult
from app.api.auth import token_required
from app.backup.executor import BackupExecutor

backup_bp = Blueprint('backup', __name__)


@backup_bp.route('/start', methods=['POST'])
@token_required
def start_backup(current_user):
    """Start a new backup"""
    data = request.get_json() or {}

    # Create backup record
    backup_id = str(uuid.uuid4())
    backup = Backup(
        backup_id=backup_id,
        status='pending',
        trigger_type=data.get('trigger_type', 'manual')
    )

    db.session.add(backup)
    db.session.commit()

    # Start backup in background thread
    executor = BackupExecutor(backup_id)
    sources = data.get('sources', [])
    parallel = data.get('parallel', 2)

    thread = threading.Thread(
        target=executor.execute,
        args=(sources, parallel)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'backup_id': backup_id,
        'status': 'started',
        'started_at': backup.started_at.isoformat(),
        'sources': len(sources) if sources else 'all'
    }), 202


@backup_bp.route('/<backup_id>', methods=['GET'])
@token_required
def get_backup_status(current_user, backup_id):
    """Get backup status"""
    backup = Backup.query.filter_by(backup_id=backup_id).first()

    if not backup:
        return jsonify({'error': 'Backup not found'}), 404

    return jsonify(backup.to_dict()), 200


@backup_bp.route('/history', methods=['GET'])
@token_required
def get_backup_history(current_user):
    """Get backup history"""
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)

    total = Backup.query.count()
    backups = Backup.query.order_by(Backup.started_at.desc()).limit(limit).offset(offset).all()

    return jsonify({
        'total': total,
        'limit': limit,
        'offset': offset,
        'backups': [backup.to_dict() for backup in backups]
    }), 200


@backup_bp.route('/<backup_id>/stop', methods=['POST'])
@token_required
def stop_backup(current_user, backup_id):
    """Stop a running backup gracefully"""
    backup = Backup.query.filter_by(backup_id=backup_id).first()

    if not backup:
        return jsonify({'error': 'Backup not found'}), 404

    if backup.status not in ['pending', 'running']:
        return jsonify({'error': 'Backup is not running'}), 400

    # Request the executor to stop gracefully
    stopped = BackupExecutor.stop_backup(backup_id)

    if stopped:
        return jsonify({
            'message': 'Backup stop requested (will complete current source)',
            'backup_id': backup_id
        }), 200
    else:
        # Backup already finished or not found, update status directly
        backup.status = 'cancelled'
        backup.completed_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': 'Backup stopped',
            'backup_id': backup_id
        }), 200


@backup_bp.route('/stats', methods=['GET'])
@token_required
def get_stats(current_user):
    """Get backup statistics"""
    total_backups = Backup.query.count()
    successful = Backup.query.filter_by(status='completed').count()
    failed = Backup.query.filter_by(status='failed').count()
    running = Backup.query.filter_by(status='running').count()

    # Last backup
    last_backup = Backup.query.order_by(Backup.started_at.desc()).first()

    # Total size
    total_size = db.session.query(db.func.sum(Backup.total_size)).scalar() or 0

    return jsonify({
        'total_backups': total_backups,
        'successful': successful,
        'failed': failed,
        'running': running,
        'total_size_bytes': total_size,
        'last_backup': last_backup.to_dict() if last_backup else None
    }), 200


@backup_bp.route('/all', methods=['DELETE'])
@token_required
def delete_all_backups(current_user):
    """Delete all backup records (DANGEROUS - requires confirmation)"""
    # Require explicit confirmation parameter
    confirm = request.args.get('confirm', '').lower() == 'true'

    if not confirm:
        return jsonify({
            'error': 'Confirmation required',
            'message': 'Add ?confirm=true to delete all backups'
        }), 400

    try:
        # Delete all backup source results first (foreign key constraint)
        source_results_count = BackupSourceResult.query.delete()

        # Delete all backups
        backups_count = Backup.query.delete()

        db.session.commit()

        return jsonify({
            'message': f'Deleted {backups_count} backups and {source_results_count} source results',
            'backups_deleted': backups_count,
            'source_results_deleted': source_results_count
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete backups: {str(e)}'}), 500
