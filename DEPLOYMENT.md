# BackupGenie - Deployment Guide für Raspberry Pi

Umfassende Anleitung für das einfache Deployment von BackupGenie auf Raspberry Pi mit Docker.

## 📋 Inhaltsverzeichnis

- [Schnellstart](#schnellstart)
- [Detaillierte Installation](#detaillierte-installation)
- [Deployment-Optionen](#deployment-optionen)
- [Hardware-Empfehlungen](#hardware-empfehlungen)
- [Performance-Optimierung](#performance-optimierung)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Schnellstart

### Option 1: Interaktiver Setup-Wizard (Empfohlen)

Der einfachste Weg - ein geführter Installationsprozess:

```bash
# Repository klonen
git clone https://github.com/hehljo/BackupGenie.git
cd BackupGenie

# Setup-Wizard starten
chmod +x scripts/setup-wizard.sh
./scripts/setup-wizard.sh
```

Der Wizard führt Sie durch:
- ✅ System-Prüfung
- ✅ Installation aller Abhängigkeiten
- ✅ Docker & Docker Compose Setup
- ✅ Konfiguration
- ✅ Container-Build & Start
- ✅ Optional: Systemd Service Installation

**Dauer:** ca. 15-25 Minuten (abhängig von Internet-Geschwindigkeit)

---

### Option 2: Quick Deploy (One-Liner)

Für schnelles Deployment ohne Interaktion:

```bash
curl -fsSL https://raw.githubusercontent.com/hehljo/BackupGenie/main/scripts/quick-deploy.sh | bash
```

Oder mit Git:

```bash
git clone https://github.com/hehljo/BackupGenie.git
cd BackupGenie
chmod +x scripts/quick-deploy.sh
./scripts/quick-deploy.sh
```

---

### Option 3: Manuelle Installation

Für erfahrene Benutzer, die jeden Schritt kontrollieren möchten:

```bash
# 1. Docker installieren
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# 2. Repository klonen
git clone https://github.com/hehljo/BackupGenie.git
cd BackupGenie

# 3. Konfiguration vorbereiten
cp .env.example .env
nano .env  # Secret Key generieren und anpassen

# 4. Container starten
docker compose up -d

# 5. Logs prüfen
docker compose logs -f
```

---

## 📦 Detaillierte Installation

### Schritt 1: Raspberry Pi Vorbereitung

#### 1.1 Betriebssystem installieren

**Empfohlen:** Raspberry Pi OS Lite (64-bit)

```bash
# System aktualisieren
sudo apt update && sudo apt upgrade -y

# Speicheroptimierung für Pi 3
sudo apt autoremove -y
sudo apt clean
```

#### 1.2 Grundlegende Konfiguration

```bash
# Hostname setzen
sudo raspi-config
# 1. System Options -> S4 Hostname -> "backupgenie"

# Zeitzone einstellen
sudo timedatectl set-timezone Europe/Berlin

# SSH aktivieren (falls noch nicht geschehen)
sudo systemctl enable ssh
sudo systemctl start ssh
```

#### 1.3 Speicher erweitern (wichtig für Raspberry Pi 3)

```bash
# Swap erweitern für bessere Performance
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=2048

sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

---

### Schritt 2: Docker Installation

```bash
# Docker installieren
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Benutzer zur Docker-Gruppe hinzufügen
sudo usermod -aG docker $USER

# Docker Compose Plugin
sudo apt install -y docker-compose-plugin

# Docker Memory Limits setzen (wichtig für Pi 3)
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  }
}
EOF

sudo systemctl restart docker

# Logout und Login für Gruppenmitgliedschaft
exit
# Neu einloggen via SSH
```

---

### Schritt 3: BackupGenie installieren

```bash
# Als normaler Benutzer (nicht root!)
cd /opt
sudo git clone https://github.com/hehljo/BackupGenie.git
sudo chown -R $USER:$USER BackupGenie
cd BackupGenie
```

---

### Schritt 4: Konfiguration

#### 4.1 Environment Variables (.env)

```bash
# .env erstellen
cp .env.example .env

# Secret Key generieren
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'

# .env bearbeiten
nano .env
```

**Wichtige Einstellungen:**

```bash
# Server
FLASK_ENV=production
SECRET_KEY=<generierter-key>
DEBUG=false

# Ports (anpassen falls nötig)
API_PORT=5000
FRONTEND_PORT=3000

# Backup
BACKUP_BASE_PATH=/mnt/backup
MAX_PARALLEL_TASKS=2  # Für Pi 3: 1, für Pi 4/5: 2-4
LOG_RETENTION_DAYS=30
```

#### 4.2 Backup-Quellen konfigurieren

```bash
# Sources Konfiguration erstellen
cp config/sources-example.json config/sources.json
nano config/sources.json
```

**Beispiel-Konfiguration:**

```json
{
  "backup_sources": [
    {
      "id": "nas-dokumente",
      "name": "NAS Dokumente",
      "type": "smb",
      "enabled": true,
      "priority": 1,
      "source": "//192.168.1.100/dokumente",
      "credentials": {
        "username": "backup_user",
        "password_env": "NAS_PASSWORD"
      },
      "options": {
        "recursive": true,
        "delete": false
      },
      "schedule": {
        "trigger": "usb_mount"
      }
    }
  ]
}
```

#### 4.3 Credentials sichern

```bash
# Separate Datei für Secrets erstellen
nano .env.secrets
```

```bash
# .env.secrets Inhalt
export NAS_PASSWORD='MeinSicheresPasswort'
export GITHUB_TOKEN='ghp_xxxxxxxxxxxxxxxxxxxx'
```

```bash
# Nur für aktuellen Benutzer lesbar
chmod 600 .env.secrets

# Vor jedem Container-Start laden
source .env.secrets
```

---

### Schritt 5: Container starten

#### Für Raspberry Pi 4/5 (2GB+ RAM):

```bash
# Standard Docker Compose
docker compose up -d --build
```

#### Für Raspberry Pi 3 (1GB RAM):

```bash
# Optimierte Konfiguration für Pi 3
docker compose -f docker-compose.rpi3.yml up -d --build
```

#### Build-Prozess überwachen:

```bash
# In separatem Terminal: Logs live verfolgen
docker compose logs -f
```

**Hinweis:** Der erste Build dauert 15-25 Minuten auf Raspberry Pi.

---

### Schritt 6: Zugriff testen

```bash
# IP-Adresse ermitteln
hostname -I | awk '{print $1}'

# Container Status prüfen
docker compose ps

# Health Checks prüfen
docker inspect backupgenie-backend | grep -A 5 Health
docker inspect backupgenie-frontend | grep -A 5 Health
```

**Web-Interface öffnen:**
```
http://<raspberry-pi-ip>:3000
```

**Initiales Admin-Passwort:**
```bash
docker compose logs backend | grep -i "initial password"
```

---

## 🔧 Deployment-Optionen

### Docker Compose Varianten

BackupGenie bietet verschiedene Docker Compose Konfigurationen:

| Datei | Verwendung | Hardware |
|-------|-----------|----------|
| `docker-compose.yml` | Standard | Pi 4/5 (2GB+ RAM) |
| `docker-compose.rpi3.yml` | Optimiert | Pi 3 (1GB RAM) |

**Verwendung:**

```bash
# Standard
docker compose up -d

# Raspberry Pi 3
docker compose -f docker-compose.rpi3.yml up -d
```

---

### Systemd Service Installation

Automatisches Backup beim Anschließen einer USB-Festplatte:

```bash
# Systemd Service & udev Regeln installieren
sudo ./scripts/install-systemd.sh

# Status prüfen
systemctl status backupgenie-backup@*

# Manuell testen
sudo /opt/BackupGenie/scripts/trigger-backup.sh
```

**Was wird installiert:**
- ✅ udev-Regel für USB-Erkennung (`/etc/udev/rules.d/99-backupgenie-backup.rules`)
- ✅ Systemd Service Template (`/etc/systemd/system/backupgenie-backup@.service`)
- ✅ Trigger-Script (`/opt/BackupGenie/scripts/trigger-backup.sh`)
- ✅ Cleanup-Script (`/opt/BackupGenie/scripts/backup-cleanup.sh`)

---

## 🖥️ Hardware-Empfehlungen

### Raspberry Pi Modelle

| Modell | RAM | Empfehlung | Max. Quellen | Parallele Tasks |
|--------|-----|-----------|--------------|-----------------|
| Pi 3 B+ | 1GB | ⚠️ Minimal | 5-10 | 1 |
| Pi 4 (2GB) | 2GB | ✅ Gut | 10-20 | 2 |
| Pi 4 (4GB) | 4GB | ✅ Sehr gut | 20-40 | 3-4 |
| Pi 4 (8GB) | 8GB | ✅✅ Optimal | 40+ | 4-6 |
| Pi 5 (4GB+) | 4GB+ | ✅✅ Optimal | 40+ | 4-8 |

### Speicher

| Komponente | Minimum | Empfohlen | Optimal |
|-----------|---------|-----------|---------|
| microSD | 16GB Class 10 | 32GB A1/A2 | 64GB+ A2 |
| USB Backup | 500GB | 1TB+ | 2TB+ |

**Tipp:** SSD-basierte USB-Festplatten sind deutlich schneller als HDD.

### Netzwerk

- **Minimum:** WLAN (WiFi 5)
- **Empfohlen:** Gigabit Ethernet (Pi 4/5)
- **Für NAS-Backups:** Unbedingt Ethernet verwenden

---

## ⚡ Performance-Optimierung

### Raspberry Pi 3 Optimierungen

```bash
# 1. Parallele Tasks reduzieren
nano .env
# MAX_PARALLEL_TASKS=1

# 2. Memory Swap erhöhen
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# 3. Weniger Log-Retention
nano .env
# LOG_RETENTION_DAYS=7

# 4. GPU Memory reduzieren (nur für Headless)
sudo raspi-config
# Performance Options -> GPU Memory -> 16
```

### Raspberry Pi 4/5 Optimierungen

```bash
# 1. Mehr parallele Tasks
nano .env
# MAX_PARALLEL_TASKS=4

# 2. USB 3.0 nutzen
# Blaue USB-Ports für externe Festplatten verwenden

# 3. Overclock (optional, nur mit guter Kühlung!)
sudo raspi-config
# Performance Options -> Overclock
```

### Docker Performance

```bash
# Container Resource Monitoring
docker stats

# Container Logs reduzieren
# In /etc/docker/daemon.json bereits konfiguriert:
# "max-size": "10m", "max-file": "3"

# Ungenutzten Speicher aufräumen
docker system prune -a --volumes
```

---

## 🔍 Troubleshooting

### Container starten nicht

**Problem:** Container bleiben im Restart-Loop

```bash
# Logs prüfen
docker compose logs backend
docker compose logs frontend

# Container Status
docker compose ps

# Resource-Probleme?
free -h
df -h

# Lösung: Container neu bauen
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

### Out of Memory (OOM) auf Pi 3

**Symptom:** Container werden unerwartet beendet

```bash
# Kernel Log prüfen
dmesg | grep -i oom

# Lösung 1: Pi 3 Konfiguration nutzen
docker compose -f docker-compose.rpi3.yml up -d

# Lösung 2: Swap erhöhen (siehe oben)

# Lösung 3: Nur einen Container zur Zeit bauen
docker compose build backend
docker compose build frontend
docker compose up -d
```

---

### Backup startet nicht automatisch (USB)

```bash
# udev-Regeln prüfen
cat /etc/udev/rules.d/99-backupgenie-backup.rules

# udev-Regeln neu laden
sudo udevadm control --reload-rules
sudo udevadm trigger

# USB-Gerät testen
lsblk
sudo udevadm info --name=/dev/sda1 --attribute-walk

# Systemd Service prüfen
journalctl -u backupgenie-backup@* -f

# Manuell testen
sudo /opt/BackupGenie/scripts/trigger-backup.sh
```

---

### Langsame Backups

**NAS (SMB/NFS):**

```bash
# Ethernet statt WiFi verwenden

# SMB Version testen
smbclient -L //192.168.1.100 -U user --option='client max protocol=SMB3'

# NFS Optionen optimieren
# In sources.json:
"options": {
  "vers": 3,
  "rsize": 8192,
  "wsize": 8192
}
```

**GitHub/Cloud:**

```bash
# Parallele Transfers erhöhen (nur Pi 4/5)
# In sources.json für rclone:
"options": {
  "transfers": 4,
  "checkers": 8
}
```

---

### Netzwerk-Probleme (NAS nicht erreichbar)

```bash
# Verbindung testen
ping 192.168.1.100

# SMB-Zugriff testen
smbclient -L //192.168.1.100 -U backup_user

# Von Container aus testen
docker exec -it backupgenie-backend smbclient -L //192.168.1.100 -U backup_user

# Firewall prüfen (auf NAS)
# SMB: Port 445
# NFS: Port 2049
```

---

### Frontend lädt nicht

```bash
# Nginx Logs prüfen
docker compose logs frontend

# Port-Konflikt?
sudo netstat -tulpn | grep 3000

# Browser Cache leeren
# Strg+Shift+R (Chrome/Firefox)

# Container neu starten
docker compose restart frontend
```

---

## 📊 Resource Monitoring

### System-Monitoring

```bash
# CPU & Memory
htop

# Docker Stats
docker stats

# Disk I/O
iostat -x 5

# Temperature (Raspberry Pi)
vcgencmd measure_temp

# Throttling prüfen
vcgencmd get_throttled
# 0x0 = OK
# Andere Werte = Throttling aktiv (Netzteil zu schwach!)
```

### Backup-Monitoring

```bash
# Aktuelle Backups
curl http://localhost:5000/api/v1/backup/stats

# Backup-Historie
curl http://localhost:5000/api/v1/backup/history?limit=10

# Log-Dateien
tail -f logs/backupgenie.log
```

---

## 🔐 Sicherheit

### SSH Hardening

```bash
# SSH-Key Authentication einrichten
ssh-keygen -t ed25519 -o -a 100
ssh-copy-id pi@backupgenie.local

# Password Authentication deaktivieren
sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no
# PermitRootLogin no
sudo systemctl restart ssh
```

### Firewall

```bash
# UFW installieren
sudo apt install ufw

# Regeln setzen
sudo ufw allow 22/tcp    # SSH
sudo ufw allow from 192.168.1.0/24 to any port 3000  # Frontend nur lokal
sudo ufw allow from 192.168.1.0/24 to any port 5000  # API nur lokal

sudo ufw enable
sudo ufw status
```

### Backup-Verschlüsselung

```bash
# GPG für verschlüsselte Backups
sudo apt install gnupg

# Key generieren
gpg --full-generate-key

# In sources.json encryption aktivieren
"options": {
  "encrypt": true,
  "gpg_recipient": "backup@example.com"
}
```

---

## 🔄 Updates

### BackupGenie aktualisieren

```bash
cd /opt/BackupGenie

# Git Update
git pull origin main

# Container neu bauen
docker compose down
docker compose build --no-cache
docker compose up -d

# Datenbank bleibt erhalten (Volume)
```

### System Updates

```bash
# Regelmäßig ausführen
sudo apt update && sudo apt upgrade -y
sudo apt autoremove -y

# Docker aktualisieren
sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

---

## 📞 Support & Dokumentation

- **Vollständige Dokumentation:** [Readme.md](Readme.md)
- **Backup-Quellen Guide:** [docs/BACKUP_SOURCES.md](docs/BACKUP_SOURCES.md)
- **i18n Dokumentation:** [docs/i18n.md](docs/i18n.md)
- **Installation:** [INSTALLATION.md](INSTALLATION.md)
- **GitHub Issues:** https://github.com/hehljo/BackupGenie/issues

---

## 📝 Checkliste für Deployment

- [ ] Raspberry Pi OS installiert und aktualisiert
- [ ] Docker & Docker Compose installiert
- [ ] BackupGenie Repository geklont
- [ ] `.env` Datei konfiguriert (Secret Key generiert)
- [ ] `config/sources.json` konfiguriert
- [ ] Credentials in `.env.secrets` gespeichert
- [ ] Backup-Mount-Verzeichnis erstellt (`/mnt/backup`)
- [ ] Container erfolgreich gebaut und gestartet
- [ ] Web-Interface erreichbar (http://IP:3000)
- [ ] Admin-Passwort geändert
- [ ] Erste Backup-Quelle getestet
- [ ] Systemd Service installiert (optional)
- [ ] USB-Trigger getestet (optional)
- [ ] SSH gehärtet
- [ ] Firewall konfiguriert
- [ ] Backup-Zeitplan erstellt

---

**Viel Erfolg mit BackupGenie! 🚀**

Bei Fragen oder Problemen: [GitHub Issues](https://github.com/hehljo/BackupGenie/issues)
