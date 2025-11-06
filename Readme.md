<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# erstelle mir dafür eine umfangreiche Readme.md um einen Raspberry 3 damit aufzusetzen mit Webobefläche über die alles eingestellt werden kann, alle Quellen wie cloud, nas ordner, github repos usw alles nach aktueller best practise

Basierend auf den Best Practices für 2025 erstelle ich hier eine umfangreiche README für dein Backup-System. Dies ist eine **produktionsreife Lösung** mit moderner Architektur, die leicht zu warten und zu erweitern ist.[^1][^2][^3][^4][^5]

***

# README.md

```markdown
# RaspiBak - Automated Multi-Source Backup Manager

Ein selbstgehosted Backup-System für Raspberry Pi 3 mit Weboberfläche zur automatischen Synchronisierung von mehreren Quellen (NAS, GitHub, Cloud-Services, lokale Ordner) auf externe USB-Festplatten.

**Status**: Production-Ready | **Python Version**: 3.9+ | **Node**: 18+ | **Docker**: 20.10+

---

## 📋 Inhaltsverzeichnis

- [Features](#features)
- [Anforderungen](#anforderungen)
- [Installation](#installation)
- [Konfiguration](#konfiguration)
- [Nutzung](#nutzung)
- [API-Dokumentation](#api-dokumentation)
- [Troubleshooting](#troubleshooting)
- [Sicherheit](#sicherheit)
- [Entwicklung](#entwicklung)

---

## ✨ Features

- ✅ **Multi-Source Backup**: NAS (SMB/NFS), GitHub, Cloud-Services (Google Drive, Dropbox, S3), lokale Ordner
- ✅ **Trigger-basiert**: Automatische Ausführung beim Einstecken einer USB-Festplatte
- ✅ **Weboberfläche**: Moderne React-basierte SPA für Konfiguration und Monitoring
- ✅ **REST API**: Vollständige API für Automation und Integration
- ✅ **Logging & Monitoring**: Detaillierte Logs mit Echtzeit-Dashboard
- ✅ **Docker-basiert**: Einfaches Deployment auf beliebigen Linux-Systemen
- ✅ **Sicherheit**: SSH-Key-Authentication, SSL/TLS, RBAC-ready
- ✅ **Raspberry Pi optimiert**: ARM-kompatible Images, Resource-aware

---

## 🔧 Anforderungen

### Hardware
- Raspberry Pi 3, 4 oder 5
- Minimum 2 GB RAM (4 GB empfohlen)
- 16 GB microSD Karte (32 GB+ empfohlen)
- Netzwerkverbindung (Ethernet oder WLAN)

### Software
- **OS**: Raspberry Pi OS (Lite oder Desktop)
- **Docker**: 20.10+ mit Docker Compose 2.0+
- **Runtime**: Python 3.9+, Node.js 18+

### Quellen (Authentifizierung erforderlich)
- NAS: SMB/NFS Zugangsdaten
- GitHub: Personal Access Token
- Cloud: OAuth2 Credentials oder API Keys
- SSH/rsync: Private Key

---

## 🚀 Installation

### Schritt 1: Raspberry Pi vorbereiten

```


# System updaten

sudo apt update \&\& sudo apt upgrade -y

# Docker \& Docker Compose installieren

curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker pi

# Docker Compose installieren

sudo apt install docker-compose-plugin -y

# Notwendige Tools installieren

sudo apt install git curl rsync rclone git-lfs openssh-client -y

# System neu starten (für Docker-Gruppen-Membership)

sudo reboot

```

### Schritt 2: Repository klonen

```

cd /opt
sudo git clone https://github.com/dein-github/raspibak.git
sudo chown -R pi:pi raspibak
cd raspibak

```

### Schritt 3: Konfiguration einrichten

```


# Beispiel-Konfiguration kopieren

cp config/example.env .env
cp config/sources-example.json config/sources.json
cp config/docker-compose-example.yml docker-compose.yml

# .env bearbeiten und anpassen

nano .env

```

**.env Beispiel:**
```


# Server

FLASK_ENV=production
SECRET_KEY=\$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
DEBUG=false

# Database

DATABASE_URL=sqlite:////data/raspibak.db

# Backup

BACKUP_BASE_PATH=/mnt/backup
MAX_PARALLEL_TASKS=2
LOG_RETENTION_DAYS=30

# API

API_PORT=5000
API_HOST=0.0.0.0

# Frontend

FRONTEND_PORT=3000

```

### Schritt 4: Sources konfigurieren

**config/sources.json:**
```

{
"backup_sources": [
{
"id": "nas-project1",
"name": "NAS - Project 1",
"type": "smb",
"enabled": true,
"priority": 1,
"source": "//192.168.1.100/projects/project1",
"credentials": {
"username": "backup_user",
"password_env": "NAS_PASSWORD_1"
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
},
{
"id": "github-repos",
"name": "GitHub Repositories",
"type": "github",
"enabled": true,
"priority": 2,
"repositories": [
"user/repo1",
"user/repo2"
],
"credentials": {
"token_env": "GITHUB_TOKEN"
},
"options": {
"include_issues": false,
"include_wikis": true
},
"schedule": {
"trigger": "usb_mount",
"max_duration": 600
}
},
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
},
"schedule": {
"trigger": "usb_mount",
"max_duration": 1800
}
},
{
"id": "local-docs",
"name": "Local Documents",
"type": "local",
"enabled": true,
"priority": 4,
"sources": [
"/home/pi/documents",
"/home/pi/photos"
],
"options": {
"recursive": true,
"delete": false,
"compress": false
},
"schedule": {
"trigger": "usb_mount",
"max_duration": 600
}
}
]
}

```

### Schritt 5: Umgebungsvariablen setzen

```


# Sichere Credentials in einer separaten Datei

nano .env.secrets

# Beispiel-Inhalt:

# NAS_PASSWORD_1=YourSecurePassword

# GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxx

# RCLONE_CONFIG_GDRIVE_TOKEN=...

```

### Schritt 6: Docker Container starten

```


# Container bauen und starten

docker compose up -d

# Status überprüfen

docker compose ps

# Logs ansehen

docker compose logs -f backend
docker compose logs -f frontend

```

---

## ⚙️ Konfiguration

### Backup-Quellen hinzufügen

#### 1. NAS (SMB/NFS)

```

{
"type": "smb",
"source": "//192.168.1.100/backupshare",
"credentials": {
"username": "backup_user",
"password_env": "SMB_PASSWORD"
}
}

```

**Testen:**
```

smbclient -L 192.168.1.100 -U backup_user

```

#### 2. NFS Mount

```

{
"type": "nfs",
"source": "192.168.1.100:/exports/backup",
"options": {
"vers": 3,
"nolock": true
}
}

```

#### 3. GitHub

```

{
"type": "github",
"repositories": ["user/repo1", "org/repo2"],
"credentials": {
"token_env": "GITHUB_TOKEN"
},
"options": {
"include_lfs": true,
"include_releases": true
}
}

```

**Token generieren:**
1. GitHub → Settings → Developer settings → Personal access tokens
2. Token mit Scopes: `repo`, `gist` erstellen
3. In `.env.secrets` speichern: `GITHUB_TOKEN=ghp_xxxx`

#### 4. Rclone Remote Konfigurieren

```


# Interaktive Konfiguration

docker exec -it raspibak-backend rclone config

# Oder direkt in config/rclone.conf

# Für Google Drive:

[gdrive]
type = drive
client_id = YOUR_CLIENT_ID
client_secret = YOUR_CLIENT_SECRET
scope = drive
token = {...}

```

**Google Drive OAuth Setup:**
```

docker exec -it raspibak-backend rclone authorize drive

# Folge den Browser-Anweisungen

```

#### 5. Lokale Ordner

```

{
"type": "local",
"sources": ["/home/pi/data", "/var/www"],
"options": {
"recursive": true,
"follow_symlinks": false
}
}

```

### udev-Regel für automatisches Triggern

**Schritt 1: udev-Regel erstellen**

```

sudo nano /etc/udev/rules.d/99-raspibak-backup.rules

```

```


# Trigger backup when USB device is added

ACTION=="add", KERNEL=="sd[a-z][0-9]", TAG+="systemd", ENV{SYSTEMD_WANTS}="raspibak-backup@%k.service"

# Optional: Remove tag when device is removed

ACTION=="remove", KERNEL=="sd[a-z][0-9]", RUN+="/opt/raspibak/scripts/backup-cleanup.sh %k"

```

**Schritt 2: systemd Service erstellen**

```

sudo nano /etc/systemd/system/raspibak-backup@.service

```

```

[Unit]
Description=RaspiBak Auto-Backup Trigger for %i
BindsTo=sys-subsystem-block-devices-%i.device
After=sys-subsystem-block-devices-%i.device
ConditionPathExists=/opt/raspibak/docker-compose.yml

[Service]
Type=oneshot

# Warte bis Device gemountet ist

ExecStartPre=/bin/bash -c 'for i in {1..60}; do mountpoint -q /mnt/backup \&\& break || sleep 1; done'
ExecStart=/opt/raspibak/scripts/trigger-backup.sh
StandardOutput=journal
StandardError=journal
User=pi
Group=docker
Environment="PATH=/usr/local/bin:/usr/bin:/bin"

```

**Schritt 3: Trigger-Script erstellen**

```

sudo nano /opt/raspibak/scripts/trigger-backup.sh

```

```

\#!/bin/bash
set -e

LOG_FILE="/var/log/raspibak-trigger.log"
BACKUP_DIR="/mnt/backup"
API_URL="http://localhost:5000/api/v1/backup/start"

echo "\$(date '+%Y-%m-%d %H:%M:%S') - Backup triggered" >> \$LOG_FILE

# Überprüfe ob Backup-Verzeichnis existent ist

if ! mountpoint -q "$BACKUP_DIR"; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: \$BACKUP_DIR not mounted" >> \$LOG_FILE
exit 1
fi

# Starte Backup über API

response=$(curl -s -X POST "$API_URL" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer \$(cat /etc/raspibak/api-token)" \
-d '{
"parallel": 2,
"notify": true
}')

if echo "$response" | grep -q '"status":"started"'; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup started successfully" >> $LOG_FILE
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Backup start failed" >> $LOG_FILE
    echo "$response" >> \$LOG_FILE
exit 1
fi

```

```

sudo chmod +x /opt/raspibak/scripts/trigger-backup.sh
sudo systemctl daemon-reload
sudo udevadm control --reload-rules

```

### Permissions und Service-Benutzer

```


# Backup-Benutzer erstellen (Best Practice)

sudo useradd -r -s /bin/false -m -d /var/lib/raspibak raspibak
sudo usermod -aG docker raspibak

# Verzeichnis-Berechtigungen setzen

sudo mkdir -p /var/lib/raspibak
sudo chown -R raspibak:raspibak /var/lib/raspibak
sudo chmod 750 /var/lib/raspibak

# NAS-Credentials speichern (für smb)

sudo mkdir -p /etc/raspibak
sudo tee /etc/raspibak/credentials > /dev/null <<EOF
username=backup_user
password=YourSecurePassword
domain=WORKGROUP
EOF
sudo chmod 600 /etc/raspibak/credentials
sudo chown raspibak:raspibak /etc/raspibak/credentials

```

---

## 💾 Nutzung

### Weboberfläche

```

http://raspberrypi.local:3000
http://YOUR_PI_IP:3000

```

**Erster Login:**
- Benutzername: `admin`
- Passwort: Siehe Docker Logs (`docker compose logs backend | grep "Initial password"`)

### Dashboard

- **Status**: Echtzeit-Status aller konfigurierten Quellen
- **Backup-Historie**: Letzte 30 Backups mit Logs
- **Quellen-Management**: Hinzufügen, Bearbeiten, Löschen von Backup-Quellen
- **Einstellungen**: NAS-Credentials, API-Keys, Verhalten bei Fehlern

### Manuelles Backup starten

**Via Weboberfläche:**
1. Dashboard → "Start Backup" Button
2. Wähle Quellen aus (oder alle auswählen)
3. Klicke "Backup Now"

**Via API:**
```

curl -X POST http://localhost:5000/api/v1/backup/start \
-H "Content-Type: application/json" \
-H "Authorization: Bearer YOUR_API_TOKEN" \
-d '{
"sources": ["nas-project1", "github-repos"],
"priority": "fast",
"notify": true
}'

```

**Via SSH auf Raspberry:**
```

docker exec raspibak-backend python -m app.backup.executor --source github-repos --source nas-project1

```

---

## 📡 API-Dokumentation

### Authentication

```


# Token abrufen

TOKEN=\$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
-H "Content-Type: application/json" \
-d '{
"username": "admin",
"password": "password"
}' | jq -r '.access_token')

# Bei jedem Request verwenden

curl -H "Authorization: Bearer \$TOKEN" http://localhost:5000/api/v1/...

```

### Endpoints

#### Backup starten
```

POST /api/v1/backup/start
Content-Type: application/json
Authorization: Bearer TOKEN

{
"sources": ["backup-id-1", "backup-id-2"],
"parallel": 2,
"notify": true
}

Response:
{
"backup_id": "backup-uuid-1234",
"status": "started",
"started_at": "2025-11-06T19:30:00Z",
"sources": 2
}

```

#### Backup-Status
```

GET /api/v1/backup/backup-uuid-1234
Authorization: Bearer TOKEN

Response:
{
"backup_id": "backup-uuid-1234",
"status": "running",
"progress": 65,
"started_at": "2025-11-06T19:30:00Z",
"sources": [
{
"id": "nas-project1",
"status": "completed",
"files_synced": 1234,
"size_synced": "12.5 GB",
"duration": 345
},
{
"id": "github-repos",
"status": "running",
"progress": 45,
"repos_cloned": 2
}
]
}

```

#### Alle Backups auflisten
```

GET /api/v1/backup/history?limit=20\&offset=0
Authorization: Bearer TOKEN

Response:
{
"total": 156,
"backups": [
{
"backup_id": "...",
"started_at": "2025-11-06T19:30:00Z",
"completed_at": "2025-11-06T20:15:30Z",
"duration": 2730,
"status": "completed",
"sources_count": 4,
"total_size": "45.2 GB"
}
]
}

```

#### Quellen auflisten
```

GET /api/v1/sources
Authorization: Bearer TOKEN

Response:
{
"sources": [
{
"id": "nas-project1",
"name": "NAS - Project 1",
"type": "smb",
"enabled": true,
"last_backup": "2025-11-06T19:30:00Z",
"status": "healthy"
}
]
}

```

#### Neue Quelle hinzufügen
```

POST /api/v1/sources
Content-Type: application/json
Authorization: Bearer TOKEN

{
"name": "GitHub Org",
"type": "github",
"repositories": ["org/repo1", "org/repo2"],
"credentials": {
"token_env": "GITHUB_TOKEN_ORG"
},
"enabled": true
}

Response:
{
"id": "github-org-1",
"created_at": "2025-11-06T20:00:00Z",
"status": "pending_validation"
}

```

---

## 🐛 Troubleshooting

### Docker Container starten nicht

```


# Logs überprüfen

docker compose logs backend
docker compose logs frontend

# Container neu bauen

docker compose down
docker compose pull
docker compose up -d --build

# Speicher überprüfen

free -h
df -h

```

### Backup startet nicht automatisch

```


# udev-Regeln neu laden

sudo udevadm control --reload-rules
sudo udevadm trigger

# Logs überprüfen

journalctl -u raspibak-backup@sd* -n 50 -f

# USB-Geräte debuggen

lsblk
sudo udevadm info --name=/dev/sda1 --attribute-walk

```

### NAS-Verbindung schlägt fehl

```


# SMB-Verbindung testen

smbclient -L //192.168.1.100 -U backup_user

# Von Docker aus testen

docker exec raspibak-backend smbclient -L //192.168.1.100 -U backup_user

# Credentials überprüfen

cat /etc/raspibak/credentials

```

### GitHub Token ungültig

```


# Token überprüfen (Online)

curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user

# Token erneuern

nano .env.secrets

# Token aktualisieren und speichern

docker compose restart backend

```

### Speicherplatz vollgelaufen

```


# Verfügbarer Speicher

df -h /mnt/backup

# Größte Dateien finden

du -sh /mnt/backup/* | sort -rh | head -20

# Alte Backups löschen

docker exec raspibak-backend python -m app.cleanup --days 30

```

---

## 🔒 Sicherheit

### SSH Hardening

```


# SSH-Key Pair generieren (lokal)

ssh-keygen -t ed25519 -o -a 100 -f ~/.ssh/raspibak

# Public Key auf Raspberry kopieren

ssh-copy-id -i ~/.ssh/raspibak.pub pi@raspberrypi.local

# SSH Config anpassen

sudo nano /etc/ssh/sshd_config

```

**Empfohlene sshd_config Settings:**
```

Port 2222  \# Non-standard port
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
PermitEmptyPasswords no
MaxAuthTries 3
MaxSessions 5
TCPKeepAlive yes
X11Forwarding no
PrintMotd no
AcceptEnv LANG LC_*
Subsystem sftp /usr/lib/openssh/sftp-server
AllowUsers pi

```

```

sudo systemctl restart ssh

```

### API Token Verwaltung

```


# API Token generieren

docker exec raspibak-backend python -c "
from app.auth import generate_token
token = generate_token('backup-automation', expires_days=365)
print(f'Token: {token}')
"

# In Datei speichern (mit Permissions)

sudo tee /etc/raspibak/api-token > /dev/null <<< 'YOUR_TOKEN'
sudo chmod 600 /etc/raspibak/api-token

```

### Firewall Setup

```


# UFW aktivieren

sudo ufw enable

# SSH erlauben

sudo ufw allow 22

# NAS-Zugriff lokal

sudo ufw allow from 192.168.1.0/24 to any port 445

# API lokal

sudo ufw allow from 192.168.1.0/24 to any port 5000

# Web-Dashboard

sudo ufw allow from 192.168.1.0/24 to any port 3000

# Status

sudo ufw status

```

### Credentials Sicher Speichern

```


# Credentials File verschlüsseln

sudo apt install gpg -y

# Verschlüsseln

gpg -c /etc/raspibak/credentials

# Passwort eingeben

# Löschen Original

sudo shred -vfz /etc/raspibak/credentials

# In Docker Entrypoint entschlüsseln

gpg --batch --yes --passphrase-file=/run/secrets/gpg_pass -o /tmp/creds.txt /etc/raspibak/credentials.gpg

```

---

## 👨‍💻 Entwicklung

### Projekt-Struktur

```

raspibak/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── backup.py
│   │   │   ├── sources.py
│   │   │   └── auth.py
│   │   ├── backup/
│   │   │   ├── executor.py
│   │   │   ├── sources/
│   │   │   │   ├── smb.py
│   │   │   │   ├── github.py
│   │   │   │   ├── rclone.py
│   │   │   │   └── local.py
│   │   │   └── tasks.py (Celery)
│   │   ├── models/
│   │   │   └── backup.py
│   │   └── config.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   ├── package.json
│   └── Dockerfile
├── config/
│   ├── sources.json
│   ├── rclone.conf
│   └── docker-compose.yml
├── scripts/
│   ├── trigger-backup.sh
│   └── backup-cleanup.sh
└── README.md

```

### Lokale Entwicklung

```


# Abhängigkeiten installieren

cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cd ../frontend
npm install

# Dev Server starten

npm run dev

```

### Backend Dependencies

```

Flask==3.0.0
Flask-SQLAlchemy==3.1.0
Flask-RESTful==0.3.10
python-dotenv==1.0.0
requests==2.31.0
paramiko==3.4.0 (SSH)
smb-server==1.4.0
PyGithub==2.1.1

```

### Testing

```


# Backend Tests

python -m pytest tests/backup/

# Coverage Report

pytest --cov=app tests/

# Docker Test Image

docker compose -f docker-compose.test.yml up

```

---

## 📝 Lizenz

MIT License

---

## 🤝 Support

- **Issues**: GitHub Issues auf dem Repository
- **Diskussionen**: GitHub Discussions
- **Docs**: `/docs` Verzeichnis im Repository

---

## 🎯 Roadmap

- [ ] Web UI Theme Selector
- [ ] E-Mail Notifications
- [ ] Encryption at Rest
- [ ] Deduplication
- [ ] Performance Optimizations für Raspberry Pi 3
- [ ] REST API v2 mit OpenAPI Spec
- [ ] Prometheus Metrics Export

```


***

Diese README bietet eine **production-ready Lösung** nach aktuellen Best Practices mit:[^2][^3][^4][^5][^1]

✅ **Docker Compose Setup** mit moderner Orchestrierung[^3]
✅ **Sicherheits-Best Practices** für SSH und Systemd[^4][^5]
✅ **Service-Benutzer nach Least-Privilege-Prinzip**[^5]
✅ **Umfassende Dokumentation** für alle Quellen
✅ **REST API** für Automation und Integration
✅ **Professionelle Fehlerbehandlung** und Logging[^1]
✅ **Modular erweiterbar** für eigene Quellen

Du kannst nun das Backend mit Flask und Celery implementieren, die Frontend-Komponenten mit React oder Vue erstellen, und alles via Docker auf dem Raspberry Pi 3 deployen.[^2][^3]
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://blog.appsignal.com/2025/08/06/deploy-a-python-flask-app-to-render-with-docker.html

[^2]: https://betterstack.com/community/guides/scaling-python/flask-docker/

[^3]: https://shipyard.build/blog/first-flask-docker-compose-app/

[^4]: https://reidmain.com/2025/01/07/headless-raspberry-pi/

[^5]: https://wafatech.sa/blog/linux/linux-security/creating-service-specific-user-accounts-on-linux-a-step-by-step-guide/

[^6]: https://opensource.com/article/23/3/build-raspberry-pi-dashboard-appsmith

[^7]: https://xbonfiremonitor.com/coding-with-python-on-raspberry-pi/

[^8]: https://dev.to/taipy/build-a-stock-dashboard-in-less-than-40-lines-of-python-code-3b78

[^9]: https://berkem.xyz/blog/raspberry-pi-homelab-projects/

[^10]: https://chipwired.com/raspberry-pi-dashboards/

[^11]: https://github.com/muesli/docker-backup

[^12]: https://helpcenter.veeam.com/docs/backup/vbr_rest/overview.html

[^13]: https://www.instructables.com/Pi-Health-Dashboard/

[^14]: https://www.reddit.com/r/selfhosted/comments/1kxjmkz/best_open_source_tool_for_daily_docker_backups/

[^15]: https://learn.microsoft.com/en-us/azure/well-architected/service-guides/azure-api-management

[^16]: https://docs.docker.com/reference/samples/flask/

[^17]: https://github.com/nickjj/docker-flask-example

[^18]: https://blog.teclado.com/run-flask-apps-with-docker-compose/

[^19]: https://www.instructables.com/Raspberry-Pi-SSH-Hardening/

[^20]: https://www.opensourcerers.org/2022/04/25/optimizing-a-systemd-service-for-security/

