"""
Rclone Backup Handler
Best Practice 02/2026: Explicit config, retries, bandwidth control,
extends BackupHandler for consistent logging and utilities
"""
import subprocess
import logging
import os
import re
from app.backup.base import BackupHandler
from app.config import Config

logger = logging.getLogger(__name__)


class RcloneBackup(BackupHandler):
    """Handles cloud storage backups using rclone"""

    def backup(self):
        """Execute rclone backup"""
        remote = self.source_config.get('remote')
        remote_path = self.source_config.get('path', '/')
        options = self.source_config.get('options', {})

        if not remote:
            raise Exception("Remote not specified for rclone source")

        # Build rclone command with explicit config path
        cmd = [
            'rclone', 'sync',
            f"{remote}:{remote_path}",
            self.dest_path,
            '--config', Config.RCLONE_CONFIG_PATH,
            '--verbose',
            '--stats', '10s',
            '--retries', '3',
            '--low-level-retries', '10',
            '--stats-one-line',
            '--log-level', 'INFO',
        ]

        # Add transfers/checkers options
        if options.get('transfers'):
            cmd.extend(['--transfers', str(options['transfers'])])

        if options.get('checkers'):
            cmd.extend(['--checkers', str(options['checkers'])])

        # Bandwidth limiting
        if options.get('bwlimit'):
            cmd.extend(['--bwlimit', str(options['bwlimit'])])

        # Exclude patterns
        for exclude in options.get('exclude', []):
            cmd.extend(['--exclude', exclude])

        # Timeout for stalled transfers
        cmd.extend(['--timeout', str(options.get('timeout', '5m'))])

        self.log(f"Running: {' '.join(cmd)}")

        # Execute rclone
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=options.get('max_duration', 7200)
        )

        if result.stdout:
            self.log(result.stdout)
        if result.stderr:
            self.log(result.stderr)

        if result.returncode != 0:
            raise Exception(f"Rclone failed with code {result.returncode}: {result.stderr[:500]}")

        # Parse stats from output
        files_synced = 0
        size_synced = 0

        output = result.stdout + '\n' + result.stderr
        for line in output.split('\n'):
            # Match "Transferred: X / Y Bytes, ..." format
            transferred_match = re.search(r'Transferred:\s+(\d+)\s*/\s*(\d+)\s*Bytes', line)
            if transferred_match:
                size_synced = int(transferred_match.group(1))

            # Match "Transferred: X" (file count)
            files_match = re.search(r'Transferred:\s+(\d+)\s*$', line)
            if files_match:
                files_synced = int(files_match.group(1))

            # Also try "Checks:" line
            checks_match = re.search(r'Checks:\s+(\d+)', line)
            if checks_match:
                files_synced = max(files_synced, int(checks_match.group(1)))

        return {
            'files_synced': files_synced,
            'size_synced': size_synced,
            'logs': self.get_logs()
        }
