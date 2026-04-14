# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BackupGenie is an automated multi-source backup manager originally designed for Raspberry Pi. Flask/Python backend with React/Vite frontend, deployed via Docker Compose. Supports 60+ backup sources (NAS, GitHub, Cloud, Docker, Self-Hosted Apps, Databases).

## Build & Run

```bash
# Start all services
docker compose up -d

# Start with Pi 3 optimized config
docker compose -f docker-compose.rpi3.yml up -d

# Backend only (development)
cd backend && pip install -r requirements.txt && python run.py

# Frontend only (development)
cd frontend && npm ci && npm run dev

# Build Docker images
docker compose build
```

## Architecture

### Backend (`backend/`)
- **Framework**: Flask 3.1 with SQLAlchemy (SQLite), served via Gunicorn
- **App Factory**: `app/__init__.py` → `create_app()` registers all blueprints
- **API Blueprints** (`app/api/`): `backup`, `sources`, `auth`, `notifications`, `settings`, `config` — all under `/api/v1/`
- **Backup Engine** (`app/backup/`):
  - `base.py` — `BackupHandler` ABC: all source handlers extend this
  - `executor.py` — `BackupExecutor`: coordinates parallel/sequential backup runs, manages lifecycle, sends notifications
  - `sources/` — One handler per source type (github, docker, smb, rclone, selfhosted, database, etc.)
- **Handler Registry**: `executor.py` maps type strings (e.g. `'github'`, `'portainer'`, `'docker-volume'`) to handler classes. `SelfHostedBackup` is a generic handler used for ~30 self-hosted service types.
- **Notifications** (`app/notifications/`): Uses Apprise for email, Telegram, ntfy, webhooks

### Frontend (`frontend/`)
- **Stack**: React + Vite + Tailwind CSS, served via nginx in production
- **i18n**: German and English (`src/locales/`)
- **Structure**: `src/pages/`, `src/components/`, `src/services/`

### Configuration
- `config/sources.json` — Backup sources definition (copy from `sources-example.json`)
- `config/rclone.conf` — Rclone remotes for cloud storage
- `config/notifications.json` — Notification channels
- `.env` — Environment variables (copy from `config/example.env`)
- Credentials are passed via env vars (e.g. `GITHUB_TOKEN`, `NAS_PASSWORD_1`)

### Docker
- Backend Dockerfile: Python 3.13-slim + rsync + git + rclone, multi-arch (amd64/arm64/arm)
- Frontend Dockerfile: Node 22 build stage → nginx:alpine
- `docker-compose.yml`: Standard config with resource limits, healthchecks, Docker socket mount
- `docker-compose.rpi3.yml`: Pi 3 optimized (reduced memory/CPU limits)

## Key Patterns

- All backup handlers return `{'files_synced': int, 'size_synced': int, 'logs': str}`
- GitHub backup uses `--mirror` clone, not regular clone — preserves all refs
- GitHub repos must be manually listed in config; no auto-discovery via API
- `SelfHostedBackup` dispatches to different methods based on `backup_method` option: `docker-volume`, `api`, `rsync`
- Rate limiting: 200/day, 50/hour default; health endpoint exempt
- Auth: JWT-based (`PyJWT`), admin bootstrap on first run with default password

## Important Rules (from claude.md)

- **No AI attribution** in commits, code, or docs — no "Generated with Claude", no "Co-Authored-By: Claude"
- Write as if written by a human developer
- Use standard commit messages focused on what changed
