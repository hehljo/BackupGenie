"""
Self-Hosted Services Backup Handler
Backs up various self-hosted services like Plex, Jellyfin, Home Assistant, etc.
"""
import subprocess
import logging
import os
import json
import requests
from datetime import datetime
from app.backup.base import BackupHandler

logger = logging.getLogger(__name__)


class SelfHostedBackup(BackupHandler):
    """Generic self-hosted service backup handler"""

    def backup(self):
        """Execute self-hosted service backup"""
        service_type = self.source_config.get('type', 'unknown')
        self.log(f"Starting backup for {service_type} service")

        options = self.source_config.get('options', {})
        backup_method = options.get('backup_method', 'docker-volume')

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        total_size = 0
        files_backed_up = 0

        try:
            # Determine backup method
            if backup_method == 'docker-volume':
                result = self._backup_docker_volumes(timestamp)
            elif backup_method in ['api', 'snapshot_api', 'json_export', 'xml_api']:
                result = self._backup_via_api(timestamp)
            elif backup_method == 'rsync':
                result = self._backup_via_rsync(timestamp)
            else:
                # Default: try docker volume backup
                result = self._backup_docker_volumes(timestamp)

            # Also backup database if specified
            if options.get('backup_database', False):
                db_result = self._backup_database(timestamp)
                result['files_synced'] += db_result.get('files_synced', 0)
                result['size_synced'] += db_result.get('size_synced', 0)

            self.log(f"{service_type} backup completed: {result['files_synced']} items, {result['size_synced']} bytes")

            return result

        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            raise

    def _backup_docker_volumes(self, timestamp):
        """Backup Docker volumes"""
        self.log("Backing up via Docker volumes")

        service_name = self.source_config.get('id', 'service')
        total_size = 0
        files_backed_up = 0

        # Find volumes for this service
        try:
            # Get all volumes matching service name
            list_cmd = ['docker', 'volume', 'ls', '--format', '{{.Name}}']
            result = subprocess.run(list_cmd, capture_output=True, text=True, check=True)

            volumes = [v for v in result.stdout.strip().split('\n') if service_name in v or self._matches_service(v)]

            if not volumes:
                self.log(f"No Docker volumes found for {service_name}, trying manual volume specification")
                volumes = self.source_config.get('volumes', [])

            for volume in volumes:
                if not volume:
                    continue

                self.log(f"Backing up volume: {volume}")

                backup_file = os.path.join(
                    self.dest_path,
                    f"{volume}_{timestamp}.tar.gz"
                )

                # Use docker run with alpine to tar the volume
                cmd = [
                    'docker', 'run', '--rm',
                    '-v', f'{volume}:/volume:ro',
                    '-v', f'{self.dest_path}:/backup',
                    'alpine',
                    'tar', 'czf',
                    f'/backup/{volume}_{timestamp}.tar.gz',
                    '-C', '/volume', '.'
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=3600
                )

                if result.returncode != 0:
                    self.log(f"WARNING: Volume backup failed for {volume}: {result.stderr}")
                    continue

                size = self._get_file_size(backup_file)
                total_size += size
                files_backed_up += 1

                self.log(f"Volume {volume} backed up: {size} bytes")

        except subprocess.CalledProcessError as e:
            self.log(f"WARNING: Could not list Docker volumes: {e}")
        except Exception as e:
            self.log(f"WARNING: Docker volume backup encountered error: {e}")

        return {
            'files_synced': files_backed_up,
            'size_synced': total_size,
            'logs': self.get_logs()
        }

    def _backup_via_api(self, timestamp):
        """Backup via service API"""
        self.log("Backing up via API")

        host = self.source_config.get('host', 'localhost')
        port = self.source_config.get('port', 80)
        service_type = self.source_config.get('type', 'unknown')

        backup_file = os.path.join(
            self.dest_path,
            f"{service_type}_api_backup_{timestamp}.json"
        )

        try:
            # Get credentials
            credentials = self.source_config.get('credentials', {})
            headers = {}

            if 'token_env' in credentials:
                token = self._get_env_credential(credentials['token_env'], required=False)
                if token:
                    headers['Authorization'] = f'Bearer {token}'
            elif 'api_key_env' in credentials:
                api_key = self._get_env_credential(credentials['api_key_env'], required=False)
                if api_key:
                    headers['X-API-Key'] = api_key

            # Service-specific API endpoints
            data = self._fetch_service_data(host, port, service_type, headers)

            if data:
                with open(backup_file, 'w') as f:
                    json.dump(data, f, indent=2)

                size = self._get_file_size(backup_file)
                self.log(f"API data backed up: {size} bytes")

                return {
                    'files_synced': 1,
                    'size_synced': size,
                    'logs': self.get_logs()
                }

        except Exception as e:
            self.log(f"WARNING: API backup failed: {e}")

        return {
            'files_synced': 0,
            'size_synced': 0,
            'logs': self.get_logs()
        }

    def _backup_via_rsync(self, timestamp):
        """Backup via rsync"""
        self.log("Backing up via rsync")

        options = self.source_config.get('options', {})
        source_path = options.get('vault_path') or options.get('backup_path', '/data')

        try:
            cmd = [
                'rsync', '-avz', '--progress',
                source_path,
                self.dest_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600
            )

            if result.returncode == 0:
                size = self._get_directory_size(self.dest_path)
                self.log(f"Rsync completed: {size} bytes")

                return {
                    'files_synced': 1,
                    'size_synced': size,
                    'logs': self.get_logs()
                }
        except Exception as e:
            self.log(f"WARNING: Rsync backup failed: {e}")

        return {
            'files_synced': 0,
            'size_synced': 0,
            'logs': self.get_logs()
        }

    def _backup_database(self, timestamp):
        """Backup service database"""
        self.log("Backing up database")

        options = self.source_config.get('options', {})
        db_type = options.get('db_type', 'sqlite')
        service_id = self.source_config.get('id', 'service')

        backup_file = os.path.join(
            self.dest_path,
            f"{service_id}_db_{timestamp}.sql"
        )

        try:
            if db_type == 'sqlite':
                # Try to find SQLite database in Docker volume
                return self._backup_docker_volumes(timestamp)
            elif db_type in ['mysql', 'mariadb']:
                return self._backup_mysql_db(backup_file, timestamp)
            elif db_type in ['postgresql', 'postgres']:
                return self._backup_postgres_db(backup_file, timestamp)
        except Exception as e:
            self.log(f"WARNING: Database backup failed: {e}")

        return {
            'files_synced': 0,
            'size_synced': 0
        }

    def _backup_mysql_db(self, backup_file, timestamp):
        """Backup MySQL/MariaDB database"""
        host = self.source_config.get('host', 'localhost')
        credentials = self.source_config.get('credentials', {})

        username = self._get_env_credential(credentials.get('username_env', 'MYSQL_USER'), required=False)
        password = self._get_env_credential(credentials.get('password_env', 'MYSQL_PASSWORD'), required=False)

        if username and password:
            cmd = [
                'mysqldump',
                '-h', host,
                '-u', username,
                f'-p{password}',
                '--all-databases'
            ]

            with open(backup_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                size = self._get_file_size(backup_file)
                self.log(f"MySQL database backed up: {size} bytes")
                return {'files_synced': 1, 'size_synced': size}

        return {'files_synced': 0, 'size_synced': 0}

    def _backup_postgres_db(self, backup_file, timestamp):
        """Backup PostgreSQL database"""
        host = self.source_config.get('host', 'localhost')
        credentials = self.source_config.get('credentials', {})

        username = self._get_env_credential(credentials.get('username_env', 'POSTGRES_USER'), required=False)
        password = self._get_env_credential(credentials.get('password_env', 'POSTGRES_PASSWORD'), required=False)

        if username:
            env = os.environ.copy()
            if password:
                env['PGPASSWORD'] = password

            cmd = [
                'pg_dumpall',
                '-h', host,
                '-U', username
            ]

            with open(backup_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True, env=env)

            if result.returncode == 0:
                size = self._get_file_size(backup_file)
                self.log(f"PostgreSQL database backed up: {size} bytes")
                return {'files_synced': 1, 'size_synced': size}

        return {'files_synced': 0, 'size_synced': 0}

    def _fetch_service_data(self, host, port, service_type, headers):
        """Fetch data from service-specific API endpoints"""
        base_url = f"http://{host}:{port}"

        try:
            # Service-specific API endpoints
            if service_type == 'homeassistant':
                return self._fetch_homeassistant_data(base_url, headers)
            elif service_type == 'grafana':
                return self._fetch_grafana_data(base_url, headers)
            elif service_type == 'portainer':
                return self._fetch_portainer_data(base_url, headers)
            elif service_type == 'syncthing':
                return self._fetch_syncthing_data(base_url, headers)
            elif service_type == 'nodered':
                return self._fetch_nodered_data(base_url, headers)
            else:
                self.log(f"No specific API implementation for {service_type}")
                return {}
        except Exception as e:
            self.log(f"WARNING: Failed to fetch data from {service_type} API: {e}")
            return {}

    def _fetch_homeassistant_data(self, base_url, headers):
        """Fetch Home Assistant data"""
        data = {}
        try:
            # Get config
            response = requests.get(f"{base_url}/api/config", headers=headers, timeout=30)
            if response.status_code == 200:
                data['config'] = response.json()

            # Get states
            response = requests.get(f"{base_url}/api/states", headers=headers, timeout=30)
            if response.status_code == 200:
                data['states'] = response.json()

            self.log("Home Assistant data fetched successfully")
        except Exception as e:
            self.log(f"WARNING: Failed to fetch Home Assistant data: {e}")

        return data

    def _fetch_grafana_data(self, base_url, headers):
        """Fetch Grafana dashboards"""
        data = {}
        try:
            # Get all dashboards
            response = requests.get(f"{base_url}/api/search", headers=headers, timeout=30)
            if response.status_code == 200:
                dashboards = response.json()
                data['dashboards'] = []

                for dashboard in dashboards:
                    if dashboard['type'] == 'dash-db':
                        uid = dashboard['uid']
                        dash_response = requests.get(
                            f"{base_url}/api/dashboards/uid/{uid}",
                            headers=headers,
                            timeout=30
                        )
                        if dash_response.status_code == 200:
                            data['dashboards'].append(dash_response.json())

                self.log(f"Grafana: {len(data['dashboards'])} dashboards fetched")
        except Exception as e:
            self.log(f"WARNING: Failed to fetch Grafana data: {e}")

        return data

    def _fetch_portainer_data(self, base_url, headers):
        """Fetch Portainer configuration"""
        data = {}
        try:
            # Get stacks
            response = requests.get(f"{base_url}/api/stacks", headers=headers, timeout=30)
            if response.status_code == 200:
                data['stacks'] = response.json()
                self.log("Portainer data fetched successfully")
        except Exception as e:
            self.log(f"WARNING: Failed to fetch Portainer data: {e}")

        return data

    def _fetch_syncthing_data(self, base_url, headers):
        """Fetch Syncthing configuration"""
        data = {}
        try:
            # Get config
            response = requests.get(f"{base_url}/rest/system/config", headers=headers, timeout=30)
            if response.status_code == 200:
                data['config'] = response.json()
                self.log("Syncthing config fetched successfully")
        except Exception as e:
            self.log(f"WARNING: Failed to fetch Syncthing data: {e}")

        return data

    def _fetch_nodered_data(self, base_url, headers):
        """Fetch Node-RED flows"""
        data = {}
        try:
            # Get flows
            auth = None
            credentials = self.source_config.get('credentials', {})
            if 'username_env' in credentials and 'password_env' in credentials:
                username = self._get_env_credential(credentials['username_env'], required=False)
                password = self._get_env_credential(credentials['password_env'], required=False)
                if username and password:
                    auth = (username, password)

            response = requests.get(f"{base_url}/flows", auth=auth, timeout=30)
            if response.status_code == 200:
                data['flows'] = response.json()
                self.log("Node-RED flows fetched successfully")
        except Exception as e:
            self.log(f"WARNING: Failed to fetch Node-RED data: {e}")

        return data

    def _matches_service(self, volume_name):
        """Check if volume name matches the service"""
        service_type = self.source_config.get('type', '').lower()
        service_id = self.source_config.get('id', '').lower()
        volume_lower = volume_name.lower()

        return service_type in volume_lower or service_id in volume_lower
