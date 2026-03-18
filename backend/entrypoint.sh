#!/bin/bash
# BackupGenie - Container Entrypoint
# Runs hardware detection and starts the application

set -e

# Source hardware detection (sets environment variables)
source /app/scripts/detect-hardware.sh

# Set MAX_PARALLEL_TASKS if not explicitly configured
if [ -z "$MAX_PARALLEL_TASKS" ] || [ "$MAX_PARALLEL_TASKS" = "auto" ]; then
    export MAX_PARALLEL_TASKS="$RECOMMENDED_PARALLEL_TASKS"
    echo "  Auto-configured MAX_PARALLEL_TASKS=$MAX_PARALLEL_TASKS"
fi

# Adjust gunicorn workers based on available resources
GUNICORN_WORKERS=${GUNICORN_WORKERS:-2}
if [ "${HARDWARE_RAM_MB:-0}" -gt 0 ] && [ "${HARDWARE_RAM_MB:-0}" -le 1024 ]; then
    GUNICORN_WORKERS=1
    echo "  Low RAM detected, using 1 gunicorn worker"
fi

echo ""
echo "Starting BackupGenie backend..."

exec gunicorn \
    --bind 0.0.0.0:5000 \
    --workers "$GUNICORN_WORKERS" \
    --timeout 300 \
    run:app
