# 🧞 BackupGenie – Setup Wizards für alle Backup-Quellen

**Schritt-für-Schritt-Anleitungen für Einsteiger**
**Best Practice: Februar 2026**

> [!TIP]
> **Hauptszenario:** Raspberry Pi mit USB-Festplatte – sobald die Platte eingesteckt wird, sichert BackupGenie automatisch alle konfigurierten Quellen darauf.

---

## 📋 Inhaltsverzeichnis

1. [Raspberry Pi Grundeinrichtung](#-raspberry-pi-grundeinrichtung)
2. [USB Auto-Backup einrichten](#-usb-auto-backup-einrichten)
3. [Lokale Verzeichnisse](#1-lokale-verzeichnisse)
4. [NAS via SMB (Synology, QNAP)](#2-nas-via-smb-synology-qnap-truenas)
5. [NAS via NFS](#3-nas-via-nfs)
6. [Rsync über SSH](#4-rsync-über-ssh)
7. [GitHub / GitLab / Gitea](#5-github--gitlab--gitea)
8. [MySQL / MariaDB](#6-mysql--mariadb)
9. [PostgreSQL](#7-postgresql)
10. [MongoDB](#8-mongodb)
11. [Redis](#9-redis)
12. [SQLite](#10-sqlite)
13. [CouchDB](#11-couchdb)
14. [InfluxDB 2.x](#12-influxdb-2x)
15. [Cloud Storage (rclone)](#13-cloud-storage-via-rclone)
16. [Docker Volumes & Images](#14-docker-volumes--images)
17. [Self-Hosted Apps](#15-self-hosted-apps)
18. [Proxmox VE](#16-proxmox-ve)
19. [FTP / SFTP](#17-ftp--sftp)
20. [WebDAV (Nextcloud etc.)](#18-webdav-nextcloud-owncloud)

---

## 🍓 Raspberry Pi Grundeinrichtung

### Voraussetzungen

- Raspberry Pi 3/4/5 mit Raspberry Pi OS (64-bit empfohlen)
- SD-Karte (min. 16 GB)
- Netzwerkverbindung (LAN empfohlen)
- USB-Festplatte für Backups (ext4 formatiert empfohlen)

### Schritt-für-Schritt

**Schritt 1:** Raspberry Pi OS installieren und SSH aktivieren.

**Schritt 2:** Per SSH verbinden:
```bash
ssh pi@<IP-ADRESSE>
```

**Schritt 3:** BackupGenie installieren:
```bash
curl -fsSL https://raw.githubusercontent.com/hehljo/BackupGenie/main/install.sh | bash
```
Oder manuell:
```bash
git clone https://github.com/hehljo/BackupGenie.git /opt/BackupGenie
cd /opt/BackupGenie
./scripts/setup-raspberry-pi.sh
```

**Schritt 4:** Starten:
```bash
cd /opt/BackupGenie
docker compose up -d
```

**Schritt 5:** Web-Interface öffnen:
```
http://<RASPBERRY-PI-IP>:3000
```
Login: `admin` / Passwort aus `docker compose logs backend | grep 'Initial password'`

---

## 🔌 USB Auto-Backup einrichten

> [!IMPORTANT]
> Das ist das Herzstück: USB-Festplatte einstecken → Backup startet automatisch.

### Schritt 1: USB-Festplatte vorbereiten

Festplatte mit ext4 formatieren und Label "BACKUP" geben:
```bash
# Festplatte finden (meistens /dev/sda)
lsblk

# Formatieren (ACHTUNG: Alle Daten werden gelöscht!)
sudo mkfs.ext4 -L BACKUP /dev/sda1
```

### Schritt 2: Systemd-Service installieren

```bash
cd /opt/BackupGenie
sudo ./scripts/install-systemd.sh
```

### Schritt 3: API-Token einrichten

```bash
# Token aus dem Web-Interface holen (Settings > API) oder:
# Temporär: den JWT-Token nach Login verwenden
echo "DEIN_TOKEN" | sudo tee /etc/backupgenie/api_token
sudo chmod 600 /etc/backupgenie/api_token
```

### Schritt 4: Testen

```bash
# USB-Festplatte einstecken, dann Logs prüfen:
journalctl -u 'backupgenie-backup@*' -f
# Oder:
tail -f /var/log/backupgenie/trigger.log
```

### ✅ Ergebnis

Ab jetzt: USB-Platte einstecken → wird automatisch gemountet → Backup aller konfigurierten Quellen startet → Platte kann wieder abgezogen werden.

---

## Backup-Quellen einrichten

> [!NOTE]
> Alle Quellen werden über das **Web-Interface** (Sources-Seite) oder direkt in `config/sources.json` konfiguriert. Unten die Anleitung für jede Quelle.

---

### 1. Lokale Verzeichnisse

**Tool:** `rsync` | **Schwierigkeit:** ⭐ Einfach

**Was wird gesichert?** Ordner auf dem Raspberry Pi selbst.

**Schritt 1:** Im Web-Interface: Sources → New Source → "Local Directory"

**Schritt 2:** Konfiguration:
```json
{
  "id": "lokale-daten",
  "name": "Meine lokalen Dokumente",
  "type": "local",
  "enabled": true,
  "sources": [
    "/home/pi/documents",
    "/home/pi/photos"
  ],
  "options": {
    "recursive": true,
    "delete": false
  }
}
```

**✅ Test:** Backup manuell starten, prüfen ob Dateien auf der USB-Platte landen.

---

### 2. NAS via SMB (Synology, QNAP, TrueNAS)

**Tool:** `mount -t cifs` + `rsync` | **Schwierigkeit:** ⭐⭐ Mittel

**Voraussetzungen:**
- NAS-IP-Adresse kennen
- Freigabe-Name kennen (z.B. "backup" oder "share")
- NAS-Benutzername und Passwort

**Schritt 1:** NAS-Zugang vorbereiten:
- Auf dem NAS: Einen Backup-Benutzer erstellen (z.B. `backup_user`)
- Einen freigegebenen Ordner erstellen (z.B. `backupshare`)
- SMB-Zugriff aktivieren

**Schritt 2:** Vom Raspberry Pi testen:
```bash
# Test-Mount
sudo mount -t cifs //192.168.1.100/backupshare /mnt/test \
  -o username=backup_user,password=deinpasswort,vers=3.0
ls /mnt/test
sudo umount /mnt/test
```

**Schritt 3:** Passwort in `.env` eintragen:
```bash
echo 'SMB_PASSWORD=deinpasswort' >> /opt/BackupGenie/.env
```

**Schritt 4:** Quelle konfigurieren:
```json
{
  "id": "nas-synology",
  "name": "Synology NAS",
  "type": "smb",
  "enabled": true,
  "source": "//192.168.1.100/backupshare",
  "credentials": {
    "username": "backup_user",
    "password_env": "SMB_PASSWORD"
  },
  "options": {
    "recursive": true,
    "delete": false
  }
}
```

**💡 Troubleshooting:**
- `mount error(13)` → Falsches Passwort oder fehlende Berechtigung
- `mount error(112)` → NAS nicht erreichbar, IP prüfen
- `mount error(22)` → SMB-Version anpassen (wird automatisch versucht: 3.1.1 → 3.0 → 2.1)

---

### 3. NAS via NFS

**Tool:** `mount -t nfs` + `rsync` | **Schwierigkeit:** ⭐⭐ Mittel

**Schritt 1:** Am NAS: NFS-Export aktivieren und die Raspberry Pi IP erlauben.

**Schritt 2:** Testen:
```bash
sudo mount -t nfs -o vers=3 192.168.1.100:/volume1/backup /mnt/test
ls /mnt/test
sudo umount /mnt/test
```

**Schritt 3:** Konfiguration:
```json
{
  "id": "nas-nfs",
  "name": "NAS via NFS",
  "type": "nfs",
  "enabled": true,
  "source": "192.168.1.100:/volume1/backup",
  "options": {
    "vers": 3,
    "nolock": true
  }
}
```

---

### 4. Rsync über SSH

**Tool:** `rsync -e ssh` | **Schwierigkeit:** ⭐⭐ Mittel

**Voraussetzungen:** SSH-Zugang zum Remote-Server

**Schritt 1:** SSH-Key erstellen (ohne Passwort für automatische Backups):
```bash
ssh-keygen -t ed25519 -f ~/.ssh/backup_key -N ""
```

**Schritt 2:** Key auf den Remote-Server kopieren:
```bash
ssh-copy-id -i ~/.ssh/backup_key.pub benutzer@192.168.1.100
```

**Schritt 3:** Testen:
```bash
ssh -i ~/.ssh/backup_key benutzer@192.168.1.100 "ls /volume1/data"
```

**Schritt 4:** Konfiguration:
```json
{
  "id": "server-rsync",
  "name": "Remote Server via SSH",
  "type": "rsync-ssh",
  "enabled": true,
  "host": "192.168.1.100",
  "port": 22,
  "path": "/volume1/data",
  "credentials": {
    "username_env": "SSH_USER",
    "ssh_key_path": "~/.ssh/backup_key"
  },
  "options": {
    "compress": true,
    "recursive": true,
    "exclude": ["*.tmp", "*.log", ".cache"]
  }
}
```
In `.env`: `SSH_USER=benutzer`

---

### 5. GitHub / GitLab / Gitea

**Tool:** `git clone --mirror` | **Schwierigkeit:** ⭐⭐ Mittel

> [!NOTE]
> **Warum nicht rclone?** Git-Repositories enthalten Branches, Tags und History – das kann nur `git clone --mirror` korrekt sichern.

#### GitHub

**Schritt 1:** GitHub Personal Access Token erstellen:
1. Gehe zu https://github.com/settings/tokens
2. Klick: **"Generate new token (classic)"**
3. Name: `BackupGenie`
4. Ablauf: Kein Ablauf (oder 1 Jahr)
5. Berechtigungen: `repo` (alle Repo-Rechte)
6. Token kopieren (beginnt mit `ghp_`)

**Schritt 2:** Token in `.env` eintragen:
```bash
echo 'GITHUB_TOKEN=ghp_dein_token_hier' >> /opt/BackupGenie/.env
```

**Schritt 3:** Konfiguration:
```json
{
  "id": "github-repos",
  "name": "GitHub Repositories",
  "type": "github",
  "enabled": true,
  "repositories": [
    "dein-username/repo1",
    "dein-username/repo2"
  ],
  "credentials": {
    "token_env": "GITHUB_TOKEN"
  },
  "options": {
    "include_wikis": true,
    "include_lfs": false
  }
}
```

#### GitLab

**Schritt 1:** Token erstellen unter https://gitlab.com/-/profile/personal_access_tokens
- Scopes: `read_api`, `read_repository`

**Schritt 2:** Konfiguration:
```json
{
  "id": "gitlab-repos",
  "name": "GitLab Projects",
  "type": "gitlab",
  "enabled": true,
  "repositories": ["username/project1"],
  "credentials": {
    "token_env": "GITLAB_TOKEN"
  }
}
```

#### Gitea / Forgejo / Codeberg

Gleicher Ablauf – Token in den jeweiligen Einstellungen erstellen. Codeberg: https://codeberg.org/user/settings/applications

---

### 6. MySQL / MariaDB

**Tool:** `mysqldump` | **Schwierigkeit:** ⭐⭐ Mittel

> [!NOTE]
> **Warum nicht rclone?** Datenbank-Dateien dürfen nie direkt kopiert werden – nur `mysqldump` erstellt konsistente Sicherungen.

**Schritt 1:** Backup-Benutzer in MySQL anlegen:
```sql
CREATE USER 'backup_user'@'%' IDENTIFIED BY 'sicheres_passwort';
GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER ON *.* TO 'backup_user'@'%';
FLUSH PRIVILEGES;
```

**Schritt 2:** Verbindung testen:
```bash
mysqldump --host=192.168.1.100 --user=backup_user --password=sicheres_passwort \
  --all-databases --single-transaction > /dev/null
echo "Verbindung OK!"
```

**Schritt 3:** Credentials in `.env`:
```bash
echo 'MYSQL_USER=backup_user' >> /opt/BackupGenie/.env
echo 'MYSQL_PASSWORD=sicheres_passwort' >> /opt/BackupGenie/.env
```

**Schritt 4:** Konfiguration:
```json
{
  "id": "mysql-db",
  "name": "MySQL Datenbank",
  "type": "mysql",
  "enabled": true,
  "host": "192.168.1.100",
  "port": 3306,
  "databases": [],
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
> `"databases": []` = alle Datenbanken sichern

**💡 Troubleshooting:**
- `Access denied` → Benutzer oder Passwort falsch
- `Can't connect` → MySQL-Port (3306) ist nicht offen oder Host stimmt nicht
- Docker: `host` = Container-Name oder `host.docker.internal`

---

### 7. PostgreSQL

**Tool:** `pg_dump` | **Schwierigkeit:** ⭐⭐ Mittel

**Schritt 1:** Backup-Benutzer vorbereiten (als PostgreSQL-Admin):
```sql
CREATE ROLE backup_user WITH LOGIN PASSWORD 'sicheres_passwort';
GRANT pg_read_all_data TO backup_user;
```

**Schritt 2:** Testen:
```bash
PGPASSWORD=sicheres_passwort pg_dump --host=localhost --username=backup_user postgres > /dev/null
echo "OK!"
```

**Schritt 3:** Konfiguration:
```json
{
  "id": "postgres-db",
  "name": "PostgreSQL",
  "type": "postgresql",
  "enabled": true,
  "host": "192.168.1.100",
  "port": 5432,
  "databases": ["meine_datenbank"],
  "credentials": {
    "username_env": "POSTGRES_USER",
    "password_env": "POSTGRES_PASSWORD"
  },
  "options": {
    "gzip": true
  }
}
```

---

### 8. MongoDB

**Tool:** `mongodump` | **Schwierigkeit:** ⭐⭐ Mittel

**Schritt 1:** Testen:
```bash
mongodump --host=localhost --port=27017 --out=/tmp/mongo_test --gzip
echo "OK!"
rm -rf /tmp/mongo_test
```

**Schritt 2:** Konfiguration:
```json
{
  "id": "mongodb",
  "name": "MongoDB",
  "type": "mongodb",
  "enabled": true,
  "host": "192.168.1.100",
  "port": 27017,
  "database": "meine_app",
  "credentials": {
    "username_env": "MONGO_USER",
    "password_env": "MONGO_PASSWORD"
  },
  "options": {
    "gzip": true
  }
}
```
> Credentials sind optional – nur wenn MongoDB Auth aktiviert ist.

---

### 9. Redis

**Tool:** `redis-cli BGSAVE` | **Schwierigkeit:** ⭐ Einfach

**Schritt 1:** Testen:
```bash
redis-cli -h 192.168.1.100 PING
# Antwort: PONG
```

**Schritt 2:** Konfiguration:
```json
{
  "id": "redis",
  "name": "Redis Cache",
  "type": "redis",
  "enabled": true,
  "host": "192.168.1.100",
  "port": 6379,
  "credentials": {
    "password_env": "REDIS_PASSWORD"
  }
}
```
> Passwort nur nötig wenn `requirepass` in Redis gesetzt ist.

---

### 10. SQLite

**Tool:** `sqlite3 .backup` | **Schwierigkeit:** ⭐ Einfach

**Schritt 1:** Dateipfad(e) der SQLite-Datenbank herausfinden:
```bash
find / -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" 2>/dev/null
```

**Schritt 2:** Konfiguration:
```json
{
  "id": "sqlite-dbs",
  "name": "SQLite Datenbanken",
  "type": "sqlite",
  "enabled": true,
  "databases": [
    "/var/lib/app/database.db",
    "/home/pi/data/local.sqlite"
  ]
}
```

---

### 11. CouchDB

**Tool:** HTTP API | **Schwierigkeit:** ⭐⭐ Mittel

**Schritt 1:** Testen:
```bash
curl -u admin:passwort http://192.168.1.100:5984/_all_dbs
```

**Schritt 2:** Konfiguration:
```json
{
  "id": "couchdb",
  "name": "CouchDB",
  "type": "couchdb",
  "enabled": true,
  "host": "192.168.1.100",
  "port": 5984,
  "databases": ["meine_db"],
  "credentials": {
    "username_env": "COUCHDB_USER",
    "password_env": "COUCHDB_PASSWORD"
  }
}
```

---

### 12. InfluxDB 2.x

**Tool:** `influx backup` | **Schwierigkeit:** ⭐⭐⭐ Fortgeschritten

**Schritt 1:** API-Token in InfluxDB UI erstellen:
1. InfluxDB UI öffnen (z.B. `http://192.168.1.100:8086`)
2. API Tokens → Generate API Token → All Access
3. Token kopieren

**Schritt 2:** Testen:
```bash
influx backup /tmp/influx_test \
  --host http://192.168.1.100:8086 \
  --token dein_token
rm -rf /tmp/influx_test
```

**Schritt 3:** Konfiguration:
```json
{
  "id": "influxdb",
  "name": "InfluxDB Metriken",
  "type": "influxdb",
  "enabled": true,
  "host": "192.168.1.100",
  "port": 8086,
  "org": "meine_org",
  "bucket": "mein_bucket",
  "credentials": {
    "token_env": "INFLUXDB_TOKEN"
  },
  "options": {
    "compress": true
  }
}
```

---

### 13. Cloud Storage (via rclone)

**Tool:** `rclone` | **Schwierigkeit:** ⭐⭐⭐ Fortgeschritten

> [!IMPORTANT]
> rclone ist die Best Practice für **Cloud Storage**: Google Drive, OneDrive, Dropbox, S3, Backblaze B2, und 40+ weitere Provider. Für alle anderen Quellen gibt es bessere native Tools (siehe oben).

#### Google Drive

**Schritt 1:** rclone konfigurieren:
```bash
docker exec -it backupgenie-backend rclone config

# Folgende Eingaben:
# n          (New remote)
# gdrive     (Name)
# drive      (Typ: Google Drive)
# [Enter]    (Client ID leer lassen)
# [Enter]    (Client Secret leer lassen)
# 1          (Full access)
# [Enter]    (Root folder ID leer)
# [Enter]    (Service account leer)
# n          (No advanced config)
# n          (No auto config - headless!)
```

**Schritt 2:** Bei "headless" wird ein Link angezeigt. Diesen im Browser auf einem PC öffnen, sich einloggen und den Code zurückkopieren.

**Schritt 3:** Testen:
```bash
docker exec -it backupgenie-backend rclone ls gdrive: --max-depth 1
```

**Schritt 4:** Konfiguration:
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
    "bwlimit": "5M"
  }
}
```

#### OneDrive / Dropbox / S3

Gleicher Ablauf mit `rclone config` – rclone führt interaktiv durch die Einrichtung. Remote-Name und Typ ändern sich:
- OneDrive: Typ `onedrive`
- Dropbox: Typ `dropbox`
- S3: Typ `s3`
- Backblaze B2: Typ `b2`

**💡 Tipp:** `bwlimit` begrenzt die Bandbreite (z.B. `5M` = 5 MB/s), damit der Pi nicht das ganze Netzwerk belegt.

---

### 14. Docker Volumes & Images

**Tool:** Docker CLI | **Schwierigkeit:** ⭐⭐ Mittel

> [!NOTE]
> **Warum nicht rclone?** rclone hat keinen Zugriff auf Docker Volumes. Nur die Docker CLI kann Volumes und Images korrekt sichern.

**Schritt 1:** Volumes auflisten:
```bash
docker volume ls
```

**Schritt 2:** Konfiguration (Volumes):
```json
{
  "id": "docker-volumes",
  "name": "Docker Volumes",
  "type": "docker-volume",
  "enabled": true,
  "volumes": [
    "mysql_data",
    "app_uploads",
    "nginx_config"
  ],
  "options": {
    "stop_for_backup": false,
    "backup_config": true
  }
}
```

**Schritt 3:** Konfiguration (Images):
```json
{
  "id": "docker-images",
  "name": "Docker Images",
  "type": "docker-image",
  "enabled": true,
  "images": [
    "nginx:latest",
    "mysql:8.0",
    "meine-app:production"
  ],
  "options": {
    "compress": true
  }
}
```

> `stop_for_backup: true` → Container werden vor dem Backup gestoppt (konsistenter, aber mit Downtime)

---

### 15. Self-Hosted Apps

**Tool:** Docker Volumes + API | **Schwierigkeit:** ⭐⭐⭐ Fortgeschritten

Jede App hat ihre eigene Backup-Methode:

| App | Methode | API-Key nötig? |
|-----|---------|---------------|
| Home Assistant | Snapshot-API | ✅ Long-Lived Token |
| Grafana | Dashboard-Export API | ✅ Service Token |
| Plex | Docker Volume | ✅ Plex Token |
| Jellyfin | Docker Volume | ✅ API Key |
| Portainer | Stacks-API | ✅ API Key |
| Node-RED | Flows-Export | Optional |
| Vaultwarden | Docker Volume + rsync | ❌ |
| Paperless-NGX | Docker Volume | ✅ Token |
| Immich | Docker Volume | ✅ API Key |

**Beispiel: Home Assistant**
```json
{
  "id": "homeassistant",
  "name": "Home Assistant",
  "type": "homeassistant",
  "enabled": true,
  "host": "192.168.1.100",
  "port": 8123,
  "credentials": {
    "token_env": "HA_TOKEN"
  },
  "options": {
    "backup_method": "api",
    "backup_database": true
  }
}
```
Token: Home Assistant → Profil → Long-Lived Access Tokens → erstellen.

---

### 16. Proxmox VE

**Tool:** vzdump API / CLI | **Schwierigkeit:** ⭐⭐⭐ Fortgeschritten

> [!NOTE]
> Sehr verbreitet im Homelab – BackupGenie kann automatisch alle VMs und Container von Proxmox sichern.

#### Methode 1: API (empfohlen – funktioniert remote)

**Schritt 1:** API-Token in Proxmox erstellen:
1. Proxmox Web UI → Datacenter → Permissions → API Tokens
2. User: `backup@pam` (oder neuen erstellen)
3. Token ID: `backup-token`
4. Privilege Separation: Nein (für Backup-Zugriff)
5. Token kopieren

**Schritt 2:** In `.env` eintragen:
```bash
echo 'PROXMOX_TOKEN=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx' >> /opt/BackupGenie/.env
```

**Schritt 3:** Konfiguration:
```json
{
  "id": "proxmox-vms",
  "name": "Proxmox VE",
  "type": "proxmox",
  "enabled": true,
  "host": "192.168.1.100",
  "port": 8006,
  "node": "pve",
  "backup_all": true,
  "credentials": {
    "token_id": "backup@pam!backup-token",
    "token_env": "PROXMOX_TOKEN"
  },
  "options": {
    "method": "api",
    "mode": "snapshot",
    "compress": "zstd",
    "backup_config": true,
    "download_backups": true,
    "verify_ssl": false
  }
}
```

#### Methode 2: CLI (auf dem Proxmox-Host selbst)

Wenn BackupGenie direkt auf dem Proxmox-Host läuft:
```json
{
  "id": "proxmox-cli",
  "name": "Proxmox VE (lokal)",
  "type": "proxmox",
  "enabled": true,
  "vmids": [100, 101, 102],
  "options": {
    "method": "cli",
    "mode": "snapshot",
    "compress": "zstd"
  }
}
```

**💡 Tipps:**
- `mode: "snapshot"` = kein Downtime (empfohlen)
- `mode: "stop"` = konsistenter, aber VM wird kurz gestoppt
- `compress: "zstd"` = schnellste Kompression (Best Practice 2026)

---

### 17. FTP / SFTP

**FTP Tool:** `lftp` | **SFTP Tool:** `rsync -e ssh` | **Schwierigkeit:** ⭐⭐ Mittel

#### FTP
```json
{
  "id": "ftp-server",
  "name": "FTP Server",
  "type": "ftp",
  "enabled": true,
  "host": "ftp.example.com",
  "port": 21,
  "path": "/backup",
  "credentials": {
    "username_env": "FTP_USER",
    "password_env": "FTP_PASSWORD"
  }
}
```

#### SFTP (empfohlen statt FTP!)
```json
{
  "id": "sftp-server",
  "name": "SFTP Server",
  "type": "sftp",
  "enabled": true,
  "host": "server.example.com",
  "port": 22,
  "path": "/backup",
  "credentials": {
    "username_env": "SFTP_USER",
    "ssh_key_path": "~/.ssh/backup_key"
  }
}
```

---

### 18. WebDAV (Nextcloud, ownCloud)

**Tool:** `rclone` oder `davfs2` | **Schwierigkeit:** ⭐⭐ Mittel

**Schritt 1:** Testen:
```bash
curl -u benutzer:passwort https://cloud.example.com/remote.php/dav/files/benutzer/
```

**Schritt 2:** Konfiguration:
```json
{
  "id": "nextcloud",
  "name": "Nextcloud",
  "type": "webdav",
  "enabled": true,
  "host": "cloud.example.com",
  "path": "/remote.php/dav/files/benutzer/Dokumente",
  "https": true,
  "vendor": "nextcloud",
  "credentials": {
    "username_env": "NEXTCLOUD_USER",
    "password_env": "NEXTCLOUD_PASSWORD"
  },
  "options": {
    "method": "rclone",
    "transfers": 4
  }
}
```

---

## 🔧 Zusammenfassung: Welches Tool für welche Quelle?

| Quelle | Best-Practice Tool | Warum? |
|---|---|---|
| **Cloud Storage** | ✅ rclone | 40+ Provider, OAuth2, bewährt |
| **Git-Repos** | `git clone --mirror` | Branches, Tags, History komplett |
| **MySQL/MariaDB** | `mysqldump` | Konsistente Dumps, Transaktionen |
| **PostgreSQL** | `pg_dump` | Custom-Format, granulare Restores |
| **MongoDB** | `mongodump` | BSON-Format, konsistente Snapshots |
| **Redis** | `redis-cli BGSAVE` | RDB-Snapshot, nicht-blockierend |
| **SQLite** | `sqlite3 .backup` | Online-Backup ohne Locks |
| **InfluxDB** | `influx backup` | Proprietäres Format |
| **Docker** | Docker CLI | Volume/Image-Layer-Zugriff |
| **Proxmox VE** | vzdump API/CLI | VM/Container-Snapshots, zstd-Kompression |
| **NAS (SMB)** | `mount + rsync` | Delta-Transfer, robust |
| **NAS (NFS)** | `mount + rsync` | Native Linux-Integration |
| **SSH/SFTP** | `rsync -e ssh` | Delta-Transfer, verschlüsselt |
| **FTP** | `lftp` | Mirror-Modus, Resume-Support |
| **WebDAV** | rclone oder davfs2 | Beides funktioniert gut |
| **Self-Hosted** | App-spezifisch | API + Docker Volumes |

> [!TIP]
> **rclone ist hervorragend für Cloud Storage, aber kein Universaltool.** BackupGenie wählt automatisch das beste Tool für jede Quelle – du musst dich um nichts kümmern!
