"""
FTP/SFTP Backup Handler
Supports: FTP, FTPS, SFTP
"""
import subprocess
import logging
import os
from app.backup.base import BackupHandler

logger = logging.getLogger(__name__)


class FTPBackup(BackupHandler):
    """FTP/FTPS backup handler using lftp"""

    def backup(self):
        """Execute FTP backup using lftp mirror"""
        host = self.source_config.get('host', 'localhost')
        port = self.source_config.get('port', 21)
        credentials = self.source_config.get('credentials', {})
        remote_path = self.source_config.get('path', '/')

        # Get credentials
        username = self._get_env_credential(credentials.get('username_env', 'FTP_USER'))
        password = self._get_env_credential(credentials.get('password_env', 'FTP_PASSWORD'))

        # Check if FTPS is enabled
        use_ftps = self.source_config.get('ftps', False)
        protocol = 'ftps' if use_ftps else 'ftp'

        try:
            self.log(f"Starting FTP backup from {protocol}://{host}:{port}{remote_path}")

            # Build lftp command
            options = self.source_config.get('options', {})

            lftp_commands = [
                f"open {protocol}://{username}:{password}@{host}:{port}",
                f"mirror --verbose --parallel={options.get('parallel', 2)}"
            ]

            if options.get('delete', False):
                lftp_commands[1] += " --delete"

            if options.get('only_newer', True):
                lftp_commands[1] += " --only-newer"

            lftp_commands[1] += f" {remote_path} {self.dest_path}"
            lftp_commands.append("bye")

            # Execute lftp
            lftp_script = '; '.join(lftp_commands)

            result = subprocess.run(
                ['lftp', '-c', lftp_script],
                capture_output=True,
                text=True,
                timeout=3600
            )

            if result.stdout:
                self.log(result.stdout)

            if result.returncode != 0 and result.stderr:
                self.log(f"WARNING: {result.stderr}")

            # Calculate backup size
            size = self._get_directory_size(self.dest_path)
            files = sum(1 for _, _, files in os.walk(self.dest_path) for _ in files)

            self.log(f"FTP backup completed: {files} files, {size} bytes")

            return {
                'files_synced': files,
                'size_synced': size,
                'logs': self.get_logs()
            }

        except subprocess.TimeoutExpired:
            self.log("ERROR: FTP backup timeout")
            raise Exception("FTP backup timeout")
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            raise


class SFTPBackup(BackupHandler):
    """SFTP backup handler using rsync over SSH"""

    def backup(self):
        """Execute SFTP backup using rsync"""
        host = self.source_config.get('host', 'localhost')
        port = self.source_config.get('port', 22)
        credentials = self.source_config.get('credentials', {})
        remote_path = self.source_config.get('path', '/')

        # Get credentials
        username = self._get_env_credential(credentials.get('username_env', 'SFTP_USER'))

        # Check for SSH key or password
        ssh_key = credentials.get('ssh_key_path', '')
        password_env = credentials.get('password_env', '')

        try:
            self.log(f"Starting SFTP backup from {username}@{host}:{port}{remote_path}")

            # Build rsync command with SSH
            cmd = ['rsync', '-avz', '--stats']

            options = self.source_config.get('options', {})

            if options.get('delete', False):
                cmd.append('--delete')

            if options.get('compress', True):
                cmd.append('--compress')

            # SSH options
            ssh_opts = f"-p {port}"
            if ssh_key and os.path.exists(ssh_key):
                ssh_opts += f" -i {ssh_key}"
                self.log(f"Using SSH key: {ssh_key}")
            elif password_env:
                # Use sshpass for password authentication
                password = self._get_env_credential(password_env)
                cmd = ['sshpass', f'-p{password}'] + cmd

            cmd.extend(['-e', f'ssh {ssh_opts}'])

            # Add source and destination
            source = f"{username}@{host}:{remote_path}"
            cmd.extend([source, self.dest_path])

            # Execute rsync
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600
            )

            if result.stdout:
                self.log(result.stdout)

            if result.returncode != 0:
                raise Exception(f"rsync failed: {result.stderr}")

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

            self.log(f"SFTP backup completed: {files_synced} files, {size_synced} bytes")

            return {
                'files_synced': files_synced,
                'size_synced': size_synced,
                'logs': self.get_logs()
            }

        except subprocess.TimeoutExpired:
            self.log("ERROR: SFTP backup timeout")
            raise Exception("SFTP backup timeout")
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            raise
