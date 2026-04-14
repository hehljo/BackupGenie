# BackupGenie - Master Roadmap

## Done
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

## Future Features
- [ ] **Inkrementelle Backups:** Nur bei Änderungen sichern (GitHub: nur wenn neue Commits)
- [ ] **Backup-Rotation:** Max. Versionen pro Source (Standard: 3, einstellbar)
- [ ] **Scheduling:** Cron-artig pro Source oder global (täglich, stündlich, wöchentlich)
- [ ] **Per-Source Scheduling:** Individuelle Backup-Intervalle pro Quelle
- [ ] **Archivierung:** Optional tar.gz nach Backup erstellen
- [ ] **Notification Channels:** Telegram, Email, ntfy über Web UI konfigurierbar
- [ ] **Multi-Repo GitHub:** Alle Repos eines Users/Org auf einmal sichern (discovery_mode: all)
- [ ] **Backup Restore:** Wiederherstellung aus Backups über Web UI
- [ ] **Storage Dashboard:** Speicherplatz-Übersicht pro Source mit Trends
