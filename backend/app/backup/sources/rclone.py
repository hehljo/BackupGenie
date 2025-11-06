"""
Rclone Backup Handler
Handles cloud storage backups using rclone
"""
import subprocess
import logging
import os

logger = logging.getLogger(__name__)


class RcloneBackup:
    """Handles cloud storage backups using rclone"""

    def __init__(self, source_config, dest_path):
        self.source_config = source_config
        self.dest_path = dest_path

    def backup(self):
        """Execute rclone backup"""
        logs = []

        remote = self.source_config.get('remote')
        remote_path = self.source_config.get('path', '/')
        options = self.source_config.get('options', {})

        if not remote:
            raise Exception("Remote not specified for rclone source")

        # Build rclone command
        cmd = [
            'rclone', 'sync',
            f"{remote}:{remote_path}",
            self.dest_path,
            '--verbose',
            '--stats', '1s'
        ]

        # Add options
        if options.get('transfers'):
            cmd.extend(['--transfers', str(options['transfers'])])

        if options.get('checkers'):
            cmd.extend(['--checkers', str(options['checkers'])])

        logs.append(f"Running: {' '.join(cmd)}")
        logger.info(f"Running rclone: {' '.join(cmd)}")

        # Execute rclone
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env={**os.environ, 'RCLONE_CONFIG': '/app/config/rclone.conf'}
        )

        logs.append(result.stdout)
        if result.stderr:
            logs.append(result.stderr)

        if result.returncode != 0:
            raise Exception(f"Rclone failed with code {result.returncode}")

        # Parse stats
        files_synced = 0
        size_synced = 0

        for line in result.stdout.split('\n'):
            if 'Transferred:' in line and 'Bytes' in line:
                try:
                    parts = line.split(',')
                    for part in parts:
                        if 'Bytes' in part:
                            size_str = part.split(':')[1].strip().split()[0].replace(',', '')
                            size_synced = int(size_str)
                except:
                    pass
            if 'Checks:' in line or 'Transferred:' in line:
                try:
                    count = int(line.split(':')[1].strip().split()[0])
                    files_synced += count
                except:
                    pass

        return {
            'files_synced': files_synced,
            'size_synced': size_synced,
            'logs': '\n'.join(logs)
        }
