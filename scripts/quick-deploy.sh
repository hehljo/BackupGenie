#!/bin/bash
################################################################################
# BackupGenie - Quick Deploy Script
# One-Command Installation für schnelles Deployment
################################################################################

set -e

REPO_URL="${REPO_URL:-https://github.com/hehljo/BackupGenie.git}"
INSTALL_DIR="${INSTALL_DIR:-/opt/BackupGenie}"
BRANCH="${BRANCH:-main}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   BackupGenie - Quick Deploy              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}\n"

# 1. System Update
echo -e "${YELLOW}[1/6]${NC} System aktualisieren..."
sudo apt update -qq

# 2. Docker installieren
echo -e "${YELLOW}[2/6]${NC} Docker installieren..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sudo sh > /dev/null
    sudo usermod -aG docker ${SUDO_USER:-$USER}
fi

if ! docker compose version &> /dev/null; then
    sudo apt install -y docker-compose-plugin > /dev/null
fi

# 3. Dependencies
echo -e "${YELLOW}[3/6]${NC} Abhängigkeiten installieren..."
sudo apt install -y git curl rsync cifs-utils nfs-common > /dev/null 2>&1

# Install rclone
if ! command -v rclone &> /dev/null; then
    curl -s https://rclone.org/install.sh | sudo bash > /dev/null 2>&1
fi

# 4. Repository klonen
echo -e "${YELLOW}[4/6]${NC} Repository klonen..."
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${GREEN}Verzeichnis existiert bereits, nutze vorhandenes Repository${NC}"
    cd "$INSTALL_DIR"
    git pull origin $BRANCH > /dev/null 2>&1 || true
else
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown ${SUDO_USER:-$USER}:${SUDO_USER:-$USER} "$INSTALL_DIR"
    git clone -b $BRANCH "$REPO_URL" "$INSTALL_DIR" > /dev/null 2>&1
    cd "$INSTALL_DIR"
fi

# 5. Konfiguration
echo -e "${YELLOW}[5/6]${NC} Konfiguration vorbereiten..."
mkdir -p config data logs
sudo mkdir -p /mnt/backup
sudo chown ${SUDO_USER:-$USER}:${SUDO_USER:-$USER} /mnt/backup

# .env
if [ ! -f ".env" ]; then
    cp .env.example .env
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))' 2>/dev/null || openssl rand -base64 32)
    sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
fi

# sources.json
if [ ! -f "config/sources.json" ]; then
    if [ -f "config/sources-example.json" ]; then
        cp config/sources-example.json config/sources.json
    else
        echo '{"backup_sources":[]}' > config/sources.json
    fi
fi

# rclone.conf
if [ ! -f "config/rclone.conf" ]; then
    touch config/rclone.conf
fi

chmod +x scripts/*.sh 2>/dev/null || true

# 6. Docker Build & Start
echo -e "${YELLOW}[6/6]${NC} Docker Container starten (dies kann 10-20 Minuten dauern)..."
docker compose up -d --build

echo -e "\n${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Deployment abgeschlossen!                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}\n"

# Get IP and wait for containers
IP=$(hostname -I | awk '{print $1}')
echo "Warte auf Container-Start..."
sleep 5

# Get admin password
ADMIN_PASS=$(docker compose logs backend 2>/dev/null | grep -i "initial.*password" | tail -1 | awk '{print $NF}' || echo "siehe 'docker compose logs backend'")

echo -e "${BLUE}Web-Interface:${NC} http://$IP:3000"
echo -e "${BLUE}Benutzername:${NC}  admin"
echo -e "${BLUE}Passwort:${NC}      $ADMIN_PASS"
echo ""
echo -e "Container Status: ${GREEN}$(docker compose ps --services | wc -l)${NC} Services aktiv"
echo ""
echo -e "${YELLOW}Nächste Schritte:${NC}"
echo "1. Web-Interface öffnen und einloggen"
echo "2. Passwort ändern in Einstellungen"
echo "3. Backup-Quellen konfigurieren: nano $INSTALL_DIR/config/sources.json"
echo "4. Container neu starten: docker compose restart"
echo ""
echo "Logs anzeigen: docker compose logs -f"
echo "Container stoppen: docker compose stop"
echo ""
