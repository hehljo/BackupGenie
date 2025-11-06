"""
SMB/NFS Backup Handler
"""
import subprocess
import logging
import os

logger = logging.getLogger(__name__)


class SMBBackup:
    """Handles SMB/CIFS and NFS backups using mount and rsync"""

    def __init__(self, source_config, dest_path):
        self.source_config = source_config
        self.dest_path = dest_path
        self.mount_point = f"/tmp/mount_{source_config['id']}"

    def backup(self):
        """Execute SMB/NFS backup"""
        logs = []

        try:
            # Create mount point
            os.makedirs(self.mount_point, exist_ok=True)
            logs.append(f"Created mount point: {self.mount_point}")

            # Mount the share
            if self.source_config['type'] == 'smb':
                self._mount_smb()
            else:
                self._mount_nfs()

            logs.append(f"Mounted {self.source_config['source']}")

            # Sync files using rsync
            result = self._rsync_files()
            logs.extend(result['logs'])

            # Unmount
            self._unmount()
            logs.append("Unmounted successfully")

            return {
                'files_synced': result['files_synced'],
                'size_synced': result['size_synced'],
                'logs': '\n'.join(logs)
            }

        except Exception as e:
            logs.append(f"ERROR: {str(e)}")
            # Try to unmount even if backup failed
            try:
                self._unmount()
            except:
                pass
            raise Exception('\n'.join(logs))

    def _mount_smb(self):
        """Mount SMB share"""
        credentials = self.source_config.get('credentials', {})
        username = credentials.get('username', '')
        password = os.environ.get(credentials.get('password_env', ''), '')

        # Build mount command
        cmd = [
            'mount',
            '-t', 'cifs',
            self.source_config['source'],
            self.mount_point,
            '-o', f'username={username},password={password},vers=3.0'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Mount failed: {result.stderr}")

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

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Mount failed: {result.stderr}")

    def _rsync_files(self):
        """Sync files using rsync"""
        options = self.source_config.get('options', {})

        # Build rsync command
        cmd = ['rsync', '-av', '--stats']

        if options.get('recursive', True):
            cmd.append('-r')

        if options.get('delete', False):
            cmd.append('--delete')

        cmd.extend([
            f"{self.mount_point}/",
            self.dest_path
        ])

        logger.info(f"Running rsync: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Parse rsync stats
        files_synced = 0
        size_synced = 0

        for line in result.stdout.split('\n'):
            if 'Number of files' in line:
                try:
                    files_synced = int(line.split(':')[1].strip().split()[0].replace(',', ''))
                except:
                    pass
            if 'Total file size' in line:
                try:
                    size_str = line.split(':')[1].strip().split()[0].replace(',', '')
                    size_synced = int(size_str)
                except:
                    pass

        return {
            'files_synced': files_synced,
            'size_synced': size_synced,
            'logs': [result.stdout, result.stderr]
        }

    def _unmount(self):
        """Unmount the share"""
        subprocess.run(['umount', self.mount_point], capture_output=True)
        try:
            os.rmdir(self.mount_point)
        except:
            pass
