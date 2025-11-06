"""
Rsync over SSH Backup Handler
For NAS systems, remote servers, and SSH-enabled devices
"""
import subprocess
import logging
import os
from app.backup.base import BackupHandler

logger = logging.getLogger(__name__)


class RsyncSSHBackup(BackupHandler):
    """Rsync over SSH backup handler"""

    def backup(self):
        """Execute rsync over SSH backup"""
        host = self.source_config.get('host', '')
        port = self.source_config.get('port', 22)
        remote_path = self.source_config.get('path', '/')
        credentials = self.source_config.get('credentials', {})

        if not host:
            raise Exception("Host is required for rsync over SSH")

        # Get username
        username = self._get_env_credential(credentials.get('username_env', 'SSH_USER'))

        # Check for SSH key
        ssh_key = credentials.get('ssh_key_path', '')
        if ssh_key:
            ssh_key = os.path.expanduser(ssh_key)

        try:
            self.log(f"Starting rsync backup from {username}@{host}:{remote_path}")

            # Build rsync command
            cmd = ['rsync', '-avz', '--stats']

            options = self.source_config.get('options', {})

            if options.get('delete', False):
                cmd.append('--delete')

            if options.get('compress', True):
                cmd.append('--compress')

            if options.get('recursive', True):
                cmd.append('--recursive')

            # Exclude patterns
            excludes = options.get('exclude', [])
            for pattern in excludes:
                cmd.extend(['--exclude', pattern])

            # Include patterns
            includes = options.get('include', [])
            for pattern in includes:
                cmd.extend(['--include', pattern])

            # SSH options
            ssh_opts = ['-p', str(port)]

            if ssh_key and os.path.exists(ssh_key):
                ssh_opts.extend(['-i', ssh_key])
                self.log(f"Using SSH key: {ssh_key}")

            # Strict host key checking
            if not options.get('strict_host_key_checking', True):
                ssh_opts.extend(['-o', 'StrictHostKeyChecking=no'])
                ssh_opts.extend(['-o', 'UserKnownHostsFile=/dev/null'])

            # Add SSH options to rsync
            ssh_command = 'ssh ' + ' '.join(ssh_opts)
            cmd.extend(['-e', ssh_command])

            # Source and destination
            source = f"{username}@{host}:{remote_path}"
            if not remote_path.endswith('/'):
                source += '/'

            cmd.extend([source, self.dest_path])

            self.log(f"Executing: {' '.join(cmd[:3])} ... (SSH details hidden)")

            # Execute rsync
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=options.get('timeout', 3600)
            )

            if result.stdout:
                self.log(result.stdout)

            if result.returncode != 0:
                raise Exception(f"rsync failed with code {result.returncode}: {result.stderr}")

            # Parse rsync stats
            files_synced = 0
            size_synced = 0

            for line in result.stdout.split('\n'):
                if 'Number of files' in line:
                    try:
                        parts = line.split(':')[1].strip().split()
                        files_synced = int(parts[0].replace(',', ''))
                    except:
                        pass
                elif 'Total file size' in line:
                    try:
                        size_str = line.split(':')[1].strip().split()[0].replace(',', '')
                        size_synced = int(size_str)
                    except:
                        pass
                elif 'Total transferred file size' in line:
                    try:
                        size_str = line.split(':')[1].strip().split()[0].replace(',', '')
                        if size_synced == 0:  # Use transferred size if total not found
                            size_synced = int(size_str)
                    except:
                        pass

            self.log(f"Rsync backup completed: {files_synced} files, {size_synced} bytes")

            return {
                'files_synced': files_synced,
                'size_synced': size_synced,
                'logs': self.get_logs()
            }

        except subprocess.TimeoutExpired:
            self.log("ERROR: Rsync backup timeout")
            raise Exception("Rsync backup timeout")
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            raise


class NASBackup(RsyncSSHBackup):
    """
    Convenience class for NAS backups (Synology, QNAP, TrueNAS, etc.)
    Uses rsync over SSH
    """
    pass
