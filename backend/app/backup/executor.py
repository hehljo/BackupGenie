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
from app.backup.sources.git import (
    GitLabBackup, GiteaBackup, ForgejoBackup,
    BitbucketBackup, CodebergBackup
)
from app.backup.sources.database import (
    MySQLBackup, PostgreSQLBackup, MongoDBBackup,
    RedisBackup, SQLiteBackup, CouchDBBackup, InfluxDBBackup
)
from app.backup.sources.ftp import FTPBackup, SFTPBackup
from app.backup.sources.webdav import WebDAVBackup
from app.backup.sources.docker import DockerVolumeBackup, DockerImageBackup
from app.backup.sources.rsync_ssh import RsyncSSHBackup, NASBackup
from app.backup.sources.selfhosted import SelfHostedBackup
from app.backup.sources.proxmox import ProxmoxBackup
from app.backup.sources.supabase import SupabaseBackup
from app.notifications.manager import NotificationManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BackupExecutor:
    """Executes backup operations"""

    # Class-level dictionary to track running backups
    _running_backups = {}

    def __init__(self, backup_id, enable_notifications=True):
        self.backup_id = backup_id
        self.backup_base_path = Config.BACKUP_BASE_PATH
        self.enable_notifications = enable_notifications
        self.notification_manager = NotificationManager() if enable_notifications else None
        self.stop_requested = False

        # Source type handlers
        self.handlers = {
            # Network Storage
            'smb': SMBBackup,
            'nfs': SMBBackup,  # NFS uses similar approach
            'local': LocalBackup,

            # Git Platforms
            'github': GitHubBackup,
            'gitlab': GitLabBackup,
            'gitea': GiteaBackup,
            'forgejo': ForgejoBackup,
            'bitbucket': BitbucketBackup,
            'codeberg': CodebergBackup,
            'gitbucket': GiteaBackup,  # GitBucket uses similar API to Gitea

            # Cloud Storage
            'rclone': RcloneBackup,
            'webdav': WebDAVBackup,

            # Databases
            'mysql': MySQLBackup,
            'mariadb': MySQLBackup,  # MariaDB uses MySQL handler
            'postgresql': PostgreSQLBackup,
            'postgres': PostgreSQLBackup,  # Alias
            'mongodb': MongoDBBackup,
            'mongo': MongoDBBackup,  # Alias
            'redis': RedisBackup,
            'sqlite': SQLiteBackup,
            'couchdb': CouchDBBackup,
            'influxdb': InfluxDBBackup,

            # FTP/SFTP
            'ftp': FTPBackup,
            'ftps': FTPBackup,
            'sftp': SFTPBackup,

            # Docker
            'docker-volume': DockerVolumeBackup,
            'docker-image': DockerImageBackup,

            # Rsync/NAS
            'rsync-ssh': RsyncSSHBackup,
            'rsync': RsyncSSHBackup,  # Alias
            'nas': NASBackup,

            # Proxmox VE
            'proxmox': ProxmoxBackup,
            'proxmox-ve': ProxmoxBackup,  # Alias

            # Self-Hosted Services - Media Servers
            'plex': SelfHostedBackup,
            'jellyfin': SelfHostedBackup,
            'immich': SelfHostedBackup,
            'photoprism': SelfHostedBackup,
            'komga': SelfHostedBackup,
            'kaleidescape': SelfHostedBackup,
            'musicbrainz': SelfHostedBackup,

            # Self-Hosted Services - File Storage
            'seafile': SelfHostedBackup,

            # Self-Hosted Services - Smart Home & Automation
            'homeassistant': SelfHostedBackup,
            'grafana': SelfHostedBackup,
            'nodered': SelfHostedBackup,
            'prometheus': SelfHostedBackup,
            'loki': SelfHostedBackup,

            # Self-Hosted Services - Security & Password Management
            'vaultwarden': SelfHostedBackup,
            'bitwarden': SelfHostedBackup,

            # Self-Hosted Services - Documentation & Wiki
            'mediawiki': SelfHostedBackup,
            'tiddlywiki': SelfHostedBackup,
            'obsidian': SelfHostedBackup,

            # Self-Hosted Services - Monitoring & Analytics
            'sentry': SelfHostedBackup,

            # Self-Hosted Services - Email & Communication
            'mailcow': SelfHostedBackup,
            'mastodon': SelfHostedBackup,
            'mattermost': SelfHostedBackup,

            # Self-Hosted Services - Content Management
            'paperless-ngx': SelfHostedBackup,
            'archivebox': SelfHostedBackup,
            'wallabag': SelfHostedBackup,
            'linkding': SelfHostedBackup,

            # Self-Hosted Services - Admin & User Management
            'portainer': SelfHostedBackup,
            'yacht': SelfHostedBackup,

            # Self-Hosted Services - Specialized
            'syncthing': SelfHostedBackup,
            'restic': SelfHostedBackup,

            # Cloud Platforms
            'supabase': SupabaseBackup,
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

    @classmethod
    def stop_backup(cls, backup_id):
        """Request a backup to stop"""
        executor = cls._running_backups.get(backup_id)
        if executor:
            executor.stop_requested = True
            logger.info(f"Stop requested for backup {backup_id}")
            return True
        return False

    def execute(self, source_ids=None, parallel=2):
        """Execute backup for specified sources"""
        from app import create_app
        app = create_app()

        with app.app_context():
            backup = Backup.query.filter_by(backup_id=self.backup_id).first()
            if not backup:
                logger.error(f"Backup {self.backup_id} not found")
                return

            # Register this executor
            BackupExecutor._running_backups[self.backup_id] = self

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

            # Send notification: Backup started
            if self.notification_manager:
                try:
                    self.notification_manager.notify_backup_started(self.backup_id, len(sources_to_backup))
                except Exception as e:
                    logger.error(f"Failed to send backup started notification: {e}")

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
                            # Check if stop was requested
                            if self.stop_requested:
                                logger.info(f"Backup {self.backup_id} stop requested, cancelling...")
                                executor.shutdown(wait=False, cancel_futures=True)
                                break

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
                        # Check if stop was requested
                        if self.stop_requested:
                            logger.info(f"Backup {self.backup_id} stop requested, stopping...")
                            break

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

                # Set status based on stop request or completion
                if self.stop_requested:
                    backup.status = 'cancelled'
                    logger.info(f"Backup {self.backup_id} cancelled by user")
                else:
                    backup.status = 'completed' if failed_count == 0 else 'partial'
                    logger.info(f"Backup {self.backup_id} completed")

                db.session.commit()

                # Send notification: Backup completed, partial, or cancelled
                if self.notification_manager and not self.stop_requested:
                    try:
                        if failed_count == 0:
                            self.notification_manager.notify_backup_completed(
                                self.backup_id,
                                backup.duration,
                                total_size,
                                len(sources_to_backup)
                            )
                        else:
                            # Get failed source names
                            failed_sources = []
                            for result in BackupSourceResult.query.filter_by(backup_id=backup.id, status='failed').all():
                                failed_sources.append(result.source_name)

                            self.notification_manager.notify_backup_partial(
                                self.backup_id,
                                failed_sources,
                                len(sources_to_backup)
                            )
                    except Exception as e:
                        logger.error(f"Failed to send backup completion notification: {e}")

            except Exception as e:
                logger.error(f"Backup {self.backup_id} failed: {e}")
                backup.status = 'failed'
                backup.error_message = str(e)
                backup.completed_at = datetime.utcnow()
                db.session.commit()

                # Send notification: Backup failed
                if self.notification_manager:
                    try:
                        self.notification_manager.notify_backup_failed(self.backup_id, str(e))
                    except Exception as ne:
                        logger.error(f"Failed to send backup failure notification: {ne}")

            finally:
                # Unregister this executor
                BackupExecutor._running_backups.pop(self.backup_id, None)

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
