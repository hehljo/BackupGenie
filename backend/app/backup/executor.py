"""
Backup Executor
Coordinates backup operations across multiple sources
"""
import json
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

from app import db
from app.models.backup import Backup, BackupSourceResult
from app.config import Config
from app.backup.sources.smb import SMBBackup
from app.backup.sources.github import GitHubBackup
from app.backup.sources.rclone import RcloneBackup
from app.backup.sources.local import LocalBackup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BackupExecutor:
    """Executes backup operations"""

    def __init__(self, backup_id):
        self.backup_id = backup_id
        self.backup_base_path = Config.BACKUP_BASE_PATH

        # Source type handlers
        self.handlers = {
            'smb': SMBBackup,
            'nfs': SMBBackup,  # NFS uses similar approach
            'github': GitHubBackup,
            'rclone': RcloneBackup,
            'local': LocalBackup
        }

    def load_sources(self):
        """Load backup sources from configuration"""
        try:
            with open(Config.SOURCES_CONFIG_PATH, 'r') as f:
                config = json.load(f)
                return config.get('backup_sources', [])
        except FileNotFoundError:
            logger.error(f"Sources config not found: {Config.SOURCES_CONFIG_PATH}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in sources config: {e}")
            return []

    def execute(self, source_ids=None, parallel=2):
        """Execute backup for specified sources"""
        from app import create_app
        app = create_app()

        with app.app_context():
            backup = Backup.query.filter_by(backup_id=self.backup_id).first()
            if not backup:
                logger.error(f"Backup {self.backup_id} not found")
                return

            # Update status
            backup.status = 'running'
            db.session.commit()

            # Load sources
            all_sources = self.load_sources()

            # Filter enabled sources
            sources_to_backup = [s for s in all_sources if s.get('enabled', True)]

            # Filter by source_ids if provided
            if source_ids:
                sources_to_backup = [s for s in sources_to_backup if s.get('id') in source_ids]

            # Sort by priority
            sources_to_backup.sort(key=lambda x: x.get('priority', 999))

            backup.sources_count = len(sources_to_backup)
            db.session.commit()

            logger.info(f"Starting backup {self.backup_id} with {len(sources_to_backup)} sources")

            # Execute backups
            total_size = 0
            failed_count = 0

            try:
                if parallel > 1:
                    # Parallel execution
                    with ThreadPoolExecutor(max_workers=parallel) as executor:
                        futures = {
                            executor.submit(self._backup_source, source): source
                            for source in sources_to_backup
                        }

                        for future in as_completed(futures):
                            source = futures[future]
                            try:
                                result = future.result()
                                if result:
                                    total_size += result.get('size_synced', 0)
                                    if result.get('status') == 'failed':
                                        failed_count += 1
                            except Exception as e:
                                logger.error(f"Error backing up {source.get('id')}: {e}")
                                failed_count += 1
                else:
                    # Sequential execution
                    for source in sources_to_backup:
                        try:
                            result = self._backup_source(source)
                            if result:
                                total_size += result.get('size_synced', 0)
                                if result.get('status') == 'failed':
                                    failed_count += 1
                        except Exception as e:
                            logger.error(f"Error backing up {source.get('id')}: {e}")
                            failed_count += 1

                # Update backup status
                backup.completed_at = datetime.utcnow()
                backup.duration = int((backup.completed_at - backup.started_at).total_seconds())
                backup.total_size = total_size
                backup.status = 'completed' if failed_count == 0 else 'partial'
                db.session.commit()

                logger.info(f"Backup {self.backup_id} completed")

            except Exception as e:
                logger.error(f"Backup {self.backup_id} failed: {e}")
                backup.status = 'failed'
                backup.error_message = str(e)
                backup.completed_at = datetime.utcnow()
                db.session.commit()

    def _backup_source(self, source):
        """Backup a single source"""
        from app import create_app
        app = create_app()

        with app.app_context():
            source_id = source.get('id')
            source_type = source.get('type')

            logger.info(f"Backing up source: {source_id} ({source_type})")

            # Create source result record
            result = BackupSourceResult(
                backup_id=Backup.query.filter_by(backup_id=self.backup_id).first().id,
                source_id=source_id,
                source_name=source.get('name', source_id),
                source_type=source_type,
                status='running'
            )
            db.session.add(result)
            db.session.commit()

            try:
                # Get handler for source type
                handler_class = self.handlers.get(source_type)
                if not handler_class:
                    raise ValueError(f"Unsupported source type: {source_type}")

                # Create destination path
                dest_path = os.path.join(self.backup_base_path, source_id)
                os.makedirs(dest_path, exist_ok=True)

                # Execute backup
                handler = handler_class(source, dest_path)
                backup_result = handler.backup()

                # Update result
                result.status = 'completed'
                result.completed_at = datetime.utcnow()
                result.duration = int((result.completed_at - result.started_at).total_seconds())
                result.files_synced = backup_result.get('files_synced', 0)
                result.size_synced = backup_result.get('size_synced', 0)
                result.progress = 100
                result.logs = backup_result.get('logs', '')

                db.session.commit()

                logger.info(f"Source {source_id} backed up successfully")

                return {
                    'status': 'completed',
                    'size_synced': result.size_synced
                }

            except Exception as e:
                logger.error(f"Error backing up source {source_id}: {e}")
                result.status = 'failed'
                result.error_message = str(e)
                result.completed_at = datetime.utcnow()
                result.duration = int((result.completed_at - result.started_at).total_seconds())
                db.session.commit()

                return {
                    'status': 'failed',
                    'size_synced': 0
                }
