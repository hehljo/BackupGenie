# BackupGenie Installation Guide

This guide will help you install BackupGenie on your Raspberry Pi.

## Quick Install (Recommended)

For a fully automated installation on Raspberry Pi:

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/BackupGenie/main/scripts/setup-raspberry-pi.sh | bash
```

Or manually:

```bash
git clone https://github.com/YOUR_USERNAME/BackupGenie.git
cd BackupGenie
chmod +x scripts/setup-raspberry-pi.sh
./scripts/setup-raspberry-pi.sh
```

## Manual Installation

### Step 1: Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Install required tools
sudo apt install -y git curl rsync rclone git-lfs openssh-client cifs-utils nfs-common

# Reboot to apply Docker group membership
sudo reboot
```

### Step 2: Clone Repository

```bash
cd /opt
sudo git clone https://github.com/YOUR_USERNAME/BackupGenie.git
sudo chown -R $USER:$USER BackupGenie
cd BackupGenie
```

### Step 3: Configuration

```bash
# Copy example configuration
cp .env.example .env
cp config/sources-example.json config/sources.json
cp config/rclone-example.conf config/rclone.conf

# Edit configuration
nano .env
nano config/sources.json
```

### Step 4: Create Backup Mount Point

```bash
sudo mkdir -p /mnt/backup
sudo chown $USER:$USER /mnt/backup
```

### Step 5: Start Services

```bash
# Build and start containers
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### Step 6: Access Web Interface

Open your browser and navigate to:
```
http://YOUR_PI_IP:3000
```

Default credentials:
- Username: `admin`
- Password: Check Docker logs with `docker compose logs backend | grep "Initial password"`

### Step 7: Install Systemd Service (Optional)

For automatic backup triggering when USB drives are connected:

```bash
sudo ./scripts/install-systemd.sh
```

## Configuration

### Adding Backup Sources

Edit `config/sources.json` to add your backup sources:

```json
{
  "backup_sources": [
    {
      "id": "my-nas",
      "name": "My NAS",
      "type": "smb",
      "enabled": true,
      "priority": 1,
      "source": "//192.168.1.100/backups",
      "credentials": {
        "username": "user",
        "password_env": "NAS_PASSWORD"
      }
    }
  ]
}
```

### Configuring Cloud Storage (rclone)

```bash
# Interactive configuration
docker exec -it backupgenie-backend rclone config

# Or edit config/rclone.conf manually
nano config/rclone.conf
```

### Environment Variables

Create a `.env.secrets` file for sensitive credentials:

```bash
# .env.secrets
export NAS_PASSWORD='your_password'
export GITHUB_TOKEN='ghp_xxxxxxxxxxxx'
export RCLONE_CONFIG_GDRIVE_TOKEN='{"access_token":"..."}'
```

Load secrets before starting:

```bash
source .env.secrets
docker compose up -d
```

## Updating

```bash
cd /opt/BackupGenie
git pull
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs backend
docker compose logs frontend

# Rebuild containers
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R $USER:$USER /opt/BackupGenie
sudo chown -R $USER:$USER /mnt/backup

# Fix permissions
chmod 755 scripts/*.sh
```

### Mount Issues (SMB/NFS)

```bash
# Test SMB connection
smbclient -L //192.168.1.100 -U username

# Test from container
docker exec backupgenie-backend smbclient -L //192.168.1.100 -U username
```

### Backup Not Triggering Automatically

```bash
# Check udev rules
cat /etc/udev/rules.d/99-backupgenie-backup.rules

# Reload udev
sudo udevadm control --reload-rules
sudo udevadm trigger

# Check systemd service
journalctl -u backupgenie-backup@* -f

# Test manually
sudo /opt/BackupGenie/scripts/trigger-backup.sh
```

## Uninstallation

```bash
# Stop and remove containers
cd /opt/BackupGenie
docker compose down -v

# Remove systemd service
sudo rm /etc/systemd/system/backupgenie-backup@.service
sudo rm /etc/udev/rules.d/99-backupgenie-backup.rules
sudo systemctl daemon-reload
sudo udevadm control --reload-rules

# Remove application
sudo rm -rf /opt/BackupGenie

# Remove data (optional)
sudo rm -rf /mnt/backup
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/YOUR_USERNAME/BackupGenie/issues
- Documentation: See README.md
