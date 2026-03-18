import { useState, useEffect } from 'react'
import {
  X, HardDrive, Cloud, Folder, Database, Eye, EyeOff,
  GitBranch, Server, Lock, Mail, Image, Home, FileText,
  Package, Cpu, Globe, Archive, Book, Users, Shield,
  Activity, Boxes, Film, Music, Camera, MessageSquare, AlertCircle
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import clsx from 'clsx'
import GitHubRepoSelector from './GitHubRepoSelector'

// Complete list of 60+ backup source types organized by category
const SOURCE_TYPES = [
  // Network Storage (4)
  { value: 'nas', label: 'NAS (SMB/CIFS)', icon: HardDrive, category: 'Network Storage' },
  { value: 'nfs', label: 'NFS', icon: Server, category: 'Network Storage' },
  { value: 'rsync-ssh', label: 'Rsync over SSH', icon: Server, category: 'Network Storage' },
  { value: 'webdav', label: 'WebDAV', icon: Cloud, category: 'Network Storage' },

  // Local Storage (1)
  { value: 'local', label: 'Local Directory', icon: Folder, category: 'Local Storage' },

  // Git Platforms (6)
  { value: 'github', label: 'GitHub', icon: GitBranch, category: 'Git Platforms' },
  { value: 'gitlab', label: 'GitLab', icon: GitBranch, category: 'Git Platforms' },
  { value: 'gitea', label: 'Gitea', icon: GitBranch, category: 'Git Platforms' },
  { value: 'forgejo', label: 'Forgejo', icon: GitBranch, category: 'Git Platforms' },
  { value: 'bitbucket', label: 'Bitbucket', icon: GitBranch, category: 'Git Platforms' },
  { value: 'codeberg', label: 'Codeberg', icon: GitBranch, category: 'Git Platforms' },

  // Databases (7)
  { value: 'mysql', label: 'MySQL/MariaDB', icon: Database, category: 'Databases' },
  { value: 'postgresql', label: 'PostgreSQL', icon: Database, category: 'Databases' },
  { value: 'mongodb', label: 'MongoDB', icon: Database, category: 'Databases' },
  { value: 'redis', label: 'Redis', icon: Database, category: 'Databases' },
  { value: 'sqlite', label: 'SQLite', icon: Database, category: 'Databases' },
  { value: 'couchdb', label: 'CouchDB', icon: Database, category: 'Databases' },
  { value: 'influxdb', label: 'InfluxDB', icon: Activity, category: 'Databases' },

  // Cloud Storage (10)
  { value: 'gdrive', label: 'Google Drive', icon: Cloud, category: 'Cloud Storage' },
  { value: 'onedrive', label: 'Microsoft OneDrive', icon: Cloud, category: 'Cloud Storage' },
  { value: 'dropbox', label: 'Dropbox', icon: Cloud, category: 'Cloud Storage' },
  { value: 's3', label: 'AWS S3', icon: Cloud, category: 'Cloud Storage' },
  { value: 'b2', label: 'Backblaze B2', icon: Cloud, category: 'Cloud Storage' },
  { value: 'icloud', label: 'Apple iCloud', icon: Cloud, category: 'Cloud Storage' },
  { value: 'box', label: 'Box', icon: Cloud, category: 'Cloud Storage' },
  { value: 'mega', label: 'MEGA', icon: Cloud, category: 'Cloud Storage' },
  { value: 'pcloud', label: 'pCloud', icon: Cloud, category: 'Cloud Storage' },
  { value: 'rclone', label: 'rclone (Generic)', icon: Cloud, category: 'Cloud Storage' },

  // FTP/SFTP (3)
  { value: 'ftp', label: 'FTP/FTPS', icon: Server, category: 'FTP/SFTP' },
  { value: 'sftp', label: 'SFTP', icon: Server, category: 'FTP/SFTP' },

  // Docker (2)
  { value: 'docker-volume', label: 'Docker Volumes', icon: Package, category: 'Docker' },
  { value: 'docker-image', label: 'Docker Images', icon: Boxes, category: 'Docker' },

  // Media Servers (5)
  { value: 'plex', label: 'Plex', icon: Film, category: 'Media Servers' },
  { value: 'jellyfin', label: 'Jellyfin', icon: Film, category: 'Media Servers' },
  { value: 'immich', label: 'Immich', icon: Camera, category: 'Media Servers' },
  { value: 'photoprism', label: 'PhotoPrism', icon: Image, category: 'Media Servers' },
  { value: 'komga', label: 'Komga', icon: Book, category: 'Media Servers' },

  // Smart Home (5)
  { value: 'homeassistant', label: 'Home Assistant', icon: Home, category: 'Smart Home' },
  { value: 'grafana', label: 'Grafana', icon: Activity, category: 'Smart Home' },
  { value: 'nodered', label: 'Node-RED', icon: Activity, category: 'Smart Home' },
  { value: 'prometheus', label: 'Prometheus', icon: Activity, category: 'Smart Home' },
  { value: 'loki', label: 'Loki', icon: FileText, category: 'Smart Home' },

  // Security (2)
  { value: 'vaultwarden', label: 'Vaultwarden', icon: Lock, category: 'Security' },
  { value: 'bitwarden', label: 'Bitwarden', icon: Shield, category: 'Security' },

  // Documentation (3)
  { value: 'mediawiki', label: 'MediaWiki', icon: Book, category: 'Documentation' },
  { value: 'tiddlywiki', label: 'TiddlyWiki', icon: Book, category: 'Documentation' },
  { value: 'obsidian', label: 'Obsidian', icon: FileText, category: 'Documentation' },

  // Communication (3)
  { value: 'mailcow', label: 'Mailcow', icon: Mail, category: 'Communication' },
  { value: 'mastodon', label: 'Mastodon', icon: Users, category: 'Communication' },
  { value: 'mattermost', label: 'Mattermost', icon: MessageSquare, category: 'Communication' },

  // Content Management (4)
  { value: 'paperless-ngx', label: 'Paperless-NGX', icon: FileText, category: 'Content Management' },
  { value: 'archivebox', label: 'ArchiveBox', icon: Archive, category: 'Content Management' },
  { value: 'wallabag', label: 'Wallabag', icon: Book, category: 'Content Management' },
  { value: 'linkding', label: 'Linkding', icon: Globe, category: 'Content Management' },

  // Management Tools (4)
  { value: 'portainer', label: 'Portainer', icon: Package, category: 'Management Tools' },
  { value: 'yacht', label: 'Yacht', icon: Package, category: 'Management Tools' },
  { value: 'syncthing', label: 'Syncthing', icon: Activity, category: 'Management Tools' },
  { value: 'restic', label: 'Restic', icon: Archive, category: 'Management Tools' },
]

// Group source types by category for better UX
const SOURCE_CATEGORIES = SOURCE_TYPES.reduce((acc, type) => {
  if (!acc[type.category]) acc[type.category] = []
  acc[type.category].push(type)
  return acc
}, {})

export default function SourceModal({ isOpen, onClose, onSave, editingSource }) {
  const { t } = useTranslation()
  const [showPassword, setShowPassword] = useState(false)
  const [showToken, setShowToken] = useState(false)
  const [showApiKey, setShowApiKey] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState('Network Storage')
  const [formData, setFormData] = useState({
    name: '',
    type: 'nas',
    enabled: true,
    priority: 1,
    config: {}
  })

  useEffect(() => {
    if (editingSource) {
      setFormData(editingSource)
      // Set category based on type
      const sourceType = SOURCE_TYPES.find(t => t.value === editingSource.type)
      if (sourceType) setSelectedCategory(sourceType.category)
    } else {
      // Reset form
      setFormData({
        name: '',
        type: 'nas',
        enabled: true,
        priority: 1,
        config: {}
      })
      setSelectedCategory('Network Storage')
    }
  }, [editingSource, isOpen])

  const handleSubmit = (e) => {
    e.preventDefault()
    onSave(formData)
  }

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleConfigChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      config: { ...prev.config, [field]: value }
    }))
  }

  const handleTypeChange = (type) => {
    setFormData(prev => ({
      ...prev,
      type,
      config: {} // Reset config when type changes
    }))
  }

  if (!isOpen) return null

  // Get config fields based on selected type
  const renderConfigFields = () => {
    const type = formData.type

    // Network Storage Types
    if (type === 'nas') {
      return (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Host/IP *</label>
            <input
              type="text"
              className="input"
              value={formData.config.host || ''}
              onChange={(e) => handleConfigChange('host', e.target.value)}
              placeholder="192.168.1.100"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Share Name *</label>
            <input
              type="text"
              className="input"
              value={formData.config.share || ''}
              onChange={(e) => handleConfigChange('share', e.target.value)}
              placeholder="backup"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Remote Path</label>
            <input
              type="text"
              className="input"
              value={formData.config.path || ''}
              onChange={(e) => handleConfigChange('path', e.target.value)}
              placeholder="/backups"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Username</label>
            <input
              type="text"
              className="input"
              value={formData.config.username || ''}
              onChange={(e) => handleConfigChange('username', e.target.value)}
              placeholder="nas_user"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                className="input pr-10"
                value={formData.config.password || ''}
                onChange={(e) => handleConfigChange('password', e.target.value)}
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-500 hover:text-gray-700"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      )
    }

    if (type === 'nfs') {
      return (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Host/IP *</label>
            <input
              type="text"
              className="input"
              value={formData.config.host || ''}
              onChange={(e) => handleConfigChange('host', e.target.value)}
              placeholder="192.168.1.100"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Export Path *</label>
            <input
              type="text"
              className="input"
              value={formData.config.share || ''}
              onChange={(e) => handleConfigChange('share', e.target.value)}
              placeholder="/exports/backup"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Remote Path</label>
            <input
              type="text"
              className="input"
              value={formData.config.path || ''}
              onChange={(e) => handleConfigChange('path', e.target.value)}
              placeholder="/data"
            />
          </div>
        </div>
      )
    }

    if (type === 'rsync-ssh') {
      return (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Host *</label>
            <input
              type="text"
              className="input"
              value={formData.config.host || ''}
              onChange={(e) => handleConfigChange('host', e.target.value)}
              placeholder="192.168.1.100"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Port</label>
            <input
              type="number"
              className="input"
              value={formData.config.port || 22}
              onChange={(e) => handleConfigChange('port', parseInt(e.target.value))}
              placeholder="22"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Remote Path *</label>
            <input
              type="text"
              className="input"
              value={formData.config.path || ''}
              onChange={(e) => handleConfigChange('path', e.target.value)}
              placeholder="/volume1/backup"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Username</label>
            <input
              type="text"
              className="input"
              value={formData.config.username || ''}
              onChange={(e) => handleConfigChange('username', e.target.value)}
              placeholder="backup_user"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">SSH Key Path</label>
            <input
              type="text"
              className="input"
              value={formData.config.ssh_key_path || ''}
              onChange={(e) => handleConfigChange('ssh_key_path', e.target.value)}
              placeholder="~/.ssh/id_rsa"
            />
            <p className="text-xs text-gray-500 mt-1">Leave empty to use password authentication</p>
          </div>
        </div>
      )
    }

    if (type === 'webdav') {
      return (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Host *</label>
            <input
              type="text"
              className="input"
              value={formData.config.host || ''}
              onChange={(e) => handleConfigChange('host', e.target.value)}
              placeholder="cloud.example.com"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Path</label>
            <input
              type="text"
              className="input"
              value={formData.config.path || ''}
              onChange={(e) => handleConfigChange('path', e.target.value)}
              placeholder="/remote.php/dav/files/username/Backup"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Username</label>
            <input
              type="text"
              className="input"
              value={formData.config.username || ''}
              onChange={(e) => handleConfigChange('username', e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                className="input pr-10"
                value={formData.config.password || ''}
                onChange={(e) => handleConfigChange('password', e.target.value)}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-500 hover:text-gray-700"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      )
    }

    // Local Storage
    if (type === 'local') {
      return (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Local Path *</label>
          <input
            type="text"
            className="input"
            value={formData.config.path || ''}
            onChange={(e) => handleConfigChange('path', e.target.value)}
            placeholder="/var/data"
            required
          />
        </div>
      )
    }

    // GitHub with auto-discovery
    if (type === 'github') {
      return (
        <div className="space-y-4">
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              GitHub Token wird unter <strong>Settings → Credentials</strong> global konfiguriert.
              Dort einmal eintragen, gilt für alle GitHub-Quellen.
            </p>
          </div>

          <GitHubRepoSelector
            discoveryMode={formData.config.discovery_mode || 'manual'}
            selectedRepos={formData.config.repositories || []}
            excludeRepos={formData.config.exclude || []}
            onDiscoveryModeChange={(mode) => handleConfigChange('discovery_mode', mode)}
            onSelectedReposChange={(repos) => handleConfigChange('repositories', repos)}
            onExcludeChange={(excludes) => handleConfigChange('exclude', excludes)}
          />
        </div>
      )
    }

    // Other Git Platforms
    if (['gitlab', 'gitea', 'forgejo', 'bitbucket', 'codeberg'].includes(type)) {
      return (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {type === 'gitlab' ? 'GitLab Instance' : 'Host'} {type === 'gitlab' && '(optional)'}
            </label>
            <input
              type="text"
              className="input"
              value={formData.config.host || ''}
              onChange={(e) => handleConfigChange('host', e.target.value)}
              placeholder={
                type === 'gitlab' ? 'gitlab.com' :
                type === 'gitea' ? 'gitea.example.com' :
                type === 'forgejo' ? 'forgejo.example.com' :
                type === 'codeberg' ? 'codeberg.org' :
                'bitbucket.org'
              }
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Repositories *</label>
            <input
              type="text"
              className="input"
              value={formData.config.repo || ''}
              onChange={(e) => handleConfigChange('repo', e.target.value)}
              placeholder="username/repository"
              required
            />
            <p className="text-xs text-gray-500 mt-1">Format: username/repository or org/repository</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Access Token *</label>
            <div className="relative">
              <input
                type={showToken ? "text" : "password"}
                className="input pr-10"
                value={formData.config.token || ''}
                onChange={(e) => handleConfigChange('token', e.target.value)}
                placeholder={
                  type === 'gitlab' ? 'glpat-xxxxxxxxxxxx' :
                  'xxxxxxxxxxxx'
                }
                required
              />
              <button
                type="button"
                onClick={() => setShowToken(!showToken)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-500 hover:text-gray-700"
              >
                {showToken ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      )
    }

    // Databases
    if (['mysql', 'postgresql', 'mongodb', 'redis', 'couchdb', 'influxdb'].includes(type)) {
      return (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Host *</label>
            <input
              type="text"
              className="input"
              value={formData.config.host || 'localhost'}
              onChange={(e) => handleConfigChange('host', e.target.value)}
              placeholder="localhost"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Port</label>
            <input
              type="number"
              className="input"
              value={formData.config.port || (
                type === 'mysql' ? 3306 :
                type === 'postgresql' ? 5432 :
                type === 'mongodb' ? 27017 :
                type === 'redis' ? 6379 :
                type === 'couchdb' ? 5984 :
                8086
              )}
              onChange={(e) => handleConfigChange('port', parseInt(e.target.value))}
            />
          </div>
          {type !== 'redis' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Database Name</label>
              <input
                type="text"
                className="input"
                value={formData.config.database || ''}
                onChange={(e) => handleConfigChange('database', e.target.value)}
                placeholder={type === 'mongodb' ? 'myapp' : 'production_db'}
              />
              <p className="text-xs text-gray-500 mt-1">Leave empty to backup all databases</p>
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Username</label>
            <input
              type="text"
              className="input"
              value={formData.config.username || ''}
              onChange={(e) => handleConfigChange('username', e.target.value)}
              placeholder={type === 'postgresql' ? 'postgres' : 'root'}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                className="input pr-10"
                value={formData.config.password || ''}
                onChange={(e) => handleConfigChange('password', e.target.value)}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-500 hover:text-gray-700"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      )
    }

    if (type === 'sqlite') {
      return (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Database File Path *</label>
          <input
            type="text"
            className="input"
            value={formData.config.path || ''}
            onChange={(e) => handleConfigChange('path', e.target.value)}
            placeholder="/var/lib/app/database.db"
            required
          />
        </div>
      )
    }

    // Cloud Storage (rclone-based)
    if (['gdrive', 'onedrive', 'dropbox', 's3', 'b2', 'icloud', 'box', 'mega', 'pcloud', 'rclone'].includes(type)) {
      // Determine if OAuth2 is needed
      const needsOAuth = !['s3', 'b2'].includes(type)

      return (
        <div className="space-y-4">
          {/* Important Notice */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
              <div className="text-sm text-blue-800">
                <p className="font-semibold mb-1">
                  {needsOAuth ? 'OAuth2 Authentication Required' : 'API Credentials Required'}
                </p>
                {needsOAuth ? (
                  <>
                    <p className="mb-2">Configure rclone manually first:</p>
                    <code className="block bg-blue-100 p-2 rounded text-xs mb-2">
                      docker exec -it backupgenie-backend rclone config
                    </code>
                    <p className="text-xs">
                      Follow the interactive prompts to authenticate with {
                        type === 'gdrive' ? 'Google Drive' :
                        type === 'onedrive' ? 'Microsoft OneDrive' :
                        type === 'dropbox' ? 'Dropbox' :
                        'your cloud provider'
                      }. Then enter the remote name below.
                    </p>
                  </>
                ) : (
                  <p className="text-xs">
                    Enter your {type === 's3' ? 'AWS' : 'Backblaze B2'} credentials below.
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* rclone Remote Name (for OAuth2 sources) */}
          {needsOAuth && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                rclone Remote Name *
              </label>
              <input
                type="text"
                className="input"
                value={formData.config.remote || ''}
                onChange={(e) => handleConfigChange('remote', e.target.value)}
                placeholder={
                  type === 'gdrive' ? 'my-gdrive' :
                  type === 'onedrive' ? 'my-onedrive' :
                  type === 'dropbox' ? 'my-dropbox' :
                  'myremote'
                }
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                The name you configured with 'rclone config'
              </p>
            </div>
          )}

          {/* S3/B2 Credentials */}
          {!needsOAuth && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {type === 's3' ? 'AWS Access Key ID *' : 'Application Key ID *'}
                </label>
                <input
                  type="text"
                  className="input"
                  value={formData.config.access_key || ''}
                  onChange={(e) => handleConfigChange('access_key', e.target.value)}
                  placeholder={type === 's3' ? 'AKIAIOSFODNN7EXAMPLE' : 'Your B2 Key ID'}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {type === 's3' ? 'AWS Secret Access Key *' : 'Application Key *'}
                </label>
                <div className="relative">
                  <input
                    type={showApiKey ? "text" : "password"}
                    className="input pr-10"
                    value={formData.config.secret_key || ''}
                    onChange={(e) => handleConfigChange('secret_key', e.target.value)}
                    placeholder="Your secret key"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-500 hover:text-gray-700"
                  >
                    {showApiKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>
              {type === 's3' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Region *</label>
                    <input
                      type="text"
                      className="input"
                      value={formData.config.region || 'us-east-1'}
                      onChange={(e) => handleConfigChange('region', e.target.value)}
                      placeholder="us-east-1"
                      required
                    />
                    <p className="text-xs text-gray-500 mt-1">AWS region (e.g., us-east-1, eu-west-1)</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Bucket Name *</label>
                    <input
                      type="text"
                      className="input"
                      value={formData.config.bucket || ''}
                      onChange={(e) => handleConfigChange('bucket', e.target.value)}
                      placeholder="my-backup-bucket"
                      required
                    />
                  </div>
                </>
              )}
              {type === 'b2' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Bucket Name *</label>
                  <input
                    type="text"
                    className="input"
                    value={formData.config.bucket || ''}
                    onChange={(e) => handleConfigChange('bucket', e.target.value)}
                    placeholder="my-b2-bucket"
                    required
                  />
                </div>
              )}
            </>
          )}

          {/* Folder Path */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Folder Path *</label>
            <input
              type="text"
              className="input"
              value={formData.config.path || ''}
              onChange={(e) => handleConfigChange('path', e.target.value)}
              placeholder={
                type === 's3' || type === 'b2' ? '/backups' :
                type === 'gdrive' ? 'Backups/MyFolder' :
                type === 'onedrive' ? 'Documents/Backups' :
                type === 'dropbox' ? '/Backups' :
                '/Backups'
              }
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              {type === 's3' || type === 'b2' ?
                'Path/prefix within the bucket' :
                'Path within your ' + (type === 'gdrive' ? 'Google Drive' : type === 'onedrive' ? 'OneDrive' : type === 'dropbox' ? 'Dropbox' : 'cloud storage')}
            </p>
          </div>
        </div>
      )
    }

    // FTP/SFTP
    if (['ftp', 'sftp'].includes(type)) {
      return (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Host *</label>
            <input
              type="text"
              className="input"
              value={formData.config.host || ''}
              onChange={(e) => handleConfigChange('host', e.target.value)}
              placeholder="ftp.example.com"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Port</label>
            <input
              type="number"
              className="input"
              value={formData.config.port || (type === 'ftp' ? 21 : 22)}
              onChange={(e) => handleConfigChange('port', parseInt(e.target.value))}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Remote Path</label>
            <input
              type="text"
              className="input"
              value={formData.config.path || ''}
              onChange={(e) => handleConfigChange('path', e.target.value)}
              placeholder="/backup"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Username</label>
            <input
              type="text"
              className="input"
              value={formData.config.username || ''}
              onChange={(e) => handleConfigChange('username', e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {type === 'sftp' ? 'Password or SSH Key' : 'Password'}
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                className="input pr-10"
                value={formData.config.password || ''}
                onChange={(e) => handleConfigChange('password', e.target.value)}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-500 hover:text-gray-700"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      )
    }

    // Docker
    if (type === 'docker-volume') {
      return (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Volume Names *</label>
            <input
              type="text"
              className="input"
              value={formData.config.volumes || ''}
              onChange={(e) => handleConfigChange('volumes', e.target.value)}
              placeholder="mysql_data, nginx_config, app_uploads"
              required
            />
            <p className="text-xs text-gray-500 mt-1">Comma-separated list of Docker volume names</p>
          </div>
        </div>
      )
    }

    if (type === 'docker-image') {
      return (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Image Names *</label>
            <input
              type="text"
              className="input"
              value={formData.config.images || ''}
              onChange={(e) => handleConfigChange('images', e.target.value)}
              placeholder="nginx:latest, mysql:8.0, myapp:production"
              required
            />
            <p className="text-xs text-gray-500 mt-1">Comma-separated list of Docker image names</p>
          </div>
        </div>
      )
    }

    // Self-Hosted Services - Generic config for all
    if (['plex', 'jellyfin', 'immich', 'photoprism', 'komga', 'homeassistant',
         'grafana', 'nodered', 'prometheus', 'loki', 'vaultwarden', 'bitwarden',
         'mediawiki', 'tiddlywiki', 'obsidian', 'mailcow', 'mastodon', 'mattermost',
         'paperless-ngx', 'archivebox', 'wallabag', 'linkding', 'portainer',
         'yacht', 'syncthing', 'restic'].includes(type)) {
      return (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Host *</label>
            <input
              type="text"
              className="input"
              value={formData.config.host || 'localhost'}
              onChange={(e) => handleConfigChange('host', e.target.value)}
              placeholder="192.168.1.100"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Port</label>
            <input
              type="number"
              className="input"
              value={formData.config.port || (
                type === 'plex' ? 32400 :
                type === 'jellyfin' ? 8096 :
                type === 'homeassistant' ? 8123 :
                type === 'grafana' ? 3000 :
                type === 'portainer' ? 9000 :
                8080
              )}
              onChange={(e) => handleConfigChange('port', parseInt(e.target.value))}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {type === 'plex' ? 'Plex Token' : 'API Key / Token'}
            </label>
            <div className="relative">
              <input
                type={showApiKey ? "text" : "password"}
                className="input pr-10"
                value={formData.config.api_key || formData.config.token || ''}
                onChange={(e) => {
                  if (type === 'plex') {
                    handleConfigChange('token', e.target.value)
                  } else {
                    handleConfigChange('api_key', e.target.value)
                  }
                }}
                placeholder="Enter API key or token"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-500 hover:text-gray-700"
              >
                {showApiKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      )
    }

    // Default fallback
    return (
      <div className="p-4 bg-blue-50 rounded-lg">
        <p className="text-sm text-blue-700">
          Configuration for this source type will be available soon. Please configure manually in sources.json.
        </p>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="sticky top-0 bg-white border-b border-gray-200 px-4 md:px-6 py-4 flex items-center justify-between z-10">
            <h2 className="text-lg md:text-xl font-bold text-gray-900">
              {editingSource ? 'Edit Source' : t('sources.addSource')}
            </h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-4 md:p-6 space-y-4 md:space-y-6">
            {/* Basic Info */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Source Name *
                </label>
                <input
                  type="text"
                  className="input"
                  value={formData.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  placeholder="My Backup Source"
                  required
                />
              </div>

              {/* Category Tabs */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Source Type * ({SOURCE_TYPES.length}+ types)
                </label>

                {/* Category Selector */}
                <div className="flex overflow-x-auto gap-2 mb-3 pb-2">
                  {Object.keys(SOURCE_CATEGORIES).map((category) => (
                    <button
                      key={category}
                      type="button"
                      onClick={() => setSelectedCategory(category)}
                      className={clsx(
                        'px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-all',
                        selectedCategory === category
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      )}
                    >
                      {category} ({SOURCE_CATEGORIES[category].length})
                    </button>
                  ))}
                </div>

                {/* Type Grid */}
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                  {SOURCE_CATEGORIES[selectedCategory]?.map(({ value, label, icon: Icon }) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => handleTypeChange(value)}
                      className={clsx(
                        'flex flex-col items-center gap-2 p-3 rounded-lg border-2 transition-all text-left',
                        formData.type === value
                          ? 'border-primary-600 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
                      )}
                    >
                      <Icon className={clsx(
                        'w-5 h-5 md:w-6 md:h-6',
                        formData.type === value ? 'text-primary-600' : 'text-gray-600'
                      )} />
                      <span className={clsx(
                        'text-xs md:text-sm font-medium text-center',
                        formData.type === value ? 'text-primary-700' : 'text-gray-700'
                      )}>
                        {label}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Priority
                  </label>
                  <input
                    type="number"
                    className="input"
                    value={formData.priority}
                    onChange={(e) => handleChange('priority', parseInt(e.target.value))}
                    min="1"
                    max="100"
                  />
                  <p className="text-xs text-gray-500 mt-1">Higher priority = backed up first</p>
                </div>

                <div>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                      checked={formData.enabled}
                      onChange={(e) => handleChange('enabled', e.target.checked)}
                    />
                    <span className="text-sm font-medium text-gray-700">
                      {t('sources.enabled')}
                    </span>
                  </label>
                  <p className="text-xs text-gray-500 mt-1">Enable automatic backups</p>
                </div>
              </div>
            </div>

            {/* Type-specific config */}
            <div className="border-t border-gray-200 pt-4 md:pt-6">
              <h3 className="text-base md:text-lg font-semibold text-gray-900 mb-3">Configuration</h3>
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg mb-4">
                <p className="text-xs text-amber-800">
                  Zugangsdaten (Tokens, Passwörter, API-Keys) werden global unter <strong>Settings → Credentials</strong> verwaltet. Dort einmal eintragen, gilt für alle Quellen dieses Typs.
                </p>
              </div>
              {renderConfigFields()}
            </div>

            {/* Actions */}
            <div className="flex flex-col-reverse sm:flex-row gap-3 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                className="btn btn-secondary w-full sm:w-auto"
              >
                {t('common.cancel')}
              </button>
              <button
                type="submit"
                className="btn btn-primary w-full sm:w-auto"
              >
                {editingSource ? t('common.save') : t('common.add')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
