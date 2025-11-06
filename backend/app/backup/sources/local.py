"""
Local Backup Handler
"""
import subprocess
import logging
import os

logger = logging.getLogger(__name__)


class LocalBackup:
    """Handles local directory backups using rsync"""

    def __init__(self, source_config, dest_path):
        self.source_config = source_config
        self.dest_path = dest_path

    def backup(self):
        """Execute local backup"""
        logs = []
        sources = self.source_config.get('sources', [])

        if not sources:
            raise Exception("No source paths specified for local backup")

        total_files = 0
        total_size = 0

        for source_path in sources:
            try:
                logs.append(f"Backing up: {source_path}")

                # Verify source exists
                if not os.path.exists(source_path):
                    logs.append(f"WARNING: Source path does not exist: {source_path}")
                    continue

                # Create destination subdirectory
                source_name = os.path.basename(source_path.rstrip('/'))
                dest_subpath = os.path.join(self.dest_path, source_name)

                # Build rsync command
                result = self._rsync_path(source_path, dest_subpath)

                logs.extend(result['logs'])
                total_files += result['files_synced']
                total_size += result['size_synced']

            except Exception as e:
                logs.append(f"ERROR backing up {source_path}: {str(e)}")
                logger.error(f"Error backing up {source_path}: {e}")

        return {
            'files_synced': total_files,
            'size_synced': total_size,
            'logs': '\n'.join(logs)
        }

    def _rsync_path(self, source, dest):
        """Rsync a single path"""
        options = self.source_config.get('options', {})

        # Build rsync command
        cmd = ['rsync', '-av', '--stats']

        if options.get('recursive', True):
            cmd.append('-r')

        if options.get('delete', False):
            cmd.append('--delete')

        if not options.get('follow_symlinks', False):
            cmd.append('--no-links')

        # Ensure source ends with / for directory contents
        if os.path.isdir(source) and not source.endswith('/'):
            source += '/'

        cmd.extend([source, dest])

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
