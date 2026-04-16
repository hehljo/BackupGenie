"""
Supabase Restore Handler
Restores a Supabase backup to a target project using psql.
Supports schema, data, and optional storage restore.
"""
import subprocess
import logging
import os
import glob
import json
import shutil
import tarfile
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)


class SupabaseRestore:
    """Restore Supabase backups to a target project"""

    def __init__(self):
        self.logs = []

    def log(self, message):
        """Add log entry"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        entry = f"[{timestamp}] {message}"
        self.logs.append(entry)
        logger.info(message)

    def get_logs(self):
        """Get all log entries as string"""
        return '\n'.join(self.logs)

    def restore(self, backup_path, target_config):
        """
        Restore backup to target Supabase project.

        Args:
            backup_path: Path to backup directory or .tar.gz archive
            target_config: dict with target_connection_string, target_db_password,
                          and optionally target_service_role_key for storage restore
        Returns:
            dict with status, logs
        """
        from urllib.parse import quote, unquote
        import re

        target_conn = target_config.get('target_connection_string', '').strip()
        target_password = target_config.get('target_db_password', '')
        restore_storage = target_config.get('restore_storage', False)
        target_service_key = target_config.get('target_service_role_key', '')

        if not target_conn:
            raise Exception("target_connection_string is required")

        # Decode URL-encoded brackets from Supabase Dashboard
        target_conn = unquote(target_conn)

        # Replace [YOUR-PASSWORD] placeholder
        if '[YOUR-PASSWORD]' in target_conn:
            if not target_password:
                raise Exception("target_db_password required when [YOUR-PASSWORD] placeholder used")
            target_conn = target_conn.replace('[YOUR-PASSWORD]', quote(target_password, safe=''))

        # Extract target ref for storage restore
        match = re.search(r'postgres\.([a-z]+)[:@]', target_conn) or re.search(r'db\.([a-z]+)\.supabase', target_conn)
        target_ref = match.group(1) if match else ''

        # Handle tar.gz archives
        working_dir = backup_path
        temp_extracted = False

        if backup_path.endswith('.tar.gz'):
            self.log("Entpacke Backup-Archiv...")
            extract_dir = backup_path.replace('.tar.gz', '_restore_tmp')
            os.makedirs(extract_dir, exist_ok=True)
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(extract_dir)
            # Find the actual backup dir inside
            subdirs = [d for d in os.listdir(extract_dir)
                       if os.path.isdir(os.path.join(extract_dir, d))]
            if subdirs:
                working_dir = os.path.join(extract_dir, subdirs[0])
            else:
                working_dir = extract_dir
            temp_extracted = True

        total_steps = 0
        completed_steps = 0
        errors = []

        try:
            # 1. Restore Schema
            schema_files = sorted(glob.glob(os.path.join(working_dir, 'schema_*.sql')))
            if schema_files:
                total_steps += 1
                self.log(f"Stelle Schema wieder her: {os.path.basename(schema_files[0])}")
                result = self._run_psql(target_conn, schema_files[0])
                if result['success']:
                    completed_steps += 1
                    self.log("Schema wiederhergestellt ✓")
                else:
                    errors.append(f"Schema: {result['error']}")
                    self.log(f"WARNING: Schema-Restore teilweise fehlgeschlagen: {result['error']}")
                    completed_steps += 1  # Continue anyway

            # 2. Restore Data
            data_files = sorted(glob.glob(os.path.join(working_dir, 'data_*.sql')))
            if data_files:
                total_steps += 1
                self.log(f"Stelle Daten wieder her: {os.path.basename(data_files[0])}")
                result = self._run_psql(target_conn, data_files[0])
                if result['success']:
                    completed_steps += 1
                    self.log("Daten wiederhergestellt ✓")
                else:
                    errors.append(f"Data: {result['error']}")
                    self.log(f"ERROR: Daten-Restore fehlgeschlagen: {result['error']}")

            # 3. Restore Roles (optional, may fail due to permissions)
            roles_files = sorted(glob.glob(os.path.join(working_dir, 'roles_*.sql')))
            if roles_files:
                total_steps += 1
                self.log(f"Stelle Roles wieder her: {os.path.basename(roles_files[0])}")
                result = self._run_psql(target_conn, roles_files[0])
                if result['success']:
                    completed_steps += 1
                    self.log("Roles wiederhergestellt ✓")
                else:
                    self.log(f"WARNING: Roles-Restore übersprungen (normal bei Supabase): {result['error']}")
                    completed_steps += 1  # Don't count as error

            # 4. Restore Auth/Config (optional)
            config_dir = os.path.join(working_dir, 'config')
            if os.path.isdir(config_dir):
                auth_files = sorted(glob.glob(os.path.join(config_dir, 'auth_schema_*.sql')))
                if auth_files:
                    total_steps += 1
                    self.log(f"Stelle Auth-Schema wieder her...")
                    result = self._run_psql(target_conn, auth_files[0])
                    if result['success']:
                        completed_steps += 1
                        self.log("Auth-Schema wiederhergestellt ✓")
                    else:
                        self.log(f"WARNING: Auth-Schema-Restore: {result['error']}")
                        completed_steps += 1

            # 5. Storage Restore (optional)
            storage_dir = os.path.join(working_dir, 'storage')
            if restore_storage and os.path.isdir(storage_dir) and target_service_key:
                total_steps += 1
                self.log("Stelle Storage-Objekte wieder her...")
                try:
                    storage_result = self._restore_storage(
                        storage_dir, target_ref, target_service_key
                    )
                    completed_steps += 1
                    self.log(f"Storage wiederhergestellt: {storage_result['files']} Dateien ✓")
                except Exception as e:
                    errors.append(f"Storage: {str(e)}")
                    self.log(f"ERROR: Storage-Restore fehlgeschlagen: {e}")

            status = 'completed' if not errors else 'partial'
            self.log(f"Restore abgeschlossen: {completed_steps}/{total_steps} Schritte, Status: {status}")

            return {
                'status': status,
                'steps_total': total_steps,
                'steps_completed': completed_steps,
                'errors': errors,
                'logs': self.get_logs()
            }

        finally:
            # Cleanup temp extraction
            if temp_extracted and os.path.exists(working_dir):
                parent = os.path.dirname(working_dir)
                if parent.endswith('_restore_tmp'):
                    shutil.rmtree(parent, ignore_errors=True)

    def _run_psql(self, connection_string, sql_file, timeout=3600):
        """Run psql with a SQL file against connection"""
        env = os.environ.copy()
        try:
            result = subprocess.run(
                ['psql', connection_string, '-f', sql_file,
                 '--set', 'ON_ERROR_STOP=off'],
                capture_output=True, text=True, env=env, timeout=timeout
            )

            if result.returncode == 0:
                return {'success': True, 'output': result.stdout}
            else:
                # psql may return non-zero even for warnings
                stderr = result.stderr.strip()
                # Filter out common harmless warnings
                serious_errors = [
                    line for line in stderr.split('\n')
                    if 'ERROR' in line and 'already exists' not in line
                ]
                if serious_errors:
                    return {'success': False, 'error': '\n'.join(serious_errors[:5])}
                return {'success': True, 'output': result.stdout}

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': f'Timeout nach {timeout}s'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _restore_storage(self, storage_dir, target_ref, service_role_key):
        """Upload storage objects to target project"""
        api_url = f"https://{target_ref}.supabase.co"
        headers = {
            'Authorization': f'Bearer {service_role_key}',
            'apikey': service_role_key,
        }

        files_uploaded = 0

        # Iterate buckets
        for bucket_name in os.listdir(storage_dir):
            bucket_path = os.path.join(storage_dir, bucket_name)
            if not os.path.isdir(bucket_path):
                continue

            self.log(f"Upload Bucket: {bucket_name}")

            # Create bucket if needed (ignore if exists)
            meta_file = os.path.join(bucket_path, '_bucket_meta.json')
            if os.path.exists(meta_file):
                with open(meta_file, 'r') as f:
                    bucket_meta = json.load(f)
                self._create_bucket(api_url, headers, bucket_meta)

            # Upload files
            for root, dirs, files in os.walk(bucket_path):
                for filename in files:
                    if filename == '_bucket_meta.json':
                        continue

                    filepath = os.path.join(root, filename)
                    # Calculate relative path within bucket
                    rel_path = os.path.relpath(filepath, bucket_path)

                    try:
                        self._upload_file(
                            api_url, headers, bucket_name, rel_path, filepath
                        )
                        files_uploaded += 1
                    except Exception as e:
                        self.log(f"WARNING: Upload fehlgeschlagen {rel_path}: {e}")

        return {'files': files_uploaded}

    def _create_bucket(self, api_url, headers, bucket_meta):
        """Create a bucket on target (ignore if exists)"""
        body = json.dumps({
            'id': bucket_meta.get('id', ''),
            'name': bucket_meta.get('name', ''),
            'public': bucket_meta.get('public', False),
        }).encode('utf-8')

        req = Request(
            f"{api_url}/storage/v1/bucket",
            data=body,
            headers={**headers, 'Content-Type': 'application/json'},
            method='POST'
        )

        try:
            with urlopen(req, timeout=30) as resp:
                pass  # Created
        except HTTPError as e:
            if e.code == 409:
                pass  # Already exists
            else:
                self.log(f"WARNING: Bucket-Erstellung: {e}")

    def _upload_file(self, api_url, headers, bucket_id, object_path, local_path):
        """Upload a file to Supabase Storage"""
        with open(local_path, 'rb') as f:
            file_data = f.read()

        req = Request(
            f"{api_url}/storage/v1/object/{bucket_id}/{object_path}",
            data=file_data,
            headers={
                **headers,
                'Content-Type': 'application/octet-stream',
                'x-upsert': 'true',
            },
            method='POST'
        )

        with urlopen(req, timeout=120) as resp:
            pass
