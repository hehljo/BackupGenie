#!/bin/bash
# BackupGenie - Install systemd service and udev rules
# Run this script with sudo after installing BackupGenie

set -e

INSTALL_DIR="/opt/BackupGenie"
SCRIPTS_DIR="$INSTALL_DIR/scripts"

echo "Installing BackupGenie systemd service and udev rules..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run as root (use sudo)"
    exit 1
fi

# Create udev rule for automatic backup triggering
echo "Creating udev rule..."
cat > /etc/udev/rules.d/99-backupgenie-backup.rules << 'EOF'
# Trigger backup when USB device is added
ACTION=="add", KERNEL=="sd[a-z][0-9]", TAG+="systemd", ENV{SYSTEMD_WANTS}="backupgenie-backup@%k.service"

# Optional: Remove tag when device is removed
ACTION=="remove", KERNEL=="sd[a-z][0-9]", RUN+="/opt/BackupGenie/scripts/backup-cleanup.sh %k"
EOF

# Create systemd service
echo "Creating systemd service..."
cat > /etc/systemd/system/backupgenie-backup@.service << 'EOF'
[Unit]
Description=BackupGenie Auto-Backup Trigger for %i
BindsTo=sys-subsystem-block-devices-%i.device
After=sys-subsystem-block-devices-%i.device
ConditionPathExists=/opt/BackupGenie/docker-compose.yml

[Service]
Type=oneshot

# Wait until device is mounted (up to 60 seconds)
ExecStartPre=/bin/bash -c 'for i in {1..60}; do mountpoint -q /mnt/backup && break || sleep 1; done'

# Trigger backup
ExecStart=/opt/BackupGenie/scripts/trigger-backup.sh

StandardOutput=journal
StandardError=journal
User=pi
Group=docker
Environment="PATH=/usr/local/bin:/usr/bin:/bin"

# Timeout after 4 hours (in case backup takes very long)
TimeoutStartSec=14400
EOF

# Make scripts executable
echo "Making scripts executable..."
chmod +x "$SCRIPTS_DIR/trigger-backup.sh"
chmod +x "$SCRIPTS_DIR/backup-cleanup.sh"

# Reload systemd and udev
echo "Reloading systemd and udev..."
systemctl daemon-reload
udevadm control --reload-rules
udevadm trigger

# Create log directory
echo "Creating log directory..."
mkdir -p /var/log/backupgenie
chown pi:pi /var/log/backupgenie

# Create API token directory
echo "Creating API token directory..."
mkdir -p /etc/backupgenie
chmod 700 /etc/backupgenie

echo ""
echo "============================================"
echo "Installation complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Generate an API token:"
echo "   docker exec backupgenie-backend python3 -c \"from app.api.auth import generate_token; print(generate_token('automation', 365))\""
echo ""
echo "2. Save the token:"
echo "   echo 'YOUR_TOKEN' | sudo tee /etc/backupgenie/api-token"
echo "   sudo chmod 600 /etc/backupgenie/api-token"
echo ""
echo "3. Test the trigger:"
echo "   sudo /opt/BackupGenie/scripts/trigger-backup.sh"
echo ""
echo "4. Monitor logs:"
echo "   tail -f /var/log/backupgenie-trigger.log"
echo "   journalctl -u backupgenie-backup@* -f"
echo ""
