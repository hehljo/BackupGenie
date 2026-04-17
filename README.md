<div align="center">

# 🧞 BackupGenie

### Automated Multi-Source Backup Manager

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-20.10%2B-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-green.svg)](https://nodejs.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-yellow.svg?logo=buy-me-a-coffee&logoColor=white)](https://buymeacoffee.com/pommesbude)

**[Features](#-features)** • **[Quick Start](#-quick-start)** • **[Documentation](docs/)** • **[API Docs](#-api-documentation)** • **[Contributing](CONTRIBUTING.md)**

---

A self-hosted backup manager with a modern web UI that automatically syncs 60+ source types (NAS, GitHub, Supabase, cloud services, Docker, self-hosted apps). Runs on Raspberry Pi, Synology NAS, any Linux server, or as a Docker container on any platform.

> 🌍 Web UI available in **English** and **German**.

</div>

---

## 🧪 Test Status

> Community-tested sources are marked ✅. Sources marked 🔲 are implemented but awaiting real-world validation — reports welcome via [Discussions](https://github.com/hehljo/BackupGenie/discussions).

| Source | Backup | Restore | Notes |
|--------|--------|---------|-------|
| **GitHub** (mirror clone, auto-discovery) | ✅ Tested | — | 77 repos, incl. private + orgs |
| **Supabase** (DB + Storage + Auth Config) | ✅ Tested | ✅ Tested | Full + db\_only mode, live logs |
| NAS (SMB) | 🔲 | — | |
| NAS (NFS) | 🔲 | — | |
| rsync over SSH | 🔲 | — | |
| GitLab | 🔲 | — | |
| Bitbucket | 🔲 | — | |
| Gitea | 🔲 | — | |
| MySQL | 🔲 | — | |
| PostgreSQL | 🔲 | — | |
| MongoDB | 🔲 | — | |
| Redis | 🔲 | — | |
| Google Drive (rclone) | 🔲 | — | |
| Dropbox (rclone) | 🔲 | — | |
| OneDrive (rclone) | 🔲 | — | |
| S3 / Backblaze B2 (rclone) | 🔲 | — | |
| Nextcloud | 🔲 | — | |
| Portainer / Docker Volumes | 🔲 | — | |
| Home Assistant | 🔲 | — | |
| Local filesystem | 🔲 | — | |

If you've tested a source, please [share your setup](https://github.com/hehljo/BackupGenie/discussions) — it helps others a lot.

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🔄 60+ Backup Sources
- **Network Storage**: NAS (SMB/NFS), rsync over SSH
- **Git Platforms**: GitHub (auto-discovery), GitLab, Bitbucket, Gitea
- **BaaS/PaaS**: Supabase (DB + Storage + Config)
- **Databases**: MySQL, PostgreSQL, MongoDB, Redis
- **Cloud Storage**: Google Drive, Dropbox, OneDrive, S3
- **Self-Hosted**: Nextcloud, Plex, Home Assistant, Vaultwarden, Portainer
- **Docker**: volumes, containers, images
- **Local**: filesystems, home directories

📚 [Full source list →](docs/BACKUP_SOURCES.md)

</td>
<td width="50%">

### 🎯 Smart Automation
- ⚡ **USB trigger**: auto-start when a drive is plugged in (Pi)
- 🔍 **Auto-discovery**: detect GitHub repos automatically
- 🌐 **Modern Web UI**: React-based SPA
- 🔐 **Secure**: SSH key auth, SSL/TLS, RBAC
- 📊 **Real-time monitoring**: live dashboard & logs
- 🐳 **Docker-based**: one-command deployment
- 🖥️ **Universal**: Raspberry Pi, Synology, Linux, Docker
- 🌍 **Multi-language**: 🇬🇧 English & 🇩🇪 German

</td>
</tr>
</table>

---

## 🚀 Quick Start

> [!NOTE]
> Requires Docker 20.10+ and 2 GB+ RAM. Runs on Raspberry Pi, Synology NAS, Linux servers, or any Docker host.

### One-line install

```bash
curl -fsSL https://raw.githubusercontent.com/hehljo/BackupGenie/main/install.sh | bash
```

### Manual setup

```bash
# 1. Clone the repository
git clone https://github.com/hehljo/BackupGenie.git
cd BackupGenie

# 2. Set SECRET_KEY (mandatory)
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# 3. Start the services
SECRET_KEY=$SECRET_KEY docker compose up -d

# 4. Get the admin password from logs
docker compose logs backend | grep "INIT"

# 5. Open the Web UI → configure credentials and sources
open http://localhost:3000
```

**Login**: `admin` / password from the container logs (step 4). All credentials (tokens, passwords) are managed via the Web UI.

---

## 📋 Table of Contents

<details open>
<summary>Click to expand</summary>

- [Requirements](#-requirements)
- [Installation](#-installation)
  - [Synology NAS / Portainer](#-synology-nas--portainer)
  - [Linux Server / VPS](#-linux-server--vps)
  - [Raspberry Pi](#-raspberry-pi)
  - [Docker (generic)](#-docker-generic)
  - [Initial Configuration](#initial-configuration)
- [Configuration](#️-configuration)
  - [Backup Sources](#backup-sources)
  - [USB Auto-Trigger](#usb-auto-trigger)
  - [Credentials Management](#credentials-management)
- [Usage](#-usage)
  - [Web Interface](#web-interface)
  - [API Usage](#api-usage)
  - [CLI Commands](#cli-commands)
- [Internationalization (i18n)](#-internationalization-i18n)
- [API Documentation](#-api-documentation)
- [Troubleshooting](#-troubleshooting)
- [Security](#-security)
- [Development](#-development)
- [Contributing](#-contributing)
- [License](#-license)

</details>

---

## 🔧 Requirements

### Hardware
| Platform | RAM | Architecture |
|----------|-----|--------------|
| **Raspberry Pi 3/4/5** | 2 GB+ | ARM/ARM64 |
| **Synology NAS** | 2 GB+ | x86_64/ARM64 |
| **Linux Server** | 2 GB+ | x86_64/ARM64 |
| **Docker Host** | 2 GB+ | x86_64/ARM64/ARM |

Hardware is detected automatically and resources are tuned to match.

### Software
```
Docker:  20.10+
Compose: 2.0+
```

### Authentication Requirements
- 🔑 **NAS**: SMB/NFS credentials
- 🔑 **GitHub**: Personal Access Token
- 🔑 **Cloud**: OAuth2 credentials or API keys
- 🔑 **SSH**: private key for rsync

---

## 🚀 Installation

> [!TIP]
> BackupGenie detects your hardware automatically and adjusts resources (workers, RAM limits, parallel tasks) on its own.

### 📦 Synology NAS / Portainer

<details>
<summary>Step-by-step guide</summary>

#### 1. Create folders on the Diskstation (SSH)

```bash
sudo mkdir -p /volume1/docker/backupgenie/{config,data,logs,backup}
```

#### 2. Generate a SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 3. Create the stack in Portainer

**Portainer** → **Stacks** → **Add Stack**:

| Field | Value |
|-------|-------|
| **Name** | `backupgenie` |
| **Build method** | Repository |
| **Repository URL** | `https://github.com/hehljo/BackupGenie` |
| **Repository reference** | `refs/heads/main` |
| **Compose path** | `docker-compose.portainer.yml` |

> **Private repo?** → enable **Authentication** → username: your GitHub user → password: Personal Access Token (classic, scope: `repo`)

**Environment variables** (advanced mode):

```
SECRET_KEY=your_generated_key
PLATFORM_PROFILE=auto
API_PORT=5050
FRONTEND_PORT=3080
```

> No `.env` file required! Just these four variables. All credentials (GitHub token, Supabase etc.) are managed through the Web UI.

→ **Deploy the stack**

#### 4. Log in

```
http://diskstation-ip:3080
```

**Password:** generated randomly on first start. Find it in Portainer → container `backupgenie-backend` → **Logs** → search for `[INIT] Admin user created. Password:`

Change the password immediately under **Settings → User**.

#### 5. Configure

1. **Settings → Credentials** → enter GitHub token, NAS passwords etc. (stored encrypted)
2. **Sources → Add Source** → configure backup sources
3. **Start backup** → Dashboard → Start Backup

#### Updates

In **Portainer** → stack `backupgenie` → **Update the stack** → **Re-pull image and redeploy**

#### Synology notes

- **Ports:** DSM occupies 5000/5001 — use `API_PORT=5050` and `FRONTEND_PORT=3080`
- **Autostart after reboot:** handled automatically via `restart: unless-stopped`
- **Permissions:** if you hit permission errors, run `sudo chown -R 1000:1000 /volume1/docker/backupgenie/`
- **Persistent data:** everything under `/volume1/docker/backupgenie/` survives updates

</details>

### 🐧 Linux Server / VPS

<details>
<summary>Step-by-step guide</summary>

#### 1. Install Docker (if not already installed)

```bash
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker $USER
# Log in again so the group change takes effect
```

#### 2. Install BackupGenie

```bash
cd /opt
sudo git clone https://github.com/hehljo/BackupGenie.git
sudo chown -R $USER:$USER BackupGenie
cd BackupGenie

cp config/example.env .env
cp config/sources-example.json config/sources.json
```

#### 3. Configure

```bash
nano .env
```
```bash
SECRET_KEY=$(openssl rand -base64 32)
BACKUP_BASE_PATH=/mnt/backups
```

#### 4. Start

```bash
docker compose up -d
docker compose ps
```

#### 5. Open the Web UI

```
http://server-ip:3000
```

</details>

### 🥧 Raspberry Pi

<details>
<summary>Step-by-step guide</summary>

#### 1. Prepare the system

```bash
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker pi

# For USB auto-trigger (optional)
sudo apt install -y usbmount

sudo reboot
```

#### 2. Install BackupGenie

```bash
cd /opt
sudo git clone https://github.com/hehljo/BackupGenie.git
sudo chown -R pi:pi BackupGenie
cd BackupGenie

cp config/example.env .env
cp config/sources-example.json config/sources.json
```

#### 3. Configure

```bash
nano .env
```
```bash
SECRET_KEY=a_long_random_string
BACKUP_BASE_PATH=/mnt/backup

# Pi 3 with limited RAM: tune the limits
# BACKEND_MEMORY_LIMIT=512M
# BACKEND_CPU_LIMIT=1.5
# FRONTEND_MEMORY_LIMIT=128M
```

#### 4. Start

```bash
docker compose up -d
```

#### 5. Open the Web UI

```
http://raspberrypi.local:3000
```

#### Set up USB auto-trigger (optional)

Plug in a USB drive → backup starts automatically:

```bash
# Create the udev rule
sudo nano /etc/udev/rules.d/99-backupgenie-backup.rules
```
```
ACTION=="add", KERNEL=="sd[a-z][0-9]", TAG+="systemd", ENV{SYSTEMD_WANTS}="backupgenie-backup@%k.service"
```
```bash
sudo udevadm control --reload-rules
```

Detailed guide: [USB Auto-Trigger →](#usb-auto-trigger)

</details>

### 🐳 Docker (generic)

<details>
<summary>For any platform with Docker</summary>

```bash
git clone https://github.com/hehljo/BackupGenie.git
cd BackupGenie
cp config/example.env .env
cp config/sources-example.json config/sources.json

# Adjust .env
nano .env

# Start
docker compose up -d

# Web UI: http://localhost:3000
```

#### Portainer (without Synology)

In Portainer → Stacks → Add Stack → Repository:
1. Repository URL: `https://github.com/hehljo/BackupGenie`
2. Compose path: `docker-compose.portainer.yml` (uses prebuilt GHCR images, no build needed)
3. Set environment variables (at minimum `SECRET_KEY`)
4. Deploy

#### Environment variables for resource tuning

| Variable | Default | Description |
|----------|---------|-------------|
| `PLATFORM_PROFILE` | `auto` | `auto`, `raspberrypi`, `synology`, `server` |
| `BACKEND_CPU_LIMIT` | `2.0` | CPU limit for the backend |
| `BACKEND_MEMORY_LIMIT` | `1G` | RAM limit for the backend |
| `FRONTEND_CPU_LIMIT` | `1.0` | CPU limit for the frontend |
| `FRONTEND_MEMORY_LIMIT` | `256M` | RAM limit for the frontend |
| `MAX_PARALLEL_TASKS` | `auto` | Parallel backup tasks (auto = based on RAM) |

</details>

### Initial Configuration

> [!IMPORTANT]
> `SECRET_KEY` is mandatory. Without it, the app refuses to start.
> Generate one: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`

**Required environment variables:**

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Random string for JWT + credential encryption |
| `API_PORT` | No (5000) | Port for the backend API |
| `FRONTEND_PORT` | No (3000) | Port for the Web UI |
| `PLATFORM_PROFILE` | No (auto) | `auto`, `raspberrypi`, `synology`, `server` |

> **Credentials** (GitHub token, NAS passwords, Supabase keys etc.) are **not** set via environment variables — manage them through the Web UI under **Settings → Credentials**. They are stored AES-encrypted in the database.

**Login:** `admin` / password is generated randomly on first start → `docker compose logs backend | grep "INIT"`

### 💾 Data Persistence (Docker Volumes)

> [!NOTE]
> **All your data survives a reinstall!**

BackupGenie uses Docker volumes for persistent storage. During updates or reinstalls, the following data is preserved automatically:

**Persistent directories:**

```yaml
./config/         # ✅ All backup sources (sources.json)
                  # ✅ rclone configuration
                  # ✅ Notification settings

./data/           # ✅ Database (users, history, settings)
                  # ✅ Backup logs
                  # ✅ Metadata

./logs/           # ✅ Application logs

/mnt/backup/      # ✅ Your backup data (configurable)
```

**Benefits:**
- 🔄 **Safe updates:** `docker compose pull && docker compose up -d`
- 💾 **Backup-friendly:** just back up `./config/` and `./data/`
- 🚀 **Migration:** copy folders → fresh install → done!
- ⚡ **Rollback:** start an older container version with no data loss

**Create a full backup:**

```bash
# Save BackupGenie configuration
cd /opt/BackupGenie
tar -czf backupgenie-config-$(date +%Y%m%d).tar.gz config/ data/ .env

# Copy to a safe location
cp backupgenie-config-*.tar.gz /mnt/external-drive/
```

**Restore after a fresh install:**

```bash
# Fresh install
cd /opt
git clone https://github.com/hehljo/BackupGenie.git
cd BackupGenie

# Restore the backup
tar -xzf /mnt/external-drive/backupgenie-config-*.tar.gz

# Start the containers - all settings are back!
docker compose up -d
```

**Export/Import via the Web UI:**

Since v1.1 you can also export/import all settings directly from the web interface:

1. **Settings** → **Configuration Export/Import**
2. **Export** → downloads a JSON file with all sources & settings
3. **Import** → select a JSON file and restore your configuration

---

## ⚙️ Configuration

### Backup Sources

BackupGenie supports 60+ backup sources. Configure them in `config/sources.json`:

<details>
<summary>📁 NAS (SMB/NFS)</summary>

```json
{
  "id": "nas-project1",
  "name": "NAS - Project 1",
  "type": "smb",
  "enabled": true,
  "priority": 1,
  "source": "//192.168.1.100/projects/project1",
  "credentials": {
    "username": "backup_user",
    "password_env": "NAS_PASSWORD"
  },
  "options": {
    "recursive": true,
    "delete": true,
    "timeout": 300
  },
  "schedule": {
    "trigger": "usb_mount",
    "max_duration": 3600
  }
}
```

**Test connection:**
```bash
smbclient -L //192.168.1.100 -U backup_user
```

</details>

<details>
<summary>🐙 GitHub Repositories (auto-discovery)</summary>

```json
{
  "id": "github-repos",
  "name": "GitHub Repositories",
  "type": "github",
  "enabled": true,
  "priority": 2,
  "discovery_mode": "all",
  "exclude": ["user/some-unwanted-fork"],
  "repositories": [],
  "credentials": {
    "token_env": "GITHUB_TOKEN"
  },
  "options": {
    "include_wikis": true,
    "include_lfs": true
  }
}
```

**`discovery_mode`**: `"all"` automatically backs up all repos (private + public + orgs). New repos are picked up on the next backup. Use `"manual"` to pick repos individually via the Web UI.

**Generate a token:** GitHub → Settings → Developer settings → Personal access tokens → scopes: `repo`, `gist`

</details>

<details>
<summary>🟢 Supabase (DB + Storage)</summary>

Configuration is done through the Web UI:

1. **Settings → Credentials → Supabase** → create a new profile with the connection string (Session Pooler URI from the Supabase dashboard) + DB password + optional service role key
2. **Sources → Add Source → Supabase** → pick a profile + choose backup mode (`db_only` or `full`)
3. **Start backup**

**`backup_mode`**: `full` saves DB (roles + schema + data) + storage buckets + RLS/auth config. `db_only` for PostgreSQL dumps only.

**Restore:** History → backup with the restore button → choose target profile → start restore. Manual connection string entry is also supported.

</details>

<details>
<summary>☁️ Cloud Storage (rclone)</summary>

```json
{
  "id": "google-drive",
  "name": "Google Drive Backup",
  "type": "rclone",
  "remote": "gdrive",
  "path": "/My_Backup",
  "enabled": true,
  "priority": 3,
  "options": {
    "transfers": 4,
    "checkers": 8
  }
}
```

**Configure rclone:**
```bash
docker exec -it backupgenie-backend rclone config
```

Supports: Google Drive, Dropbox, OneDrive, S3, Backblaze B2, and 40+ more!

</details>

<details>
<summary>🐳 Docker Volumes</summary>

```json
{
  "id": "docker-volumes",
  "name": "Docker Volumes",
  "type": "docker",
  "enabled": true,
  "priority": 4,
  "volumes": ["volume1", "volume2"],
  "options": {
    "compress": true,
    "stop_containers": false
  }
}
```

</details>

<details>
<summary>💾 Local Directories</summary>

```json
{
  "id": "local-docs",
  "name": "Local Documents",
  "type": "local",
  "enabled": true,
  "priority": 5,
  "sources": [
    "/home/pi/documents",
    "/home/pi/photos"
  ],
  "options": {
    "recursive": true,
    "delete": false,
    "compress": false
  }
}
```

</details>

📚 **[View all 60+ supported sources →](docs/BACKUP_SOURCES.md)**

### USB Auto-Trigger

Configure automatic backup triggering when a USB drive is connected:

<details>
<summary>Set up udev + systemd</summary>

#### 1. Create the udev rule

```bash
sudo nano /etc/udev/rules.d/99-backupgenie-backup.rules
```

```bash
# Trigger backup when a USB device is added
ACTION=="add", KERNEL=="sd[a-z][0-9]", TAG+="systemd", ENV{SYSTEMD_WANTS}="backupgenie-backup@%k.service"
```

#### 2. Create the systemd service

```bash
sudo nano /etc/systemd/system/backupgenie-backup@.service
```

```ini
[Unit]
Description=BackupGenie Auto-Backup Trigger for %i
BindsTo=sys-subsystem-block-devices-%i.device
After=sys-subsystem-block-devices-%i.device
ConditionPathExists=/opt/BackupGenie/docker-compose.yml

[Service]
Type=oneshot
ExecStartPre=/bin/bash -c 'for i in {1..60}; do mountpoint -q /mnt/backup && break || sleep 1; done'
ExecStart=/opt/BackupGenie/scripts/trigger-backup.sh
StandardOutput=journal
StandardError=journal
User=pi
Group=docker
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
```

#### 3. Create the trigger script

```bash
sudo nano /opt/BackupGenie/scripts/trigger-backup.sh
```

```bash
#!/bin/bash
set -e

LOG_FILE="/var/log/backupgenie-trigger.log"
API_URL="http://localhost:5000/api/v1/backup/start"

echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup triggered" >> "$LOG_FILE"

# Check if backup directory is mounted
if ! mountpoint -q "/mnt/backup"; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: /mnt/backup not mounted" >> "$LOG_FILE"
    exit 1
fi

# Start backup via API
response=$(curl -s -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $(cat /etc/backupgenie/api-token)" \
    -d '{"parallel": 2, "notify": true}')

if echo "$response" | grep -q '"status":"started"'; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup started successfully" >> "$LOG_FILE"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Backup start failed" >> "$LOG_FILE"
    exit 1
fi
```

#### 4. Activate

```bash
sudo chmod +x /opt/BackupGenie/scripts/trigger-backup.sh
sudo systemctl daemon-reload
sudo udevadm control --reload-rules
```

</details>

### Credentials Management

All credentials are managed via the Web UI:

1. **Settings** → **Credentials**
2. Enter token / password (GitHub, NAS, Supabase, SMTP, Telegram etc.)
3. **Save Credentials**

Credentials are stored **AES-encrypted** in the database (Fernet/PBKDF2). No plaintext passwords in files or environment variables.

---

## 💾 Usage

### Web Interface

Access the dashboard at:
```
http://raspberrypi.local:3000
http://YOUR_PI_IP:3000
```

**Features:**
- 📊 Real-time backup status dashboard
- 📜 Detailed backup history with logs
- ⚙️ Source management (add/edit/delete)
- 🔐 Credentials configuration
- 📈 Storage usage statistics
- 🔔 Notification settings
- 🌍 Language switcher (EN/DE)

### API Usage

<details>
<summary>Start a backup via API</summary>

```bash
# Get an API token
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}' \
  | jq -r '.access_token')

# Start a backup
curl -X POST http://localhost:5000/api/v1/backup/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["nas-project1", "github-repos"],
    "parallel": 2,
    "notify": true
  }'
```

</details>

<details>
<summary>Check backup status</summary>

```bash
curl -X GET http://localhost:5000/api/v1/backup/BACKUP_ID \
  -H "Authorization: Bearer $TOKEN"
```

</details>

### CLI Commands

```bash
# Start a backup for specific sources
docker exec backupgenie-backend python -m app.backup.executor \
  --source github-repos --source nas-project1

# List all configured sources
docker exec backupgenie-backend python -m app.cli sources list

# Test a source connection
docker exec backupgenie-backend python -m app.cli sources test nas-project1

# View backup history
docker exec backupgenie-backend python -m app.cli backup history --limit 10

# Clean old backups
docker exec backupgenie-backend python -m app.cleanup --days 30
```

---

## 🌍 Internationalization (i18n)

BackupGenie ships with full multi-language support:

### Supported languages
- 🇬🇧 **English** — fully translated
- 🇩🇪 **Deutsch** — vollständig übersetzt

### Language selection
- **Frontend**: language switcher in the sidebar header
- **Backend**: auto-detection via the `Accept-Language` header
- **Storage**: preference saved in browser localStorage

### Adding a new language

See the detailed guide: **[i18n Documentation →](docs/i18n.md)**

**Quick steps:**
1. Frontend: create `frontend/src/locales/{lang}/translation.json`
2. Backend: run `pybabel init -d app/translations -l {lang}`
3. Translate the `.po` files
4. Compile: `pybabel compile -d app/translations`

**Technology stack:**
- Frontend: `react-i18next` + `i18next-browser-languagedetector`
- Backend: `Flask-Babel`

---

## 📡 API Documentation

### Authentication

All API endpoints require Bearer token authentication.

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your_password"
}

Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Endpoints

<details>
<summary>📦 Backup management</summary>

#### Start a backup
```http
POST /api/v1/backup/start
Authorization: Bearer TOKEN

{
  "sources": ["source-id-1", "source-id-2"],
  "parallel": 2,
  "notify": true
}

Response 200:
{
  "backup_id": "backup-uuid-1234",
  "status": "started",
  "started_at": "2025-11-13T19:30:00Z",
  "sources_count": 2
}
```

#### Get backup status
```http
GET /api/v1/backup/{backup_id}
Authorization: Bearer TOKEN

Response 200:
{
  "backup_id": "backup-uuid-1234",
  "status": "running",
  "progress": 65,
  "started_at": "2025-11-13T19:30:00Z",
  "sources": [...]
}
```

#### List backup history
```http
GET /api/v1/backup/history?limit=20&offset=0
Authorization: Bearer TOKEN

Response 200:
{
  "total": 156,
  "backups": [...]
}
```

</details>

<details>
<summary>🔧 Source management</summary>

#### List sources
```http
GET /api/v1/sources
Authorization: Bearer TOKEN

Response 200:
{
  "sources": [
    {
      "id": "nas-project1",
      "name": "NAS - Project 1",
      "type": "smb",
      "enabled": true,
      "last_backup": "2025-11-13T19:30:00Z",
      "status": "healthy"
    }
  ]
}
```

#### Add a source
```http
POST /api/v1/sources
Authorization: Bearer TOKEN
Content-Type: application/json

{
  "name": "GitHub Org",
  "type": "github",
  "repositories": ["org/repo1"],
  "credentials": {
    "token_env": "GITHUB_TOKEN"
  },
  "enabled": true
}

Response 201:
{
  "id": "github-org-1",
  "created_at": "2025-11-13T20:00:00Z",
  "status": "pending_validation"
}
```

#### Update a source
```http
PUT /api/v1/sources/{source_id}
Authorization: Bearer TOKEN
Content-Type: application/json

{
  "enabled": false
}
```

#### Delete a source
```http
DELETE /api/v1/sources/{source_id}
Authorization: Bearer TOKEN
```

</details>

📚 **[Complete API documentation →](docs/API.md)**

---

## 🐛 Troubleshooting

<details>
<summary>🚫 Docker containers won't start</summary>

```bash
# Check the logs
docker compose logs backend
docker compose logs frontend

# Rebuild the containers
docker compose down
docker compose up -d --build --force-recreate

# Check system resources
free -h
df -h
```

</details>

<details>
<summary>⚠️ Backup doesn't start automatically</summary>

```bash
# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Check systemd logs
journalctl -u backupgenie-backup@sd* -n 50 -f

# Debug USB devices
lsblk
sudo udevadm info --name=/dev/sda1 --attribute-walk
```

</details>

<details>
<summary>🔌 NAS connection fails</summary>

```bash
# Test SMB connection
smbclient -L //192.168.1.100 -U backup_user

# Test from inside Docker
docker exec backupgenie-backend smbclient -L //192.168.1.100 -U backup_user

# Verify credentials
cat /etc/backupgenie/credentials
```

</details>

<details>
<summary>🔑 GitHub token invalid</summary>

```bash
# Verify the token online
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user

# Update the token
nano .env.secrets
docker compose restart backend
```

</details>

<details>
<summary>💽 Disk space full</summary>

```bash
# Check available space
df -h /mnt/backup

# Find the largest files
du -sh /mnt/backup/* | sort -rh | head -20

# Clean old backups
docker exec backupgenie-backend python -m app.cleanup --days 30
```

</details>

📚 **[More troubleshooting →](docs/TROUBLESHOOTING.md)**

---

## 🔒 Security

> [!IMPORTANT]
> Follow security best practices to protect your backup data!

### SSH hardening

<details>
<summary>Set up secure SSH access</summary>

```bash
# Generate an ED25519 key pair (locally)
ssh-keygen -t ed25519 -o -a 100 -f ~/.ssh/backupgenie

# Copy the public key to the Raspberry Pi
ssh-copy-id -i ~/.ssh/backupgenie.pub pi@raspberrypi.local

# Configure the SSH server
sudo nano /etc/ssh/sshd_config
```

**Recommended `sshd_config` settings:**
```
Port 2222  # Non-standard port
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
PermitEmptyPasswords no
MaxAuthTries 3
X11Forwarding no
AllowUsers pi
```

```bash
sudo systemctl restart ssh
```

</details>

### Firewall configuration

```bash
# Enable UFW
sudo ufw enable

# Allow SSH (adjust port if changed)
sudo ufw allow 2222/tcp

# Allow API (local network only)
sudo ufw allow from 192.168.1.0/24 to any port 5000

# Allow Web UI (local network only)
sudo ufw allow from 192.168.1.0/24 to any port 3000

# Check status
sudo ufw status
```

### API token management

```bash
# Generate a long-lived API token
docker exec backupgenie-backend python -c "
from app.auth import generate_token
token = generate_token('backup-automation', expires_days=365)
print(f'Token: {token}')
"

# Store it securely
sudo mkdir -p /etc/backupgenie
echo 'YOUR_TOKEN' | sudo tee /etc/backupgenie/api-token > /dev/null
sudo chmod 600 /etc/backupgenie/api-token
sudo chown pi:pi /etc/backupgenie/api-token
```

### Encrypt credentials

```bash
# Install GPG
sudo apt install gpg -y

# Encrypt the credentials file
gpg -c /etc/backupgenie/credentials

# Securely delete the original
sudo shred -vfz /etc/backupgenie/credentials

# Decrypt in the Docker entrypoint
gpg --batch --yes --passphrase-file=/run/secrets/gpg_pass \
    -o /tmp/creds.txt \
    /etc/backupgenie/credentials.gpg
```

📚 **[Security best practices →](docs/SECURITY.md)**

---

## 👨‍💻 Development

### Project structure

```
BackupGenie/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/              # REST API endpoints
│   │   │   ├── backup.py
│   │   │   ├── sources.py
│   │   │   └── auth.py
│   │   ├── backup/           # Backup engine
│   │   │   ├── executor.py
│   │   │   ├── sources/      # 60+ source implementations
│   │   │   │   ├── smb.py
│   │   │   │   ├── github.py
│   │   │   │   ├── rclone.py
│   │   │   │   └── ...
│   │   │   └── tasks.py      # Celery tasks
│   │   ├── models/
│   │   │   └── backup.py
│   │   ├── translations/     # i18n translations
│   │   └── config.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/
│   │   ├── services/         # API client
│   │   └── locales/          # i18n translations
│   ├── package.json
│   └── Dockerfile
├── config/
│   ├── sources.json          # Backup source definitions
│   ├── rclone.conf          # rclone remote configurations
│   └── docker-compose.yml
├── scripts/
│   ├── trigger-backup.sh
│   └── backup-cleanup.sh
├── docs/
│   ├── BACKUP_SOURCES.md    # Complete source documentation
│   ├── API.md               # API reference
│   ├── i18n.md              # Internationalization guide
│   └── TROUBLESHOOTING.md
└── README.md
```

### Local development setup

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run the backend
flask run --debug

# Frontend
cd frontend
npm install
npm run dev
```

### Running tests

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test

# Integration tests
docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

### Build Docker images

```bash
# Build all services
docker compose build

# Build a specific service
docker compose build backend

# Build for ARM (Raspberry Pi)
docker buildx build --platform linux/arm/v7,linux/arm64 -t backupgenie-backend:latest .
```

📚 **[Development guide →](docs/DEVELOPMENT.md)**

---

## 🤝 Contributing

Contributions are welcome! See the [Contributing Guide](CONTRIBUTING.md) for details.

### How to contribute

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a pull request

### Development guidelines

- Follow [PEP 8](https://pep8.org/) for Python code
- Follow the [Airbnb Style Guide](https://github.com/airbnb/javascript) for JavaScript
- Write tests for new features
- Update documentation when API behavior changes
- Add i18n translations for any new UI strings

---

## 🎯 Roadmap

**Done**
- [x] Notifications (email, Telegram, ntfy, webhooks via Apprise)
- [x] Supabase backup + restore with profile-based credentials
- [x] Encrypted credential storage (Fernet/PBKDF2)
- [x] EN/DE multi-language UI
- [x] Configuration export/import
- [x] Multi-arch Docker images (amd64, arm64, armv7)

**In progress / planned**
- [ ] Dark/light theme toggle
- [ ] Advanced filtering in backup history
- [ ] Backup scheduling (cron-style triggers)
- [ ] Two-factor authentication (2FA)
- [ ] Audit logging
- [ ] Deduplication / incremental backups
- [ ] Restore UI for additional source types (currently Supabase only)
- [ ] Prometheus metrics export
- [ ] OpenAPI 3.0 spec
- [ ] Additional languages (FR, ES, IT)

---

## 📝 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 📞 Support & Community

<div align="center">

**Need help? Have questions?**

[![GitHub Issues](https://img.shields.io/github/issues/hehljo/BackupGenie?style=for-the-badge)](https://github.com/hehljo/BackupGenie/issues)
[![GitHub Discussions](https://img.shields.io/github/discussions/hehljo/BackupGenie?style=for-the-badge)](https://github.com/hehljo/BackupGenie/discussions)

[Report Bug](https://github.com/hehljo/BackupGenie/issues/new?template=bug_report.md) • [Request Feature](https://github.com/hehljo/BackupGenie/issues/new?template=feature_request.md) • [Ask a Question](https://github.com/hehljo/BackupGenie/discussions)

---

### ☕ Support this project

If BackupGenie helps you manage your backups, consider supporting development!

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support%20Development-yellow?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white)](https://buymeacoffee.com/pommesbude)

Your support keeps this project alive and growing! 🙏

</div>

### Resources

- 📚 **[Full documentation](docs/)**
- 🔌 **[API reference](docs/API.md)**
- 🌐 **[i18n guide](docs/i18n.md)**
- 🐞 **[Troubleshooting](docs/TROUBLESHOOTING.md)**
- 🔐 **[Security policy](SECURITY.md)**

---

<div align="center">

**Made with ❤️ by the BackupGenie community**

⭐ **Star this repo if BackupGenie helps you!** ⭐

[🏠 Home](https://github.com/hehljo/BackupGenie) • [📖 Docs](docs/) • [🐛 Issues](https://github.com/hehljo/BackupGenie/issues) • [💬 Discussions](https://github.com/hehljo/BackupGenie/discussions)

</div>
