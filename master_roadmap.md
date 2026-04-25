# BackupGenie - Master Roadmap

## Done
- [x] Dark Mode für komplettes Frontend mit Systemerkennung, Toggle und globalen Kontrast-Overrides umgesetzt
- [x] Projekt-spezifische `AGENTS.md` mit BackupGenie-Arbeitsregeln erstellt
- [x] Fix: Security-/Runtime-Bugs aus Tiefenanalyse behoben (Admin-Bootstrap, Supabase Full, Restore-Pfade, Config-Export, Source-Verträge, Notifications-Auth)
- [x] Global Credentials System (encrypted in DB)
- [x] Log Viewer im Frontend (System Logs Seite)
- [x] Security Hardening (Fernet encryption, input sanitization, capability reduction)
- [x] GitHub Backup funktional (Mirror Clone)
- [x] Version Number in Sidebar
- [x] Credentials Hint bei Source-Erstellung
- [x] Simplified Deployment (nur 4 Env Vars)
- [x] Fix: duplicate logging
- [x] Fix: datetime naive/aware mismatch
- [x] Fix: config sub-object in GitHub handler

## In Progress
- [ ] Alle Backup-Handler fixen: `config` Sub-Objekt Problem (wie bei GitHub) bei allen Source-Typen prüfen

## Done (Supabase & Restore)
- [x] **Supabase Source im Frontend:** Neue Kategorie "Cloud Platforms" mit Config-Formular (Project Ref, Region, Backup Mode)
- [x] **Suchfunktion in SourceModal:** Globale Suche über alle 60+ Source-Typen (nach Label, Kategorie, Value)
- [x] **Supabase Verbindungstest:** Button in Source-Config + Backend-Endpoint mit pg_dump/psql Validierung
- [x] **Supabase Restore Backend:** `SupabaseRestore` Klasse (Schema, Data, Roles, Auth, Storage)
- [x] **Restore API Endpoints:** Available Backups auflisten, Restore starten, Status-Polling
- [x] **Restore UI in History:** Restore-Button bei Supabase-Sources, Modal mit Ziel-Konfiguration, Bestätigungsdialog
- [x] **Restore Frontend API:** restoreAPI Service (getAvailable, start, getStatus)

## Future Features
- [ ] **Inkrementelle Backups:** Nur bei Änderungen sichern (GitHub: nur wenn neue Commits)
- [ ] **Backup-Rotation:** Max. Versionen pro Source (Standard: 3, einstellbar)
- [ ] **Scheduling:** Cron-artig pro Source oder global (täglich, stündlich, wöchentlich)
- [ ] **Per-Source Scheduling:** Individuelle Backup-Intervalle pro Quelle
- [ ] **Archivierung:** Optional tar.gz nach Backup erstellen
- [ ] **Notification Channels:** Telegram, Email, ntfy über Web UI konfigurierbar
- [ ] **Multi-Repo GitHub:** Alle Repos eines Users/Org auf einmal sichern (discovery_mode: all)
- [ ] **Storage Dashboard:** Speicherplatz-Übersicht pro Source mit Trends
- [ ] **Restore für weitere Source-Typen:** Docker, MySQL etc.
