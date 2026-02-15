"""
SMB/NFS Backup Handler
Best Practice 02/2026: Extends BackupHandler, SMB version auto-detection,
lazy unmount fallback, consistent logging
"""
import subprocess
import logging
import os
from app.backup.base import BackupHandler

logger = logging.getLogger(__name__)


class SMBBackup(BackupHandler):
    """Handles SMB/CIFS and NFS backups using mount and rsync"""

    def __init__(self, source_config, dest_path):
        super().__init__(source_config, dest_path)
        self.mount_point = f"/tmp/mount_{source_config.get('id', 'unknown')}"

    def backup(self):
        """Execute SMB/NFS backup"""
        try:
            # Create mount point
            os.makedirs(self.mount_point, exist_ok=True)
            self.log(f"Created mount point: {self.mount_point}")

            # Mount the share
            if self.source_config.get('type') == 'nfs':
                self._mount_nfs()
            else:
                self._mount_smb()

            self.log(f"Mounted {self.source_config.get('source', 'unknown')}")

            # Sync files using rsync
            result = self._rsync_files()

            # Unmount
            self._unmount()
            self.log("Unmounted successfully")

            return {
                'files_synced': result['files_synced'],
                'size_synced': result['size_synced'],
                'logs': self.get_logs()
            }

        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            # Try to unmount even if backup failed
            try:
                self._unmount()
            except Exception:
                pass
            raise

    def _mount_smb(self):
        """Mount SMB share with protocol version auto-detection"""
        credentials = self.source_config.get('credentials', {})
        username = credentials.get('username', '')
        password = os.environ.get(credentials.get('password_env', ''), '')
        options = self.source_config.get('options', {})

        # Try SMB protocol versions in order: 3.1.1 → 3.0 → 2.1
        smb_versions = options.get('smb_versions', ['3.1.1', '3.0', '2.1'])
        if isinstance(smb_versions, str):
            smb_versions = [smb_versions]

        last_error = None
        for vers in smb_versions:
            cmd = [
                'mount',
                '-t', 'cifs',
                self.source_config['source'],
                self.mount_point,
                '-o', f'username={username},password={password},vers={vers},sec=ntlmssp'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.log(f"SMB mounted with vers={vers}")
                return
            last_error = result.stderr
            self.log(f"SMB mount failed with vers={vers}: {result.stderr.strip()}")

        raise Exception(f"SMB mount failed with all protocol versions: {last_error}")

    def _mount_nfs(self):
        """Mount NFS share"""
        options = self.source_config.get('options', {})
        vers = options.get('vers', 3)
        nolock = ',nolock' if options.get('nolock', False) else ''

        cmd = [
            'mount',
            '-t', 'nfs',
            '-o', f'vers={vers}{nolock}',
            self.source_config['source'],
            self.mount_point
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise Exception(f"NFS mount failed: {result.stderr}")
        self.log(f"NFS mounted with vers={vers}")

    def _rsync_files(self):
        """Sync files using rsync"""
        options = self.source_config.get('options', {})

        # Build rsync command
        cmd = ['rsync', '-av', '--stats']

        if options.get('recursive', True):
            cmd.append('-r')

        if options.get('delete', False):
            cmd.append('--delete')

        # Exclude patterns
        for pattern in options.get('exclude', []):
            cmd.extend(['--exclude', pattern])

        cmd.extend([
            f"{self.mount_point}/",
            self.dest_path
        ])

        self.log(f"Running rsync...")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=options.get('timeout', 3600)
        )

        if result.stdout:
            self.log(result.stdout)
        if result.stderr:
            self.log(result.stderr)

        # Parse rsync stats
        files_synced = 0
        size_synced = 0

        for line in result.stdout.split('\n'):
            if 'Number of files' in line:
                try:
                    files_synced = int(line.split(':')[1].strip().split()[0].replace(',', ''))
                except Exception:
                    pass
            if 'Total file size' in line:
                try:
                    size_str = line.split(':')[1].strip().split()[0].replace(',', '')
                    size_synced = int(size_str)
                except Exception:
                    pass

        return {
            'files_synced': files_synced,
            'size_synced': size_synced,
        }

    def _unmount(self):
        """Unmount the share with lazy fallback"""
        result = subprocess.run(['umount', self.mount_point], capture_output=True)
        if result.returncode != 0:
            # Lazy unmount as fallback for busy mount points
            subprocess.run(['umount', '-l', self.mount_point], capture_output=True)
        try:
            os.rmdir(self.mount_point)
        except Exception:
            pass
