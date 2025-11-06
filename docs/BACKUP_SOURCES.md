# BackupGenie - Supported Backup Sources

BackupGenie supports a comprehensive range of backup sources, from local files to cloud storage, databases, and Git repositories.

## Table of Contents

- [Local Storage](#local-storage)
- [Network Storage (NAS)](#network-storage-nas)
- [Git Platforms](#git-platforms)
- [Databases](#databases)
- [Cloud Storage](#cloud-storage)
- [FTP/SFTP](#ftpsftp)
- [WebDAV](#webdav)
- [Docker](#docker)

---

## Local Storage

### Local Files and Directories

**Type:** `local`

Backup local filesystem directories using rsync.

**Configuration:**
```json
{
  "id": "local-docs",
  "name": "Local Documents",
  "type": "local",
  "enabled": true,
  "priority": 1,
  "sources": [
    "/home/user/documents",
    "/home/user/photos"
  ],
  "options": {
    "recursive": true,
    "delete": false,
    "follow_symlinks": false
  }
}
```

**Options:**
- `recursive`: Recursively backup directories (default: true)
- `delete`: Delete files in destination that don't exist in source (default: false)
- `follow_symlinks`: Follow symbolic links (default: false)

---

## Network Storage (NAS)

### SMB/CIFS (Windows Shares, Samba)

**Type:** `smb`

Backup from Windows network shares or Samba servers.

**Configuration:**
```json
{
  "id": "nas-smb",
  "name": "NAS via SMB",
  "type": "smb",
  "enabled": true,
  "source": "//192.168.1.100/backupshare",
  "credentials": {
    "username": "backup_user",
    "password_env": "SMB_PASSWORD"
  },
  "options": {
    "recursive": true,
    "delete": true,
    "timeout": 300
  }
}
```

**Credentials:**
- `username`: SMB username
- `password_env`: Environment variable containing SMB password

### NFS (Network File System)

**Type:** `nfs`

Backup from NFS mounts (Unix/Linux network file systems).

**Configuration:**
```json
{
  "id": "nas-nfs",
  "name": "NAS via NFS",
  "type": "nfs",
  "enabled": true,
  "source": "192.168.1.100:/exports/backup",
  "options": {
    "vers": 3,
    "nolock": true
  }
}
```

**Options:**
- `vers`: NFS version (default: 3)
- `nolock`: Disable NFS locking (default: true)

### Rsync over SSH

**Type:** `rsync-ssh`, `rsync`, or `nas`

Backup from remote servers via rsync over SSH. Perfect for NAS systems (Synology, QNAP, TrueNAS).

**Configuration:**
```json
{
  "id": "synology-nas",
  "name": "Synology NAS",
  "type": "rsync-ssh",
  "enabled": true,
  "host": "192.168.1.100",
  "port": 22,
  "path": "/volume1/backup",
  "credentials": {
    "username_env": "NAS_USER",
    "ssh_key_path": "~/.ssh/id_rsa"
  },
  "options": {
    "delete": false,
    "compress": true,
    "recursive": true,
    "exclude": ["*.tmp", "*.log"],
    "timeout": 3600
  }
}
```

**Credentials:**
- `username_env`: Environment variable with SSH username
- `ssh_key_path`: Path to SSH private key (optional)
- `password_env`: Environment variable with SSH password (if not using key)

**Options:**
- `delete`: Delete files in destination not in source
- `compress`: Enable compression during transfer
- `recursive`: Recursively backup directories
- `exclude`: List of patterns to exclude
- `include`: List of patterns to include
- `strict_host_key_checking`: Verify SSH host key (default: true)
- `timeout`: Backup timeout in seconds (default: 3600)

---

## Git Platforms

### GitHub

**Type:** `github`

Backup GitHub repositories (public and private).

**Configuration:**
```json
{
  "id": "github-repos",
  "name": "GitHub Repositories",
  "type": "github",
  "enabled": true,
  "repositories": [
    "username/repo1",
    "organization/repo2"
  ],
  "credentials": {
    "token_env": "GITHUB_TOKEN"
  },
  "options": {
    "include_lfs": true,
    "include_wikis": true,
    "include_releases": true
  }
}
```

**Credentials:**
- `token_env`: Environment variable with GitHub Personal Access Token

**Options:**
- `include_lfs`: Backup Git LFS files (default: false)
- `include_wikis`: Backup repository wikis (default: false)
- `include_releases`: Backup release files (default: false)

### GitLab

**Type:** `gitlab`

Backup GitLab repositories (gitlab.com or self-hosted).

**Configuration:**
```json
{
  "id": "gitlab-repos",
  "name": "GitLab Projects",
  "type": "gitlab",
  "enabled": true,
  "host": "gitlab.example.com",  // Optional, defaults to gitlab.com
  "repositories": [
    "username/project1",
    "group/project2"
  ],
  "credentials": {
    "token_env": "GITLAB_TOKEN"
  },
  "options": {
    "include_lfs": true,
    "include_wikis": true
  }
}
```

### Gitea / Forgejo

**Type:** `gitea` or `forgejo`

Backup Gitea or Forgejo self-hosted repositories.

**Configuration:**
```json
{
  "id": "gitea-repos",
  "name": "Gitea Repositories",
  "type": "gitea",
  "enabled": true,
  "host": "git.example.com",
  "repositories": [
    "user/repo1",
    "organization/repo2"
  ],
  "credentials": {
    "token_env": "GITEA_TOKEN"
  }
}
```

### Bitbucket

**Type:** `bitbucket`

Backup Bitbucket repositories.

**Configuration:**
```json
{
  "id": "bitbucket-repos",
  "name": "Bitbucket Repositories",
  "type": "bitbucket",
  "enabled": true,
  "repositories": [
    "workspace/repo1"
  ],
  "credentials": {
    "token_env": "BITBUCKET_TOKEN"
  }
}
```

### Codeberg

**Type:** `codeberg`

Backup Codeberg repositories.

**Configuration:**
```json
{
  "id": "codeberg-repos",
  "name": "Codeberg Repositories",
  "type": "codeberg",
  "enabled": true,
  "repositories": [
    "username/project1"
  ],
  "credentials": {
    "token_env": "CODEBERG_TOKEN"
  }
}
```

---

## Databases

### MySQL / MariaDB

**Type:** `mysql` or `mariadb`

Backup MySQL or MariaDB databases using `mysqldump`.

**Configuration:**
```json
{
  "id": "mysql-db",
  "name": "MySQL Database",
  "type": "mysql",
  "enabled": true,
  "host": "localhost",
  "port": 3306,
  "databases": [
    "production_db",
    "analytics_db"
  ],
  "credentials": {
    "username_env": "MYSQL_USER",
    "password_env": "MYSQL_PASSWORD"
  },
  "options": {
    "compress": true,
    "gzip": true
  }
}
```

**Options:**
- `compress`: Use MySQL compression (default: true)
- `gzip`: Compress backup file with gzip (default: true)

**Note:** Leave `databases` empty to backup all databases.

### PostgreSQL

**Type:** `postgresql` or `postgres`

Backup PostgreSQL databases using `pg_dump`.

**Configuration:**
```json
{
  "id": "postgresql-db",
  "name": "PostgreSQL Database",
  "type": "postgresql",
  "enabled": true,
  "host": "localhost",
  "port": 5432,
  "databases": [
    "app_database"
  ],
  "credentials": {
    "username_env": "POSTGRES_USER",
    "password_env": "POSTGRES_PASSWORD"
  },
  "options": {
    "gzip": true,
    "schema_only": false,
    "data_only": false
  }
}
```

**Options:**
- `gzip`: Compress backup with gzip (default: true)
- `schema_only`: Backup only schema (default: false)
- `data_only`: Backup only data (default: false)

### MongoDB

**Type:** `mongodb` or `mongo`

Backup MongoDB databases using `mongodump`.

**Configuration:**
```json
{
  "id": "mongodb-db",
  "name": "MongoDB Database",
  "type": "mongodb",
  "enabled": true,
  "host": "localhost",
  "port": 27017,
  "database": "myapp",
  "credentials": {
    "username_env": "MONGO_USER",
    "password_env": "MONGO_PASSWORD"
  },
  "options": {
    "gzip": true
  }
}
```

**Credentials:** Optional for MongoDB (only if authentication is enabled)

### Redis

**Type:** `redis`

Backup Redis database using RDB snapshot.

**Configuration:**
```json
{
  "id": "redis-cache",
  "name": "Redis Database",
  "type": "redis",
  "enabled": true,
  "host": "localhost",
  "port": 6379,
  "credentials": {
    "password_env": "REDIS_PASSWORD"
  }
}
```

**Credentials:** Optional (only if Redis has password protection)

### SQLite

**Type:** `sqlite`

Backup SQLite database files.

**Configuration:**
```json
{
  "id": "sqlite-dbs",
  "name": "SQLite Databases",
  "type": "sqlite",
  "enabled": true,
  "databases": [
    "/var/lib/app/database.db",
    "/home/user/data/local.db"
  ]
}
```

**Note:** Provide full paths to SQLite database files.

### CouchDB

**Type:** `couchdb`

Backup CouchDB databases.

**Configuration:**
```json
{
  "id": "couchdb-db",
  "name": "CouchDB Database",
  "type": "couchdb",
  "enabled": true,
  "host": "localhost",
  "port": 5984,
  "databases": [
    "app_data"
  ],
  "credentials": {
    "username_env": "COUCHDB_USER",
    "password_env": "COUCHDB_PASSWORD"
  }
}
```

---

## Cloud Storage

All major cloud storage providers are supported via **rclone**.

### Type: `rclone`

**Supported Services:**
- Google Drive
- Microsoft OneDrive
- Dropbox
- Apple iCloud Drive
- Amazon S3
- Backblaze B2
- DigitalOcean Spaces
- Wasabi
- Azure Blob Storage
- Google Cloud Storage
- Box
- Mega
- pCloud
- Nextcloud (via rclone)
- ...and 40+ more

### Google Drive

```json
{
  "id": "google-drive",
  "name": "Google Drive",
  "type": "rclone",
  "enabled": true,
  "remote": "gdrive",
  "path": "/Backup",
  "options": {
    "transfers": 4,
    "checkers": 8
  }
}
```

### Dropbox

```json
{
  "id": "dropbox",
  "name": "Dropbox",
  "type": "rclone",
  "enabled": true,
  "remote": "dropbox",
  "path": "/Backups"
}
```

### OneDrive

```json
{
  "id": "onedrive",
  "name": "Microsoft OneDrive",
  "type": "rclone",
  "enabled": true,
  "remote": "onedrive",
  "path": "/Documents/Backup"
}
```

### AWS S3

```json
{
  "id": "aws-s3",
  "name": "AWS S3 Bucket",
  "type": "rclone",
  "enabled": true,
  "remote": "s3",
  "path": "/my-backup-bucket",
  "options": {
    "transfers": 8,
    "checkers": 16
  }
}
```

### Backblaze B2

```json
{
  "id": "backblaze-b2",
  "name": "Backblaze B2",
  "type": "rclone",
  "enabled": true,
  "remote": "b2",
  "path": "/my-backup-bucket"
}
```

**Options:**
- `transfers`: Number of parallel file transfers (default: 4)
- `checkers`: Number of parallel file checkers (default: 8)

**Note:** You need to configure rclone remotes first using `rclone config`.

---

## WebDAV

**Type:** `webdav`

Backup from WebDAV servers (Nextcloud, Seafile, ownCloud, etc.).

**Configuration:**
```json
{
  "id": "nextcloud",
  "name": "Nextcloud",
  "type": "webdav",
  "enabled": true,
  "host": "cloud.example.com",
  "path": "/remote.php/dav/files/username/Backup",
  "https": true,
  "vendor": "nextcloud",
  "credentials": {
    "username_env": "NEXTCLOUD_USER",
    "password_env": "NEXTCLOUD_PASSWORD"
  },
  "options": {
    "method": "rclone",
    "transfers": 4,
    "delete": false
  }
}
```

**Options:**
- `method`: Backup method ("rclone" or "davfs") (default: "rclone")
- `transfers`: Number of parallel transfers (rclone only)
- `delete`: Delete files in destination not in source

**Vendors:** `nextcloud`, `owncloud`, `seafile`, `sharepoint`, `other`

---

## FTP/SFTP

### FTP/FTPS

**Type:** `ftp` or `ftps`

Backup from FTP or FTPS servers using lftp.

**Configuration:**
```json
{
  "id": "ftp-server",
  "name": "FTP Server",
  "type": "ftp",
  "enabled": true,
  "host": "ftp.example.com",
  "port": 21,
  "path": "/backup",
  "ftps": false,
  "credentials": {
    "username_env": "FTP_USER",
    "password_env": "FTP_PASSWORD"
  },
  "options": {
    "parallel": 2,
    "delete": false,
    "only_newer": true
  }
}
```

**Options:**
- `parallel`: Number of parallel connections (default: 2)
- `delete`: Delete files in destination not in source
- `only_newer`: Only download newer files (default: true)

### SFTP

**Type:** `sftp`

Backup from SFTP servers using rsync over SSH.

**Configuration:**
```json
{
  "id": "sftp-server",
  "name": "SFTP Server",
  "type": "sftp",
  "enabled": true,
  "host": "sftp.example.com",
  "port": 22,
  "path": "/backup",
  "credentials": {
    "username_env": "SFTP_USER",
    "ssh_key_path": "~/.ssh/id_rsa",
    "password_env": "SFTP_PASSWORD"
  },
  "options": {
    "delete": false,
    "compress": true
  }
}
```

**Credentials:** Use either `ssh_key_path` or `password_env` (key is preferred).

---

## Docker

### Docker Volumes

**Type:** `docker-volume`

Backup Docker volumes and container filesystems.

**Configuration:**
```json
{
  "id": "docker-volumes",
  "name": "Docker Volumes",
  "type": "docker-volume",
  "enabled": true,
  "volumes": [
    "mysql_data",
    "nginx_config",
    "app_uploads"
  ],
  "containers": [
    "web_app",
    "database"
  ],
  "options": {
    "export_filesystem": true,
    "backup_config": true
  }
}
```

**Options:**
- `export_filesystem`: Export container filesystem as tar (default: true)
- `backup_config`: Save container configuration (default: true)

### Docker Images

**Type:** `docker-image`

Backup Docker images as tar archives.

**Configuration:**
```json
{
  "id": "docker-images",
  "name": "Docker Images",
  "type": "docker-image",
  "enabled": true,
  "images": [
    "nginx:latest",
    "mysql:8.0",
    "myapp:production"
  ],
  "options": {
    "compress": true
  }
}
```

**Options:**
- `compress`: Compress with gzip (default: true)

---

## Environment Variables

Many backup sources require credentials stored in environment variables for security.

**Example `.env` file:**
```bash
# NAS Credentials
SMB_PASSWORD=your_smb_password
NAS_USER=backup_user

# Git Platforms
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
GITEA_TOKEN=xxxxxxxxxxxxxxxxxxxx
BITBUCKET_TOKEN=xxxxxxxxxxxxxxxxxxxx
CODEBERG_TOKEN=xxxxxxxxxxxxxxxxxxxx

# Databases
MYSQL_USER=backup_user
MYSQL_PASSWORD=your_mysql_password
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password
MONGO_USER=admin
MONGO_PASSWORD=your_mongo_password
REDIS_PASSWORD=your_redis_password
COUCHDB_USER=admin
COUCHDB_PASSWORD=your_couchdb_password

# Cloud/FTP/WebDAV
FTP_USER=ftpuser
FTP_PASSWORD=ftppassword
SFTP_USER=sftpuser
NEXTCLOUD_USER=username
NEXTCLOUD_PASSWORD=password
```

**Load environment variables:**
```bash
export $(cat .env | xargs)
```

---

## Summary

BackupGenie supports **30+ backup source types** across:
- ✅ **Local Storage** (files, directories)
- ✅ **Network Storage** (SMB, NFS, rsync/SSH, NAS systems)
- ✅ **Git Platforms** (GitHub, GitLab, Gitea, Forgejo, Bitbucket, Codeberg)
- ✅ **Databases** (MySQL, PostgreSQL, MongoDB, Redis, SQLite, CouchDB)
- ✅ **Cloud Storage** (Google Drive, Dropbox, OneDrive, S3, Backblaze B2, and 40+ more)
- ✅ **WebDAV** (Nextcloud, Seafile, ownCloud)
- ✅ **FTP/SFTP** (FTP, FTPS, SFTP servers)
- ✅ **Docker** (volumes, containers, images)

For complete examples, see `config/sources-extended-example.json`.
