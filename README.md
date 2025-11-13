<div align="center">

# 🧞 BackupGenie

### Automated Multi-Source Backup Manager for Raspberry Pi

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-20.10%2B-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-green.svg)](https://nodejs.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**[Features](#-features)** • **[Quick Start](#-quick-start)** • **[Documentation](docs/)** • **[API Docs](#-api-documentation)** • **[Contributing](CONTRIBUTING.md)**

---

Ein selbstgehostetes Backup-System für Raspberry Pi mit moderner Weboberfläche zur automatischen Synchronisierung von 60+ Quellen (NAS, GitHub, Cloud-Services, Docker, Self-Hosted Apps) auf externe USB-Festplatten.

[🇩🇪 Deutsch](#) • [🇬🇧 English](README.en.md)

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🔄 60+ Backup Sources
- **Network Storage**: NAS (SMB/NFS), rsync over SSH
- **Git Platforms**: GitHub, GitLab, Bitbucket, Gitea
- **Databases**: MySQL, PostgreSQL, MongoDB, Redis
- **Cloud Storage**: Google Drive, Dropbox, OneDrive, S3
- **Self-Hosted**: Nextcloud, Plex, Home Assistant, Vaultwarden
- **Docker**: Volumes, Containers, Images
- **Local**: Filesystems, Home Directories

📚 [Vollständige Quellenliste →](docs/BACKUP_SOURCES.md)

</td>
<td width="50%">

### 🎯 Smart Automation
- ⚡ **USB-Trigger**: Automatischer Start beim Einstecken
- 🌐 **Modern Web UI**: React-basierte SPA
- 🔐 **Secure**: SSH-Key Auth, SSL/TLS, RBAC
- 📊 **Real-time Monitoring**: Live Dashboard & Logs
- 🐳 **Docker-based**: One-command deployment
- 🥧 **Raspberry Pi optimized**: ARM-compatible
- 🌍 **Multi-Language**: 🇩🇪 German & 🇬🇧 English

</td>
</tr>
</table>

---

## 🚀 Quick Start

> [!NOTE]
> Requires Raspberry Pi 3/4/5 with 2GB+ RAM and Docker installed.

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
open http://raspberrypi.local:3000
```

**Default Login**: `admin` / Check logs: `docker compose logs backend | grep "Initial password"`

---

## 📋 Table of Contents

<details open>
<summary>Click to expand</summary>

- [Requirements](#-requirements)
- [Installation](#-installation)
  - [Raspberry Pi Setup](#raspberry-pi-setup)
  - [Docker Installation](#docker-installation)
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
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Board** | Raspberry Pi 3 | Raspberry Pi 4/5 |
| **RAM** | 2 GB | 4 GB |
| **Storage** | 16 GB microSD | 32 GB+ microSD |
| **Network** | WLAN | Ethernet |
| **USB** | USB 2.0 Drive | USB 3.0+ SSD |

### Software
```
OS:      Raspberry Pi OS (Lite or Desktop)
Docker:  20.10+
Compose: 2.0+
Python:  3.9+
Node.js: 18+
```

### Authentication Requirements
- 🔑 **NAS**: SMB/NFS credentials
- 🔑 **GitHub**: Personal Access Token
- 🔑 **Cloud**: OAuth2 credentials or API keys
- 🔑 **SSH**: Private key for rsync

---

## 🚀 Installation

### Raspberry Pi Setup

<details>
<summary>Expand for detailed steps</summary>

#### 1. System Update

```bash
sudo apt update && sudo apt upgrade -y
```

#### 2. Install Docker & Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker pi

# Install Docker Compose Plugin
sudo apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

#### 3. Install Dependencies

```bash
sudo apt install -y \
    git \
    curl \
    rsync \
    rclone \
    git-lfs \
    openssh-client \
    usbmount
```

#### 4. Reboot

```bash
sudo reboot
```

</details>

### Docker Installation

```bash
# Clone repository
cd /opt
sudo git clone https://github.com/hehljo/BackupGenie.git
sudo chown -R $USER:$USER BackupGenie
cd BackupGenie

# Copy configuration templates
cp config/example.env .env
cp config/sources-example.json config/sources.json

# Edit configuration
nano .env

# Start services
docker compose up -d

# Check status
docker compose ps
docker compose logs -f
```

### Initial Configuration

> [!IMPORTANT]
> Generate a secure `SECRET_KEY` before first run!

**.env Configuration:**

```bash
# Server
FLASK_ENV=production
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
DEBUG=false

# Database
DATABASE_URL=sqlite:////data/backupgenie.db

# Backup
BACKUP_BASE_PATH=/mnt/backup
MAX_PARALLEL_TASKS=2
LOG_RETENTION_DAYS=30

# API
API_PORT=5000
API_HOST=0.0.0.0

# Frontend
FRONTEND_PORT=3000

# Language (de or en)
DEFAULT_LANGUAGE=de
```

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
<summary>🐙 GitHub Repositories</summary>

```json
{
  "id": "github-repos",
  "name": "GitHub Repositories",
  "type": "github",
  "enabled": true,
  "priority": 2,
  "repositories": ["user/repo1", "user/repo2"],
  "credentials": {
    "token_env": "GITHUB_TOKEN"
  },
  "options": {
    "include_issues": false,
    "include_wikis": true,
    "include_lfs": true
  },
  "schedule": {
    "trigger": "usb_mount",
    "max_duration": 600
  }
}
```

**Generate token:** GitHub → Settings → Developer settings → Personal access tokens → Scopes: `repo`, `gist`

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
