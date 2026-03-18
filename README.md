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

Ein selbstgehostetes Backup-System mit moderner Weboberfläche zur automatischen Synchronisierung von 60+ Quellen (NAS, GitHub, Supabase, Cloud-Services, Docker, Self-Hosted Apps). Läuft auf Raspberry Pi, Synology NAS, jedem Linux-Server oder als Docker-Container auf jeder Plattform.

[🇩🇪 Deutsch](#) • [🇬🇧 English](README.en.md)

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🔄 60+ Backup Sources
- **Network Storage**: NAS (SMB/NFS), rsync over SSH
- **Git Platforms**: GitHub (Auto-Discovery), GitLab, Bitbucket, Gitea
- **BaaS/PaaS**: Supabase (DB + Storage + Config)
- **Databases**: MySQL, PostgreSQL, MongoDB, Redis
- **Cloud Storage**: Google Drive, Dropbox, OneDrive, S3
- **Self-Hosted**: Nextcloud, Plex, Home Assistant, Vaultwarden, Portainer
- **Docker**: Volumes, Containers, Images
- **Local**: Filesystems, Home Directories

📚 [Vollständige Quellenliste →](docs/BACKUP_SOURCES.md)

</td>
<td width="50%">

### 🎯 Smart Automation
- ⚡ **USB-Trigger**: Automatischer Start beim Einstecken (Pi)
- 🔍 **Auto-Discovery**: GitHub Repos automatisch erkennen
- 🌐 **Modern Web UI**: React-basierte SPA
- 🔐 **Secure**: SSH-Key Auth, SSL/TLS, RBAC
- 📊 **Real-time Monitoring**: Live Dashboard & Logs
- 🐳 **Docker-based**: One-command deployment
- 🖥️ **Universal**: Raspberry Pi, Synology, Linux, Docker
- 🌍 **Multi-Language**: 🇩🇪 German & 🇬🇧 English

</td>
</tr>
</table>

---

## 🚀 Quick Start

> [!NOTE]
> Requires Docker 20.10+ and 2GB+ RAM. Runs on Raspberry Pi, Synology NAS, Linux servers, or any Docker host.

### One-Line Install

```bash
curl -fsSL https://raw.githubusercontent.com/hehljo/BackupGenie/main/install.sh | bash
```

### Manual Setup

```bash
# 1. Clone repository
git clone https://github.com/hehljo/BackupGenie.git
cd BackupGenie

# 2. Configure environment
cp config/example.env .env
cp config/sources-example.json config/sources.json
nano .env  # Edit your settings

# 3. Start services
docker compose up -d

# 4. Open Web UI
open http://localhost:3000
```

**Default Login**: `admin` / Check logs: `docker compose logs backend | grep "Initial password"`

---

## 📋 Table of Contents

<details open>
<summary>Click to expand</summary>

- [Requirements](#-requirements)
- [Installation](#-installation)
  - [Synology NAS / Portainer](#-synology-nas--portainer)
  - [Linux Server / VPS](#-linux-server--vps)
  - [Raspberry Pi](#-raspberry-pi)
  - [Docker (Generic)](#-docker-generic)
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
| Platform | RAM | Architektur |
|----------|-----|-------------|
| **Raspberry Pi 3/4/5** | 2 GB+ | ARM/ARM64 |
| **Synology NAS** | 2 GB+ | x86_64/ARM64 |
| **Linux Server** | 2 GB+ | x86_64/ARM64 |
| **Docker Host** | 2 GB+ | x86_64/ARM64/ARM |

Hardware wird automatisch erkannt und Ressourcen entsprechend angepasst.

### Software
```
Docker:  20.10+
Compose: 2.0+
```

### Authentication Requirements
- 🔑 **NAS**: SMB/NFS credentials
- 🔑 **GitHub**: Personal Access Token
- 🔑 **Cloud**: OAuth2 credentials or API keys
- 🔑 **SSH**: Private key for rsync

---

## 🚀 Installation

> [!TIP]
> BackupGenie erkennt die Hardware automatisch und passt Ressourcen (Worker, RAM-Limits, Parallel-Tasks) selbstständig an.

### 📦 Synology NAS / Portainer

<details>
<summary>Schritt-für-Schritt Anleitung</summary>

#### Verzeichnisstruktur auf der Diskstation

Alle Daten liegen persistent unter `/volume1/docker/backupgenie/` (Mariushosting-Konvention). Bei Updates oder Neuinstallation bleiben alle Daten erhalten.

```
/volume1/docker/backupgenie/
├── config/          # Backup-Quellen, rclone, Notifications
│   ├── sources.json
│   ├── rclone.conf
│   └── notifications.json
├── data/            # Datenbank, User, Backup-Historie
├── logs/            # Anwendungs-Logs
└── backup/          # Hier landen die Backups
```

#### 1. Ordner per SSH anlegen

```bash
sudo mkdir -p /volume1/docker/backupgenie/{config,data,logs,backup}
```

#### 2. Beispiel-Configs kopieren (einmalig)

```bash
cd /volume1/docker/backupgenie
# Temporär Repo klonen um Config-Templates zu holen
git clone --depth 1 https://github.com/hehljo/BackupGenie.git /tmp/backupgenie-setup
cp /tmp/backupgenie-setup/config/sources-example.json config/sources.json
cp /tmp/backupgenie-setup/config/example.env .env
rm -rf /tmp/backupgenie-setup
```

#### 3. `.env` konfigurieren

```bash
nano /volume1/docker/backupgenie/.env
```
```bash
SECRET_KEY=hier_einen_langen_zufaelligen_string_setzen
PLATFORM_PROFILE=auto

# Pfade auf der Diskstation (persistent!)
CONFIG_PATH=/volume1/docker/backupgenie/config
DATA_PATH=/volume1/docker/backupgenie/data
LOGS_PATH=/volume1/docker/backupgenie/logs
BACKUP_BASE_PATH=/volume1/docker/backupgenie/backup

# Ports (DSM belegt oft 5000/5001!)
API_PORT=5050
FRONTEND_PORT=3080

# Credentials
GITHUB_TOKEN=ghp_dein_token
# SUPABASE_DB_PASSWORD=...
# SUPABASE_SERVICE_ROLE_KEY=...
```

#### 4. In Portainer den Stack anlegen

**Portainer** → **Stacks** → **Add Stack**:

| Feld | Wert |
|------|------|
| **Name** | `backupgenie` |
| **Build method** | Repository |
| **Repository URL** | `https://github.com/hehljo/BackupGenie` |
| **Repository reference** | `refs/heads/main` |
| **Compose path** | `docker-compose.yml` |
| **Env variables** | Aus `.env` übertragen (Advanced mode) |

→ **Deploy the stack**

#### 5. Web UI öffnen

```
http://diskstation-ip:3080
```

**Login:** `admin` / `AdminPassword123!` (sofort ändern!)

#### Variante B: Docker Compose direkt via SSH

```bash
cd /volume1/docker/backupgenie
# Repo klonen
git clone https://github.com/hehljo/BackupGenie.git /tmp/backupgenie-repo
# docker-compose.yml von dort starten
docker compose -f /tmp/backupgenie-repo/docker-compose.yml --env-file .env up -d
docker compose logs -f
```

#### Updates durchführen

Daten bleiben erhalten, nur das Stack-Image wird aktualisiert:

In **Portainer** → Stack `backupgenie` → **Editor** → **Update the stack** → **Re-pull image and redeploy**

Oder via SSH:
```bash
docker compose pull && docker compose up -d
```

#### Synology-spezifische Hinweise

- **Ports:** DSM belegt 5000 (HTTP) und 5001 (HTTPS) - daher `API_PORT=5050` und `FRONTEND_PORT=3080` empfohlen
- **SMB/NFS Backups:** Funktioniert, da `SYS_ADMIN` Capability gesetzt ist
- **Autostart nach Reboot:** Durch `restart: unless-stopped` automatisch
- **Berechtigungen:** Falls Permission-Fehler, Ordner mit `sudo chown -R 1000:1000 /volume1/docker/backupgenie/` anpassen

</details>

### 🐧 Linux Server / VPS

<details>
<summary>Schritt-für-Schritt Anleitung</summary>

#### 1. Docker installieren (falls noch nicht vorhanden)

```bash
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker $USER
# Neu einloggen damit Gruppenänderung greift
```

#### 2. BackupGenie installieren

```bash
cd /opt
sudo git clone https://github.com/hehljo/BackupGenie.git
sudo chown -R $USER:$USER BackupGenie
cd BackupGenie

cp config/example.env .env
cp config/sources-example.json config/sources.json
```

#### 3. Konfigurieren

```bash
nano .env
```
```bash
SECRET_KEY=$(openssl rand -base64 32)
BACKUP_BASE_PATH=/mnt/backups
```

#### 4. Starten

```bash
docker compose up -d
docker compose ps
```

#### 5. Web UI öffnen

```
http://server-ip:3000
```

</details>

### 🥧 Raspberry Pi

<details>
<summary>Schritt-für-Schritt Anleitung</summary>

#### 1. System vorbereiten

```bash
sudo apt update && sudo apt upgrade -y

# Docker installieren
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker pi

# Für USB Auto-Trigger (optional)
sudo apt install -y usbmount

sudo reboot
```

#### 2. BackupGenie installieren

```bash
cd /opt
sudo git clone https://github.com/hehljo/BackupGenie.git
sudo chown -R pi:pi BackupGenie
cd BackupGenie

cp config/example.env .env
cp config/sources-example.json config/sources.json
```

#### 3. Konfigurieren

```bash
nano .env
```
```bash
SECRET_KEY=ein_langer_zufaelliger_string
BACKUP_BASE_PATH=/mnt/backup

# Pi 3 mit wenig RAM: Limits anpassen
# BACKEND_MEMORY_LIMIT=512M
# BACKEND_CPU_LIMIT=1.5
# FRONTEND_MEMORY_LIMIT=128M
```

#### 4. Starten

```bash
docker compose up -d
```

#### 5. Web UI öffnen

```
http://raspberrypi.local:3000
```

#### USB Auto-Trigger einrichten (optional)

USB-Festplatte einstecken → Backup startet automatisch:

```bash
# udev-Regel erstellen
sudo nano /etc/udev/rules.d/99-backupgenie-backup.rules
```
```
ACTION=="add", KERNEL=="sd[a-z][0-9]", TAG+="systemd", ENV{SYSTEMD_WANTS}="backupgenie-backup@%k.service"
```
```bash
sudo udevadm control --reload-rules
```

Detaillierte Anleitung: [USB Auto-Trigger →](#usb-auto-trigger)

</details>

### 🐳 Docker (Generic)

<details>
<summary>Für jede Plattform mit Docker</summary>

```bash
git clone https://github.com/hehljo/BackupGenie.git
cd BackupGenie
cp config/example.env .env
cp config/sources-example.json config/sources.json

# .env anpassen
nano .env

# Starten
docker compose up -d

# Web UI: http://localhost:3000
```

#### Portainer (ohne Synology)

In Portainer → Stacks → Add Stack → Web editor:
1. `docker-compose.yml` Inhalt einfügen
2. Environment Variables setzen (mindestens `SECRET_KEY`)
3. Deploy

#### Umgebungsvariablen für Ressourcen-Anpassung

| Variable | Default | Beschreibung |
|----------|---------|-------------|
| `PLATFORM_PROFILE` | `auto` | `auto`, `raspberrypi`, `synology`, `server` |
| `BACKEND_CPU_LIMIT` | `2.0` | CPU-Limit Backend |
| `BACKEND_MEMORY_LIMIT` | `1G` | RAM-Limit Backend |
| `FRONTEND_CPU_LIMIT` | `1.0` | CPU-Limit Frontend |
| `FRONTEND_MEMORY_LIMIT` | `256M` | RAM-Limit Frontend |
| `MAX_PARALLEL_TASKS` | `auto` | Parallele Backup-Tasks (auto = basierend auf RAM) |

</details>

### Initial Configuration

> [!IMPORTANT]
> `SECRET_KEY` in `.env` muss vor dem ersten Start gesetzt werden!

**.env Übersicht:**

```bash
# Server
SECRET_KEY=CHANGE_THIS          # Pflicht! Langer zufälliger String
FLASK_ENV=production
DEBUG=false

# Ports
API_PORT=5000
FRONTEND_PORT=3000

# Backup
BACKUP_BASE_PATH=/mnt/backup    # Pfad wo Backups gespeichert werden
MAX_PARALLEL_TASKS=auto          # auto = wird anhand RAM berechnet

# Platform (optional)
PLATFORM_PROFILE=auto            # auto|raspberrypi|synology|server

# Credentials (je nach genutzten Backup-Quellen)
# GITHUB_TOKEN=ghp_xxx
# SUPABASE_DB_PASSWORD=xxx
# SUPABASE_SERVICE_ROLE_KEY=xxx
# NAS_PASSWORD_1=xxx
```

**Default Login:** `admin` / Passwort in den Logs: `docker compose logs backend | grep "password"`

### 💾 Data Persistence (Docker Volumes)

> [!NOTE]
> **Alle Ihre Daten bleiben nach einer Neuinstallation erhalten!**

BackupGenie nutzt Docker Volumes für persistente Datenspeicherung. Bei Updates oder Neuinstallationen bleiben folgende Daten automatisch erhalten:

**Persistente Verzeichnisse:**

```yaml
./config/         # ✅ Alle Backup-Quellen (sources.json)
                  # ✅ rclone Konfiguration
                  # ✅ Notification-Einstellungen

./data/           # ✅ Datenbank (User, Historie, Settings)
                  # ✅ Backup-Logs
                  # ✅ Metadaten

./logs/           # ✅ Anwendungs-Logs

/mnt/backup/      # ✅ Ihre Backup-Daten (konfigurierbar)
```

**Vorteile:**
- 🔄 **Sichere Updates:** `docker compose pull && docker compose up -d`
- 💾 **Backup-fähig:** Einfach `./config/` und `./data/` sichern
- 🚀 **Migration:** Ordner kopieren → neue Installation → fertig!
- ⚡ **Rollback:** Alte Container-Version starten ohne Datenverlust

**Vollständiges Backup erstellen:**

```bash
# BackupGenie Konfiguration sichern
cd /opt/BackupGenie
tar -czf backupgenie-config-$(date +%Y%m%d).tar.gz config/ data/ .env

# Backup an sicheren Ort kopieren
cp backupgenie-config-*.tar.gz /mnt/external-drive/
```

**Nach Neuinstallation wiederherstellen:**

```bash
# Neue Installation
cd /opt
git clone https://github.com/hehljo/BackupGenie.git
cd BackupGenie

# Backup wiederherstellen
tar -xzf /mnt/external-drive/backupgenie-config-*.tar.gz

# Container starten - alle Einstellungen sind da!
docker compose up -d
```

**Export/Import über Web-UI:**

Seit v1.1 können Sie alle Einstellungen auch direkt über die Web-Oberfläche exportieren/importieren:

1. **Settings** → **Configuration Export/Import**
2. **Export** → Lädt JSON-Datei mit allen Quellen & Einstellungen herunter
3. **Import** → Wählen Sie JSON-Datei aus und stellen Sie Ihre Konfiguration wieder her

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
<summary>🐙 GitHub Repositories (Auto-Discovery)</summary>

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

**`discovery_mode`**: `"all"` sichert automatisch alle Repos (private + public + Orgs). Neue Repos werden beim nächsten Backup automatisch erkannt. Alternativ `"manual"` für manuelle Auswahl über die Web UI.

**Generate token:** GitHub → Settings → Developer settings → Personal access tokens → Scopes: `repo`, `gist`

</details>

<details>
<summary>🟢 Supabase (DB + Storage)</summary>

```json
{
  "id": "supabase-project",
  "name": "Supabase Production",
  "type": "supabase",
  "enabled": true,
  "priority": 3,
  "project_ref": "your-project-ref",
  "region": "aws-0-eu-central-1",
  "backup_mode": "full",
  "credentials": {
    "db_password_env": "SUPABASE_DB_PASSWORD",
    "service_role_key_env": "SUPABASE_SERVICE_ROLE_KEY"
  },
  "options": {
    "include_storage": true,
    "include_auth_config": true,
    "compress": true
  }
}
```

**`backup_mode`**: `"full"` sichert DB (roles + schema + data) + Storage Buckets + RLS/Auth Config. `"db_only"` für nur PostgreSQL Dumps.

**Restore-Anleitung:** [docs/SUPABASE_RESTORE.md](docs/SUPABASE_RESTORE.md)

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

Configure automatic backup triggering when USB drive is connected:

<details>
<summary>Setup udev + systemd</summary>

#### 1. Create udev rule

```bash
sudo nano /etc/udev/rules.d/99-backupgenie-backup.rules
```

```bash
# Trigger backup when USB device is added
ACTION=="add", KERNEL=="sd[a-z][0-9]", TAG+="systemd", ENV{SYSTEMD_WANTS}="backupgenie-backup@%k.service"
```

#### 2. Create systemd service

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

#### 3. Create trigger script

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

> [!WARNING]
> Never commit credentials to version control!

Store sensitive credentials in `.env.secrets`:

```bash
# Create secrets file
nano .env.secrets

# Add credentials
NAS_PASSWORD=YourSecurePassword
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxx
RCLONE_CONFIG_GDRIVE_TOKEN=...

# Set secure permissions
chmod 600 .env.secrets
```

Load in `docker-compose.yml`:
```yaml
services:
  backend:
    env_file:
      - .env
      - .env.secrets
```

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
- 🌍 Language switcher (DE/EN)

### API Usage

<details>
<summary>Start backup via API</summary>

```bash
# Get API token
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}' \
  | jq -r '.access_token')

# Start backup
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
# Start backup for specific sources
docker exec backupgenie-backend python -m app.backup.executor \
  --source github-repos --source nas-project1

# List all configured sources
docker exec backupgenie-backend python -m app.cli sources list

# Test source connection
docker exec backupgenie-backend python -m app.cli sources test nas-project1

# View backup history
docker exec backupgenie-backend python -m app.cli backup history --limit 10

# Clean old backups
docker exec backupgenie-backend python -m app.cleanup --days 30
```

---

## 🌍 Internationalization (i18n)

BackupGenie provides full multi-language support:

### Supported Languages
- 🇩🇪 **Deutsch** - Vollständig übersetzt
- 🇬🇧 **English** - Fully translated

### Language Selection
- **Frontend**: Language switcher in sidebar header
- **Backend**: Auto-detection via `Accept-Language` header
- **Storage**: Preference saved in browser localStorage

### Add New Languages

See detailed guide: **[i18n Documentation →](docs/i18n.md)**

**Quick Steps:**
1. Frontend: Create `frontend/src/locales/{lang}/translation.json`
2. Backend: Run `pybabel init -d app/translations -l {lang}`
3. Translate `.po` files
4. Compile: `pybabel compile -d app/translations`

**Technology Stack:**
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
<summary>📦 Backup Management</summary>

#### Start Backup
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

#### Get Backup Status
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

#### List Backup History
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
<summary>🔧 Source Management</summary>

#### List Sources
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

#### Add Source
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

#### Update Source
```http
PUT /api/v1/sources/{source_id}
Authorization: Bearer TOKEN
Content-Type: application/json

{
  "enabled": false
}
```

#### Delete Source
```http
DELETE /api/v1/sources/{source_id}
Authorization: Bearer TOKEN
```

</details>

📚 **[Complete API Documentation →](docs/API.md)**

---

## 🐛 Troubleshooting

<details>
<summary>🚫 Docker containers won't start</summary>

```bash
# Check logs
docker compose logs backend
docker compose logs frontend

# Rebuild containers
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

# Test from Docker
docker exec backupgenie-backend smbclient -L //192.168.1.100 -U backup_user

# Verify credentials
cat /etc/backupgenie/credentials
```

</details>

<details>
<summary>🔑 GitHub token invalid</summary>

```bash
# Verify token online
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user

# Update token
nano .env.secrets
docker compose restart backend
```

</details>

<details>
<summary>💽 Disk space full</summary>

```bash
# Check available space
df -h /mnt/backup

# Find largest files
du -sh /mnt/backup/* | sort -rh | head -20

# Clean old backups
docker exec backupgenie-backend python -m app.cleanup --days 30
```

</details>

📚 **[More Troubleshooting →](docs/TROUBLESHOOTING.md)**

---

## 🔒 Security

> [!IMPORTANT]
> Follow security best practices to protect your backup data!

### SSH Hardening

<details>
<summary>Setup secure SSH access</summary>

```bash
# Generate ED25519 key pair (locally)
ssh-keygen -t ed25519 -o -a 100 -f ~/.ssh/backupgenie

# Copy public key to Raspberry Pi
ssh-copy-id -i ~/.ssh/backupgenie.pub pi@raspberrypi.local

# Configure SSH server
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

### Firewall Configuration

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

### API Token Management

```bash
# Generate long-lived API token
docker exec backupgenie-backend python -c "
from app.auth import generate_token
token = generate_token('backup-automation', expires_days=365)
print(f'Token: {token}')
"

# Store securely
sudo mkdir -p /etc/backupgenie
echo 'YOUR_TOKEN' | sudo tee /etc/backupgenie/api-token > /dev/null
sudo chmod 600 /etc/backupgenie/api-token
sudo chown pi:pi /etc/backupgenie/api-token
```

### Encrypt Credentials

```bash
# Install GPG
sudo apt install gpg -y

# Encrypt credentials file
gpg -c /etc/backupgenie/credentials

# Securely delete original
sudo shred -vfz /etc/backupgenie/credentials

# Decrypt in Docker entrypoint
gpg --batch --yes --passphrase-file=/run/secrets/gpg_pass \
    -o /tmp/creds.txt \
    /etc/backupgenie/credentials.gpg
```

📚 **[Security Best Practices →](docs/SECURITY.md)**

---

## 👨‍💻 Development

### Project Structure

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

### Local Development Setup

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run backend
flask run --debug

# Frontend
cd frontend
npm install
npm run dev
```

### Running Tests

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

### Build Docker Images

```bash
# Build all services
docker compose build

# Build specific service
docker compose build backend

# Build for ARM (Raspberry Pi)
docker buildx build --platform linux/arm/v7,linux/arm64 -t backupgenie-backend:latest .
```

📚 **[Development Guide →](docs/DEVELOPMENT.md)**

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### How to Contribute

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines

- Follow [PEP 8](https://pep8.org/) for Python code
- Follow [Airbnb Style Guide](https://github.com/airbnb/javascript) for JavaScript
- Write tests for new features
- Update documentation for API changes
- Add i18n translations for new UI strings

### Code of Conduct

This project adheres to the Contributor Covenant [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

## 🎯 Roadmap

- [ ] **Web UI Enhancements**
  - [ ] Dark/Light theme toggle
  - [ ] Advanced filtering in backup history
  - [ ] Backup scheduling calendar view
- [ ] **Notifications**
  - [ ] Email notifications
  - [ ] Webhook support
  - [ ] Telegram bot integration
- [ ] **Security**
  - [ ] Encryption at rest
  - [ ] Two-factor authentication (2FA)
  - [ ] Audit logging
- [ ] **Performance**
  - [ ] Deduplication support
  - [ ] Incremental backup optimization
  - [ ] Multi-threaded compression
- [ ] **Features**
  - [ ] Backup verification/validation
  - [ ] Restore functionality via UI
  - [ ] Prometheus metrics export
  - [ ] REST API v2 with OpenAPI 3.0 spec
- [ ] **Languages**
  - [ ] 🇫🇷 French
  - [ ] 🇪🇸 Spanish
  - [ ] 🇮🇹 Italian

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 BackupGenie Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

## 📞 Support & Community

<div align="center">

**Need help? Have questions?**

[![GitHub Issues](https://img.shields.io/github/issues/hehljo/BackupGenie?style=for-the-badge)](https://github.com/hehljo/BackupGenie/issues)
[![GitHub Discussions](https://img.shields.io/github/discussions/hehljo/BackupGenie?style=for-the-badge)](https://github.com/hehljo/BackupGenie/discussions)

[Report Bug](https://github.com/hehljo/BackupGenie/issues/new?template=bug_report.md) • [Request Feature](https://github.com/hehljo/BackupGenie/issues/new?template=feature_request.md) • [Ask Question](https://github.com/hehljo/BackupGenie/discussions)

---

### ☕ Support This Project

If BackupGenie helps you manage your backups, consider supporting the development!

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support%20Development-yellow?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white)](https://buymeacoffee.com/pommesbude)

Your support helps keep this project alive and growing! 🙏

</div>

### Resources

- 📚 **[Full Documentation](docs/)**
- 🔌 **[API Reference](docs/API.md)**
- 🌐 **[i18n Guide](docs/i18n.md)**
- 🐞 **[Troubleshooting](docs/TROUBLESHOOTING.md)**
- 🔐 **[Security Policy](SECURITY.md)**

---

<div align="center">

**Made with ❤️ by the BackupGenie Community**

⭐ **Star this repo if BackupGenie helps you!** ⭐

[🏠 Home](https://github.com/hehljo/BackupGenie) • [📖 Docs](docs/) • [🐛 Issues](https://github.com/hehljo/BackupGenie/issues) • [💬 Discussions](https://github.com/hehljo/BackupGenie/discussions)

</div>
