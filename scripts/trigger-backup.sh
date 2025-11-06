#!/bin/bash
# BackupGenie - Automatic Backup Trigger Script
# This script is called by systemd when a USB device is plugged in

set -e

LOG_FILE="/var/log/backupgenie-trigger.log"
BACKUP_DIR="/mnt/backup"
API_URL="http://localhost:5000/api/v1/backup/start"
TOKEN_FILE="/etc/backupgenie/api-token"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log "============================================"
log "Backup trigger started"

# Check if backup directory is mounted
if ! mountpoint -q "$BACKUP_DIR"; then
    log "ERROR: $BACKUP_DIR is not mounted"
    exit 1
fi

log "Backup directory verified: $BACKUP_DIR"

# Check if Docker containers are running
if ! docker ps | grep -q backupgenie-backend; then
    log "ERROR: BackupGenie backend container is not running"
    exit 1
fi

log "Backend container is running"

# Get API token
if [ -f "$TOKEN_FILE" ]; then
    TOKEN=$(cat "$TOKEN_FILE")
else
    log "WARNING: API token file not found, using environment variable"
    TOKEN="${BACKUPGENIE_API_TOKEN:-}"
fi

if [ -z "$TOKEN" ]; then
    log "ERROR: No API token available"
    exit 1
fi

# Wait a bit for the system to stabilize
log "Waiting 5 seconds for system to stabilize..."
sleep 5

# Trigger backup via API
log "Triggering backup via API..."
response=$(curl -s -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{
        "parallel": 2,
        "trigger_type": "usb_mount",
        "notify": true
    }' 2>&1)

if echo "$response" | grep -q '"status":"started"'; then
    backup_id=$(echo "$response" | grep -o '"backup_id":"[^"]*"' | cut -d'"' -f4)
    log "SUCCESS: Backup started successfully (ID: $backup_id)"

    # Optional: Send notification
    if command -v notify-send &> /dev/null; then
        notify-send "BackupGenie" "Backup started successfully"
    fi

    exit 0
else
    log "ERROR: Failed to start backup"
    log "Response: $response"

    # Optional: Send error notification
    if command -v notify-send &> /dev/null; then
        notify-send -u critical "BackupGenie" "Failed to start backup"
    fi

    exit 1
fi
