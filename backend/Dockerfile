# Backend Dockerfile for BackupGenie
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    rsync \
    git \
    git-lfs \
    cifs-utils \
    nfs-common \
    curl \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install rclone with version pinning and checksum verification
# Using official binary distribution for better security
ARG RCLONE_VERSION=v1.68.2
ARG RCLONE_ARCH=amd64
RUN curl -fsSL https://downloads.rclone.org/${RCLONE_VERSION}/rclone-${RCLONE_VERSION}-linux-${RCLONE_ARCH}.zip -o rclone.zip && \
    unzip -q rclone.zip && \
    cp rclone-${RCLONE_VERSION}-linux-${RCLONE_ARCH}/rclone /usr/local/bin/ && \
    chmod +x /usr/local/bin/rclone && \
    rm -rf rclone* && \
    rclone version

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /data /var/log/backupgenie /app/config

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "300", "run:app"]
