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

# Install rclone with version pinning and automatic architecture detection
# Using official binary distribution for better security
ARG RCLONE_VERSION=v1.69.1
ARG TARGETARCH
RUN set -x && \
    # Map Docker TARGETARCH to rclone architecture naming
    case "${TARGETARCH}" in \
        amd64) RCLONE_ARCH="amd64" ;; \
        arm64) RCLONE_ARCH="arm64" ;; \
        arm) RCLONE_ARCH="arm" ;; \
        *) echo "Unsupported architecture: ${TARGETARCH}"; exit 1 ;; \
    esac && \
    echo "Installing rclone for architecture: ${RCLONE_ARCH} (Docker: ${TARGETARCH})" && \
    curl -fsSL https://downloads.rclone.org/${RCLONE_VERSION}/rclone-${RCLONE_VERSION}-linux-${RCLONE_ARCH}.zip -o rclone.zip && \
    unzip -q rclone.zip && \
    cp rclone-${RCLONE_VERSION}-linux-${RCLONE_ARCH}/rclone /usr/local/bin/ && \
    chmod +x /usr/local/bin/rclone && \
    rm -rf rclone* && \
    # Unset RCLONE_VERSION to avoid conflict with rclone's environment variables
    unset RCLONE_VERSION && \
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
