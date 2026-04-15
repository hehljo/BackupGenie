"""
Supabase Backup Handler
Supports two modes:
- "full": DB (roles, schema, data) + Storage Buckets + Projekt-Config
- "db_only": Only PostgreSQL dump (roles, schema, data)

Uses pg_dump directly for database backups.
Storage objects are downloaded via Supabase Storage API.
"""
import subprocess
import logging
import os
import json
import shutil
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from app.backup.base import BackupHandler

logger = logging.getLogger(__name__)


class SupabaseBackup(BackupHandler):
    """Supabase backup handler with full and db_only modes"""

    def backup(self):
        """Execute Supabase backup"""
        credentials = self.source_config.get('credentials', {})
        backup_mode = self.source_config.get('backup_mode', 'db_only')
        options = self.source_config.get('options', {})

        connection_string = self.source_config.get('connection_string', '')
        if not connection_string:
            raise Exception("Connection String ist erforderlich. Kopiere ihn aus dem Supabase Dashboard.")

        # Replace [YOUR-PASSWORD] placeholder with credential from DB
        db_password = self._get_env_credential(
            credentials.get('db_password_env', 'SUPABASE_DB_PASSWORD')
        )
        if '[YOUR-PASSWORD]' in connection_string:
            connection_string = connection_string.replace('[YOUR-PASSWORD]', db_password)

        # Extract project_ref from connection string for API URL
        project_ref = self._extract_project_ref(connection_string)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(self.dest_path, f"supabase_{timestamp}")
        os.makedirs(backup_dir, exist_ok=True)

        total_size = 0
        files_backed_up = 0

        try:
            # --- Database Backup (always) ---
            db_size, db_files = self._backup_database(
                connection_string, backup_dir, timestamp, options
            )
            total_size += db_size
            files_backed_up += db_files

            # --- Full mode: Storage + Config ---
            if backup_mode == 'full':
                service_role_key = self._get_env_credential(
                    credentials.get('service_role_key_env', 'SUPABASE_SERVICE_ROLE_KEY')
                )
                api_url = f"https://{project_ref}.supabase.co"

                if options.get('include_storage', True):
                    storage_size, storage_files = self._backup_storage(
                        api_url, service_role_key, backup_dir
                    )
                    total_size += storage_size
                    files_backed_up += storage_files

                if options.get('include_auth_config', True):
                    config_size, config_files = self._backup_config(
                        connection_string, backup_dir, timestamp
                    )
                    total_size += config_size
                    files_backed_up += config_files

            # Compress if requested
            if options.get('compress', True):
                self.log("Komprimiere Backup...")
                archive = os.path.join(
                    self.dest_path, f"supabase_{project_ref}_{timestamp}.tar.gz"
                )
                subprocess.run(
                    ['tar', 'czf', archive, '-C', self.dest_path,
                     f"supabase_{timestamp}"],
                    check=True, timeout=600
                )
                shutil.rmtree(backup_dir)
                total_size = self._get_file_size(archive)
                self.log(f"Backup komprimiert: {archive}")

            self.log(
                f"Supabase Backup abgeschlossen: "
                f"{files_backed_up} Dateien, {total_size} Bytes"
            )

            return {
                'files_synced': files_backed_up,
                'size_synced': total_size,
                'logs': self.get_logs()
            }

        except subprocess.TimeoutExpired:
            self.log("ERROR: Supabase Backup Timeout")
            raise Exception("Supabase backup timeout")
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            raise

    def _backup_database(self, connection_string, backup_dir, timestamp, options):
        """
        Backup PostgreSQL database in three parts: roles, schema, data.
        Returns (total_size, file_count).
        """
        total_size = 0
        files = 0
        timeout = options.get('timeout', 3600)

        env = os.environ.copy()

        # 1. Roles dump
        roles_file = os.path.join(backup_dir, f"roles_{timestamp}.sql")
        self.log("Dumping roles...")
        result = subprocess.run(
            ['pg_dumpall', '--dbname', connection_string,
             '--roles-only', '-f', roles_file],
            capture_output=True, text=True, env=env, timeout=timeout
        )
        if result.returncode != 0:
            self.log(f"WARNING: Roles dump returned code {result.returncode}: "
                     f"{result.stderr}")
        else:
            total_size += self._get_file_size(roles_file)
            files += 1
            self.log(f"Roles dump: {roles_file}")

        # 2. Schema dump
        schema_file = os.path.join(backup_dir, f"schema_{timestamp}.sql")
        self.log("Dumping schema...")
        result = subprocess.run(
            ['pg_dump', connection_string,
             '--schema-only', '-f', schema_file],
            capture_output=True, text=True, env=env, timeout=timeout
        )
        if result.returncode != 0:
            raise Exception(f"Schema dump failed: {result.stderr}")
        total_size += self._get_file_size(schema_file)
        files += 1
        self.log(f"Schema dump: {schema_file}")

        # 3. Data dump
        data_file = os.path.join(backup_dir, f"data_{timestamp}.sql")
        self.log("Dumping data (COPY format)...")
        data_cmd = ['pg_dump', connection_string, '--data-only',
                    '-f', data_file]
        result = subprocess.run(
            data_cmd,
            capture_output=True, text=True, env=env, timeout=timeout
        )
        if result.returncode != 0:
            raise Exception(f"Data dump failed: {result.stderr}")
        total_size += self._get_file_size(data_file)
        files += 1
        self.log(f"Data dump: {data_file}")

        return total_size, files

    def _backup_storage(self, api_url, service_role_key, backup_dir):
        """
        Backup all Storage buckets and their objects.
        Returns (total_size, file_count).
        """
        storage_dir = os.path.join(backup_dir, 'storage')
        os.makedirs(storage_dir, exist_ok=True)

        total_size = 0
        files = 0
        headers = {
            'Authorization': f'Bearer {service_role_key}',
            'apikey': service_role_key,
        }

        # List all buckets
        self.log("Listing Storage Buckets...")
        buckets = self._api_get(f"{api_url}/storage/v1/bucket", headers)

        if not buckets:
            self.log("Keine Storage Buckets gefunden.")
            return 0, 0

        for bucket in buckets:
            bucket_id = bucket.get('id', '')
            bucket_name = bucket.get('name', bucket_id)
            self.log(f"Backup Bucket: {bucket_name}")

            bucket_dir = os.path.join(storage_dir, bucket_name)
            os.makedirs(bucket_dir, exist_ok=True)

            # Save bucket metadata
            meta_file = os.path.join(bucket_dir, '_bucket_meta.json')
            with open(meta_file, 'w') as f:
                json.dump(bucket, f, indent=2)

            # List objects in bucket
            objects = self._list_bucket_objects(
                api_url, headers, bucket_id
            )

            for obj in objects:
                obj_name = obj.get('name', '')
                if not obj_name or obj.get('id') is None:
                    continue

                try:
                    obj_path = os.path.join(bucket_dir, obj_name)
                    obj_dir = os.path.dirname(obj_path)
                    os.makedirs(obj_dir, exist_ok=True)

                    # Download object
                    download_url = (
                        f"{api_url}/storage/v1/object/{bucket_id}/{obj_name}"
                    )
                    self._download_file(download_url, headers, obj_path)

                    size = self._get_file_size(obj_path)
                    total_size += size
                    files += 1
                except Exception as e:
                    self.log(f"WARNING: Konnte {obj_name} nicht laden: {e}")

        self.log(f"Storage Backup: {files} Dateien, {total_size} Bytes")
        return total_size, files

    def _list_bucket_objects(self, api_url, headers, bucket_id,
                             prefix='', limit=1000):
        """Recursively list all objects in a bucket."""
        all_objects = []
        offset = 0

        while True:
            body = json.dumps({
                'prefix': prefix,
                'limit': limit,
                'offset': offset,
            }).encode('utf-8')

            req = Request(
                f"{api_url}/storage/v1/object/list/{bucket_id}",
                data=body,
                headers={**headers, 'Content-Type': 'application/json'},
                method='POST'
            )

            try:
                with urlopen(req, timeout=30) as resp:
                    items = json.loads(resp.read().decode('utf-8'))
            except Exception as e:
                self.log(f"WARNING: Bucket-Listing fehlgeschlagen: {e}")
                break

            if not items:
                break

            for item in items:
                if item.get('id') is None:
                    # Folder - recurse
                    folder_prefix = prefix + item.get('name', '') + '/'
                    sub_items = self._list_bucket_objects(
                        api_url, headers, bucket_id, folder_prefix, limit
                    )
                    all_objects.extend(sub_items)
                else:
                    # File
                    item['name'] = prefix + item.get('name', '')
                    all_objects.append(item)

            if len(items) < limit:
                break
            offset += limit

        return all_objects

    def _backup_config(self, connection_string, backup_dir, timestamp):
        """
        Backup RLS policies and auth config via SQL queries.
        Returns (total_size, file_count).
        """
        config_dir = os.path.join(backup_dir, 'config')
        os.makedirs(config_dir, exist_ok=True)

        total_size = 0
        files = 0
        env = os.environ.copy()

        # Dump RLS policies
        rls_file = os.path.join(config_dir, f"rls_policies_{timestamp}.sql")
        rls_query = """
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies
ORDER BY schemaname, tablename, policyname;
"""
        self.log("Exporting RLS Policies...")
        result = subprocess.run(
            ['psql', connection_string, '-c',
             f"\\copy ({rls_query.strip()}) TO STDOUT WITH CSV HEADER"],
            capture_output=True, text=True, env=env, timeout=120
        )

        if result.returncode == 0 and result.stdout:
            with open(rls_file, 'w') as f:
                f.write(result.stdout)
            total_size += self._get_file_size(rls_file)
            files += 1
            self.log(f"RLS Policies exportiert: {rls_file}")
        else:
            self.log(f"WARNING: RLS Policy Export: {result.stderr}")

        # Dump auth schema
        auth_file = os.path.join(config_dir, f"auth_schema_{timestamp}.sql")
        self.log("Exporting auth schema...")
        result = subprocess.run(
            ['pg_dump', connection_string,
             '--schema=auth', '--schema=storage',
             '-f', auth_file],
            capture_output=True, text=True, env=env, timeout=300
        )

        if result.returncode == 0:
            total_size += self._get_file_size(auth_file)
            files += 1
            self.log(f"Auth/Storage Schema exportiert: {auth_file}")
        else:
            self.log(f"WARNING: Auth Schema Export: {result.stderr}")

        return total_size, files

    def _extract_project_ref(self, connection_string):
        """Extract project ref from connection string.
        Handles both formats:
        - pooler: postgres.PROJECTREF@...pooler.supabase.com
        - direct: @db.PROJECTREF.supabase.co
        """
        import re
        # Try pooler format: postgres.XXXXX:
        match = re.search(r'postgres\.([a-z]+)[:@]', connection_string)
        if match:
            return match.group(1)
        # Try direct format: db.XXXXX.supabase
        match = re.search(r'db\.([a-z]+)\.supabase', connection_string)
        if match:
            return match.group(1)
        return ''

    def _api_get(self, url, headers):
        """Simple GET request, returns parsed JSON or empty list."""
        req = Request(url, headers=headers, method='GET')
        try:
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except (HTTPError, URLError) as e:
            self.log(f"WARNING: API GET {url} fehlgeschlagen: {e}")
            return []

    def _download_file(self, url, headers, dest_path):
        """Download file from URL to dest_path."""
        req = Request(url, headers=headers, method='GET')
        with urlopen(req, timeout=120) as resp:
            with open(dest_path, 'wb') as f:
                shutil.copyfileobj(resp, f)
