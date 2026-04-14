import { useState, useEffect, useRef } from 'react'
import { Settings as SettingsIcon, User, Shield, Database, Save, Loader, Download, Upload, FileJson, CheckCircle, AlertCircle, Key, Eye, EyeOff, Plus, Trash2, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { authAPI, backupAPI, settingsAPI, configAPI } from '../services/api'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { FormSkeleton } from '../components/Skeleton'
import ConfirmDialog from '../components/ConfirmDialog'

export default function Settings() {
  const { t } = useTranslation()
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [saveStatus, setSaveStatus] = useState(null)

  // User and Settings Data
  const [user, setUser] = useState(null)
  const [settings, setSettings] = useState({
    backupBasePath: '/mnt/backup',
    maxParallelTasks: 2,
    logRetention: 30,
    apiAuth: true,
    httpsOnly: false,
    autoCleanup: true,
  })

  // Storage Data
  const [storage, setStorage] = useState({
    totalBytes: 0,
    usedBytes: 0,
    percentage: 0,
  })

  // Password Change
  const [passwords, setPasswords] = useState({
    newPassword: '',
    confirmPassword: '',
  })
  const [passwordError, setPasswordError] = useState('')
  const [passwordSuccess, setPasswordSuccess] = useState(false)

  // Export/Import
  const fileInputRef = useRef(null)
  const [importFile, setImportFile] = useState(null)
  const [importMerge, setImportMerge] = useState(false)
  const [validationResult, setValidationResult] = useState(null)

  // Credentials
  const [credentials, setCredentials] = useState({})
  const [credentialVisibility, setCredentialVisibility] = useState({})
  const [isSavingCredentials, setIsSavingCredentials] = useState(false)
  const [newProfile, setNewProfile] = useState({ type: '', name: '', value: '' })
  const [showAddProfile, setShowAddProfile] = useState(null) // which type is adding

  // Confirm Dialogs
  const [clearBackupsConfirm, setClearBackupsConfirm] = useState(false)
  const [isClearing, setIsClearing] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      // Load user info
      const userRes = await authAPI.getCurrentUser()
      setUser(userRes.data)

      // Load settings from backend (includes real storage stats)
      const settingsRes = await settingsAPI.get()
      const settingsData = settingsRes.data

      // Update settings state
      setSettings({
        backupBasePath: settingsData.backup_base_path,
        maxParallelTasks: settingsData.max_parallel_tasks,
        logRetention: settingsData.log_retention_days,
        apiAuth: settingsData.api_auth_enabled,
        httpsOnly: settingsData.https_only,
        autoCleanup: settingsData.auto_cleanup,
      })

      // Update storage stats (now from real disk usage!)
      if (settingsData.storage) {
        setStorage({
          totalBytes: settingsData.storage.total_bytes,
          usedBytes: settingsData.storage.used_bytes,
          percentage: settingsData.storage.percentage_used,
        })
      }

      // Load credentials status
      try {
        const credRes = await settingsAPI.getCredentials()
        setCredentials(credRes.data)
      } catch (e) {
        console.error('Error loading credentials:', e)
      }

      setIsLoading(false)
    } catch (error) {
      console.error('Error loading settings:', error)
      toast.error('Failed to load settings')
      setIsLoading(false)
    }
  }

  const providerLabels = {
    github: {
      label: 'GitHub',
      icon: '🔑',
      fields: {
        token: { label: 'Access Token', hint: 'Personal Access Token (Scopes: repo, gist)' }
      }
    },
    nas: {
      label: 'NAS / SMB',
      icon: '💾',
      fields: {
        password: { label: 'Passwort', hint: 'SMB/NFS Zugangspasswort' }
      }
    },
    supabase: {
      label: 'Supabase',
      icon: '⚡',
      fields: {
        db_password: { label: 'DB Passwort', hint: 'Datenbank-Passwort aus dem Supabase Dashboard' },
        service_role_key: { label: 'Service Role Key', hint: 'Für Storage & Config Backup' }
      }
    },
    smtp: {
      label: 'SMTP / E-Mail',
      icon: '📧',
      fields: {
        password: { label: 'Passwort', hint: 'E-Mail-Benachrichtigungspasswort' }
      }
    },
    telegram: {
      label: 'Telegram',
      icon: '📱',
      fields: {
        bot_token: { label: 'Bot Token', hint: 'Von @BotFather' }
      }
    },
    gdrive: {
      label: 'Google Drive',
      icon: '☁️',
      fields: {
        token: { label: 'OAuth Token', hint: 'rclone OAuth Token für Google Drive' }
      }
    },
  }

  const handleAddProfile = async () => {
    if (!newProfile.name.trim()) {
      toast.error('Profilname erforderlich')
      return
    }
    const hasValues = Object.values(newProfile.values || {}).some(v => v?.trim())
    if (!hasValues) {
      toast.error('Mindestens ein Feld ausfüllen')
      return
    }
    setIsSavingCredentials(true)
    try {
      await settingsAPI.addCredentialProfile(showAddProfile, newProfile.name, newProfile.values)
      toast.success(`Profil "${newProfile.name}" gespeichert`)
      setNewProfile({ name: '', values: {} })
      setShowAddProfile(null)
      const credRes = await settingsAPI.getCredentials()
      setCredentials(credRes.data)
    } catch (error) {
      toast.error(error.response?.data?.error || 'Fehler beim Speichern')
    } finally {
      setIsSavingCredentials(false)
    }
  }

  const handleDeleteProfile = async (provider, profile) => {
    if (!confirm(`Profil "${profile}" wirklich löschen?`)) return
    try {
      await settingsAPI.deleteCredentialProfile(provider, profile)
      toast.success(`Profil "${profile}" gelöscht`)
      const credRes = await settingsAPI.getCredentials()
      setCredentials(credRes.data)
    } catch (error) {
      toast.error(error.response?.data?.error || 'Fehler beim Löschen')
    }
  }

  const validatePassword = (password) => {
    if (password.length < 12) {
      return 'Password must be at least 12 characters long'
    }
    if (!/[A-Z]/.test(password)) {
      return 'Password must contain at least one uppercase letter'
    }
    if (!/[a-z]/.test(password)) {
      return 'Password must contain at least one lowercase letter'
    }
    if (!/\d/.test(password)) {
      return 'Password must contain at least one digit'
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      return 'Password must contain at least one special character'
    }
    return null
  }

  const handlePasswordChange = async (e) => {
    e.preventDefault()
    setPasswordError('')
    setPasswordSuccess(false)

    // Validate passwords match
    if (passwords.newPassword !== passwords.confirmPassword) {
      setPasswordError('Passwords do not match')
      return
    }

    // Validate password strength
    const validationError = validatePassword(passwords.newPassword)
    if (validationError) {
      setPasswordError(validationError)
      return
    }

    setIsSaving(true)
    try {
      // Call real API endpoint
      await authAPI.changePassword(passwords.newPassword)
      toast.success('Password changed successfully!')
      setPasswordSuccess(true)
      setPasswords({ newPassword: '', confirmPassword: '' })
      setTimeout(() => setPasswordSuccess(false), 5000)
    } catch (error) {
      console.error('Error changing password:', error)
      const errorMsg = error.response?.data?.error || 'Failed to change password'
      setPasswordError(errorMsg)
      toast.error(errorMsg)
    } finally {
      setIsSaving(false)
    }
  }

  const handleSettingsSave = async () => {
    setIsSaving(true)
    setSaveStatus(null)
    try {
      // Call real API endpoint
      await settingsAPI.update({
        backup_base_path: settings.backupBasePath,
        max_parallel_tasks: settings.maxParallelTasks,
        log_retention_days: settings.logRetention,
      })
      toast.success('Settings saved successfully!')
      setSaveStatus('success')
      setTimeout(() => setSaveStatus(null), 3000)
    } catch (error) {
      console.error('Error saving settings:', error)
      toast.error('Failed to save settings')
      setSaveStatus('error')
      setTimeout(() => setSaveStatus(null), 3000)
    } finally {
      setIsSaving(false)
    }
  }

  const handleClearBackupsClick = () => {
    setClearBackupsConfirm(true)
  }

  const handleClearBackupsConfirm = async () => {
    setIsClearing(true)
    try {
      const response = await backupAPI.deleteAll()
      toast.success(response.data.message ||'All backups deleted successfully')
      setClearBackupsConfirm(false)
      loadData()
    } catch (error) {
      console.error('Error clearing backups:', error)
      toast.error(error.response?.data?.error || 'Failed to clear backups')
    } finally {
      setIsClearing(false)
    }
  }

  const handleExport = async () => {
    const loadingToast = toast.loading('Exporting configuration...')
    try {
      const response = await configAPI.export()

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url

      // Generate filename with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0]
      link.setAttribute('download', `backupgenie_config_${timestamp}.json`)

      document.body.appendChild(link)
      link.click()
      link.parentNode.removeChild(link)
      window.URL.revokeObjectURL(url)

      toast.success('Configuration exported successfully!', { id: loadingToast })
    } catch (error) {
      console.error('Error exporting configuration:', error)
      toast.error(error.response?.data?.error || 'Failed to export configuration', { id: loadingToast })
    }
  }

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    setImportFile(file)
    setValidationResult(null)

    // Read and validate file
    const reader = new FileReader()
    reader.onload = async (event) => {
      try {
        const configData = JSON.parse(event.target.result)

        // Validate configuration
        const response = await configAPI.validate(configData)
        setValidationResult(response.data)

        if (response.data.valid) {
          toast.success('Configuration file is valid!')
        } else {
          toast.error('Configuration file has errors')
        }
      } catch (error) {
        console.error('Error validating file:', error)
        setValidationResult({
          valid: false,
          errors: ['Invalid JSON format or file is corrupted'],
          warnings: []
        })
        toast.error('Invalid configuration file')
      }
    }
    reader.readAsText(file)
  }

  const handleImport = async () => {
    if (!importFile || !validationResult?.valid) {
      toast.error('Please select a valid configuration file first')
      return
    }

    if (!confirm(`Are you sure you want to import this configuration? ${importMerge ? 'This will merge with' : 'This will replace'} your current settings.`)) {
      return
    }

    const loadingToast = toast.loading('Importing configuration...')
    try {
      const reader = new FileReader()
      reader.onload = async (event) => {
        try {
          const configData = JSON.parse(event.target.result)
          const response = await configAPI.import(configData, importMerge)

          toast.success(
            `Configuration imported! ${response.data.summary.sources_imported} sources imported.`,
            { id: loadingToast }
          )

          // Reset state
          setImportFile(null)
          setValidationResult(null)
          if (fileInputRef.current) {
            fileInputRef.current.value = ''
          }

          // Reload data
          loadData()
        } catch (error) {
          console.error('Error importing configuration:', error)
          toast.error(error.response?.data?.error || 'Failed to import configuration', { id: loadingToast })
        }
      }
      reader.readAsText(importFile)
    } catch (error) {
      console.error('Error reading file:', error)
      toast.error('Failed to read configuration file', { id: loadingToast })
    }
  }

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const getStorageColor = () => {
    if (storage.percentage < 60) return 'bg-green-600'
    if (storage.percentage < 80) return 'bg-yellow-600'
    return 'bg-red-600'
  }

  if (isLoading) {
    return (
      <div className="space-y-4 md:space-y-6">
        {/* Header Skeleton */}
        <div className="space-y-2">
          <div className="h-8 w-40 bg-gray-200 rounded animate-pulse"></div>
          <div className="h-4 w-64 bg-gray-200 rounded animate-pulse"></div>
        </div>

        {/* Settings Cards Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 bg-gray-200 rounded-lg animate-pulse"></div>
                <div className="h-6 w-32 bg-gray-200 rounded animate-pulse"></div>
              </div>
              <FormSkeleton />
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4 md:space-y-6">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">{t('settings.title')}</h1>
        <p className="text-sm md:text-base text-gray-600 mt-1">{t('settings.subtitle')}</p>
      </div>

      {saveStatus && (
        <div className={clsx(
          'p-3 md:p-4 rounded-lg text-sm md:text-base',
          saveStatus === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'
        )}>
          {saveStatus === 'success' ? t('settings.saved') : t('settings.error')}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        <div className="card">
          <div className="flex items-center gap-2 md:gap-3 mb-4 md:mb-6">
            <div className="p-1.5 md:p-2 bg-blue-100 rounded-lg shrink-0">
              <SettingsIcon className="w-5 h-5 md:w-6 md:h-6 text-blue-600" />
            </div>
            <h2 className="text-lg md:text-xl font-bold text-gray-900">{t('settings.general')}</h2>
          </div>
          <div className="space-y-3 md:space-y-4">
            <div>
              <label className="block text-xs md:text-sm font-medium text-gray-700 mb-2">{t('settings.backupBasePath')}</label>
              <input type="text" className="input" value={settings.backupBasePath} onChange={(e) => setSettings({...settings, backupBasePath: e.target.value})} />
              <p className="text-xs text-gray-500 mt-1">{t('settings.backupBasePathHint')}</p>
            </div>
            <div>
              <label className="block text-xs md:text-sm font-medium text-gray-700 mb-2">{t('settings.maxParallelTasks')}</label>
              <input type="number" className="input" value={settings.maxParallelTasks} onChange={(e) => setSettings({...settings, maxParallelTasks: parseInt(e.target.value)})} min="1" max="10" />
              <p className="text-xs text-gray-500 mt-1">Number of concurrent backup operations</p>
            </div>
            <div>
              <label className="block text-xs md:text-sm font-medium text-gray-700 mb-2">{t('settings.logRetention')}</label>
              <input type="number" className="input" value={settings.logRetention} onChange={(e) => setSettings({...settings, logRetention: parseInt(e.target.value)})} min="1" />
              <p className="text-xs text-gray-500 mt-1">How long to keep backup logs</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-2 md:gap-3 mb-4 md:mb-6">
            <div className="p-1.5 md:p-2 bg-green-100 rounded-lg shrink-0">
              <User className="w-5 h-5 md:w-6 md:h-6 text-green-600" />
            </div>
            <h2 className="text-lg md:text-xl font-bold text-gray-900">{t('settings.user')}</h2>
          </div>
          <form onSubmit={handlePasswordChange} className="space-y-3 md:space-y-4">
            <div>
              <label className="block text-xs md:text-sm font-medium text-gray-700 mb-2">{t('settings.username')}</label>
              <input type="text" className="input" value={user?.username || 'admin'} disabled />
            </div>
            <div>
              <label className="block text-xs md:text-sm font-medium text-gray-700 mb-2">{t('settings.newPassword')}</label>
              <input type="password" className="input" placeholder={t('settings.newPassword')} value={passwords.newPassword} onChange={(e) => setPasswords({...passwords, newPassword: e.target.value})} />
            </div>
            <div>
              <label className="block text-xs md:text-sm font-medium text-gray-700 mb-2">{t('settings.confirmPassword')}</label>
              <input type="password" className="input" placeholder={t('settings.confirmPassword')} value={passwords.confirmPassword} onChange={(e) => setPasswords({...passwords, confirmPassword: e.target.value})} />
            </div>
            {passwordError && <p className="text-xs md:text-sm text-red-600">{passwordError}</p>}
            {passwordSuccess && <p className="text-xs md:text-sm text-green-600">Password changed successfully!</p>}
            <button type="submit" className="btn btn-primary w-full flex items-center justify-center gap-2" disabled={isSaving || !passwords.newPassword || !passwords.confirmPassword}>
              {isSaving ? <><Loader className="w-4 h-4 md:w-5 md:h-5 animate-spin" /><span className="text-sm md:text-base">{t('settings.saving')}</span></> : <span className="text-sm md:text-base">{t('settings.save')}</span>}
            </button>
          </form>
        </div>

        <div className="card">
          <div className="flex items-center gap-2 md:gap-3 mb-4 md:mb-6">
            <div className="p-1.5 md:p-2 bg-red-100 rounded-lg shrink-0">
              <Shield className="w-5 h-5 md:w-6 md:h-6 text-red-600" />
            </div>
            <h2 className="text-lg md:text-xl font-bold text-gray-900">Security</h2>
          </div>
          <div className="space-y-3 md:space-y-4">
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0 flex-1">
                <p className="text-sm md:text-base font-medium text-gray-900 truncate">API Authentication</p>
                <p className="text-xs md:text-sm text-gray-600">Require token for API access</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer shrink-0">
                <input type="checkbox" className="sr-only peer" checked={settings.apiAuth} disabled />
                <div className="w-9 h-5 md:w-11 md:h-6 bg-gray-200 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:rounded-full after:h-4 after:w-4 md:after:h-5 md:after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0 flex-1">
                <p className="text-sm md:text-base font-medium text-gray-900 truncate">HTTPS Only</p>
                <p className="text-xs md:text-sm text-gray-600">Enforce secure connections</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer shrink-0">
                <input type="checkbox" className="sr-only peer" checked={settings.httpsOnly} onChange={(e) => setSettings({...settings, httpsOnly: e.target.checked})} />
                <div className="w-9 h-5 md:w-11 md:h-6 bg-gray-200 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:rounded-full after:h-4 after:w-4 md:after:h-5 md:after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Credentials Card */}
        <div className="card lg:col-span-2">
          <div className="flex items-center gap-2 md:gap-3 mb-4 md:mb-6">
            <div className="p-1.5 md:p-2 bg-amber-100 rounded-lg shrink-0">
              <Key className="w-5 h-5 md:w-6 md:h-6 text-amber-600" />
            </div>
            <div>
              <h2 className="text-lg md:text-xl font-bold text-gray-900">{t('settings.credentials.title')}</h2>
              <p className="text-xs text-gray-500">{t('settings.credentials.subtitle')}</p>
            </div>
          </div>
          <div className="space-y-4">
            {Object.entries(providerLabels).map(([provider, meta]) => (
              <div key={provider} className="border border-gray-200 rounded-lg p-3 md:p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-semibold text-gray-800">
                    <span className="mr-2">{meta.icon}</span>{meta.label}
                  </h3>
                  <button
                    onClick={() => {
                      setShowAddProfile(showAddProfile === provider ? null : provider)
                      setNewProfile({ name: '', values: {} })
                    }}
                    className="text-xs flex items-center gap-1 text-primary-600 hover:text-primary-800"
                  >
                    {showAddProfile === provider ? <X className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
                    {showAddProfile === provider ? 'Abbrechen' : 'Profil hinzufügen'}
                  </button>
                </div>

                {/* Existing profiles */}
                {credentials[provider]?.profiles?.length > 0 ? (
                  <div className="space-y-2">
                    {credentials[provider].profiles.map((p) => (
                      <div key={p.profile} className="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2">
                        <span className="text-sm font-medium text-gray-700 flex-1">{p.profile}</span>
                        {p.fields && (
                          <div className="flex gap-1">
                            {Object.entries(p.fields).map(([field, configured]) => (
                              <span key={field} className={`text-xs px-1.5 py-0.5 rounded ${configured ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'}`}>
                                {meta.fields[field]?.label || field}
                              </span>
                            ))}
                          </div>
                        )}
                        <span className="text-xs text-gray-400">{p.source}</span>
                        {p.source === 'database' && (
                          <button
                            onClick={() => handleDeleteProfile(provider, p.profile)}
                            className="text-gray-400 hover:text-red-500"
                            title="Profil löschen"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-gray-400 italic mt-1">Kein Profil konfiguriert</p>
                )}

                {/* Add new profile form */}
                {showAddProfile === provider && (
                  <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg space-y-3">
                    <input
                      type="text"
                      className="input text-sm"
                      placeholder="Profilname (z.B. Privat, Arbeit, Server-1)"
                      value={newProfile.name}
                      onChange={(e) => setNewProfile({...newProfile, name: e.target.value})}
                    />
                    {Object.entries(meta.fields).map(([field, fieldMeta]) => (
                      <div key={field}>
                        <label className="block text-xs font-medium text-gray-600 mb-1">{fieldMeta.label}</label>
                        <div className="relative">
                          <input
                            type={credentialVisibility[`${provider}_${field}`] ? 'text' : 'password'}
                            className="input text-sm pr-10"
                            placeholder={fieldMeta.hint}
                            value={newProfile.values?.[field] || ''}
                            onChange={(e) => setNewProfile({
                              ...newProfile,
                              values: { ...newProfile.values, [field]: e.target.value }
                            })}
                          />
                          <button
                            type="button"
                            onClick={() => setCredentialVisibility({...credentialVisibility, [`${provider}_${field}`]: !credentialVisibility[`${provider}_${field}`]})}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                          >
                            {credentialVisibility[`${provider}_${field}`] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        </div>
                      </div>
                    ))}
                    <button
                      onClick={handleAddProfile}
                      className="btn btn-primary text-sm w-full flex items-center justify-center gap-2"
                      disabled={isSavingCredentials || !newProfile.name.trim()}
                    >
                      {isSavingCredentials ? (
                        <Loader className="w-4 h-4 animate-spin" />
                      ) : (
                        <><Key className="w-4 h-4" /><span>Profil speichern</span></>
                      )}
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-2 md:gap-3 mb-4 md:mb-6">
            <div className="p-1.5 md:p-2 bg-purple-100 rounded-lg shrink-0">
              <Database className="w-5 h-5 md:w-6 md:h-6 text-purple-600" />
            </div>
            <h2 className="text-lg md:text-xl font-bold text-gray-900">Storage</h2>
          </div>
          <div className="space-y-3 md:space-y-4">
            <div className="p-3 md:p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs md:text-sm text-gray-600">Used Space</span>
                <span className="text-sm md:text-base font-medium text-gray-900">
                  {formatBytes(storage.usedBytes)} / {formatBytes(storage.totalBytes)}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className={clsx('h-2 rounded-full transition-all', getStorageColor())} style={{ width: `${Math.min(storage.percentage, 100)}%` }}></div>
              </div>
              <p className="text-xs text-gray-500 mt-1">{storage.percentage}% used</p>
            </div>
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0 flex-1">
                <p className="text-sm md:text-base font-medium text-gray-900 truncate">Auto Cleanup</p>
                <p className="text-xs md:text-sm text-gray-600">Delete old backups automatically</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer shrink-0">
                <input type="checkbox" className="sr-only peer" checked={settings.autoCleanup} onChange={(e) => setSettings({...settings, autoCleanup: e.target.checked})} />
                <div className="w-9 h-5 md:w-11 md:h-6 bg-gray-200 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:rounded-full after:h-4 after:w-4 md:after:h-5 md:after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>
            <button onClick={handleClearBackupsClick} className="btn btn-danger w-full flex items-center justify-center gap-2" disabled={isSaving}>
              <span className="text-sm md:text-base">Clear All Backups</span>
            </button>
          </div>
        </div>

        {/* Export/Import Configuration Card */}
        <div className="card lg:col-span-2">
          <div className="flex items-center gap-2 md:gap-3 mb-4 md:mb-6">
            <div className="p-1.5 md:p-2 bg-indigo-100 rounded-lg shrink-0">
              <FileJson className="w-5 h-5 md:w-6 md:h-6 text-indigo-600" />
            </div>
            <h2 className="text-lg md:text-xl font-bold text-gray-900">Configuration Export/Import</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
            {/* Export Section */}
            <div className="space-y-3 md:space-y-4">
              <h3 className="text-base md:text-lg font-semibold text-gray-800">Export</h3>
              <p className="text-xs md:text-sm text-gray-600">
                Download all your sources, settings, and configurations as a JSON file for backup or migration.
              </p>
              <button
                onClick={handleExport}
                className="btn btn-primary w-full flex items-center justify-center gap-2"
                disabled={isSaving}
              >
                <Download className="w-4 h-4 md:w-5 md:h-5" />
                <span className="text-sm md:text-base">Export Configuration</span>
              </button>
            </div>

            {/* Import Section */}
            <div className="space-y-3 md:space-y-4">
              <h3 className="text-base md:text-lg font-semibold text-gray-800">Import</h3>
              <p className="text-xs md:text-sm text-gray-600">
                Upload a previously exported configuration file to restore your settings.
              </p>

              <input
                ref={fileInputRef}
                type="file"
                accept=".json"
                onChange={handleFileSelect}
                className="hidden"
              />

              <button
                onClick={() => fileInputRef.current?.click()}
                className="btn btn-secondary w-full flex items-center justify-center gap-2"
                disabled={isSaving}
              >
                <Upload className="w-4 h-4 md:w-5 md:h-5" />
                <span className="text-sm md:text-base">
                  {importFile ? `Selected: ${importFile.name}` : 'Choose File'}
                </span>
              </button>

              {validationResult && (
                <div className={clsx(
                  'p-3 rounded-lg text-xs md:text-sm',
                  validationResult.valid
                    ? 'bg-green-50 border border-green-200'
                    : 'bg-red-50 border border-red-200'
                )}>
                  <div className="flex items-start gap-2 mb-2">
                    {validationResult.valid ? (
                      <CheckCircle className="w-4 h-4 text-green-600 shrink-0 mt-0.5" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className={clsx('font-semibold', validationResult.valid ? 'text-green-800' : 'text-red-800')}>
                        {validationResult.valid ? 'Valid Configuration' : 'Invalid Configuration'}
                      </p>
                      {validationResult.summary && (
                        <p className="text-gray-700 mt-1">
                          {validationResult.summary.total_sources} sources found
                        </p>
                      )}
                    </div>
                  </div>

                  {validationResult.errors?.length > 0 && (
                    <div className="mt-2">
                      <p className="font-medium text-red-800 mb-1">Errors:</p>
                      <ul className="list-disc list-inside text-red-700 space-y-1">
                        {validationResult.errors.map((error, i) => (
                          <li key={i} className="break-words">{error}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {validationResult.warnings?.length > 0 && (
                    <div className="mt-2">
                      <p className="font-medium text-yellow-800 mb-1">Warnings:</p>
                      <ul className="list-disc list-inside text-yellow-700 space-y-1">
                        {validationResult.warnings.map((warning, i) => (
                          <li key={i} className="break-words">{warning}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {importFile && validationResult?.valid && (
                <>
                  <div className="flex items-center gap-3">
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={importMerge}
                        onChange={(e) => setImportMerge(e.target.checked)}
                      />
                      <div className="w-9 h-5 md:w-11 md:h-6 bg-gray-200 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:rounded-full after:h-4 after:w-4 md:after:h-5 md:after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                    <div>
                      <p className="text-sm md:text-base font-medium text-gray-900">Merge Mode</p>
                      <p className="text-xs text-gray-600">
                        {importMerge ? 'Add to existing sources' : 'Replace all sources'}
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={handleImport}
                    className="btn btn-primary w-full flex items-center justify-center gap-2"
                    disabled={isSaving}
                  >
                    {isSaving ? (
                      <>
                        <Loader className="w-4 h-4 md:w-5 md:h-5 animate-spin" />
                        <span className="text-sm md:text-base">Importing...</span>
                      </>
                    ) : (
                      <>
                        <Upload className="w-4 h-4 md:w-5 md:h-5" />
                        <span className="text-sm md:text-base">Import Configuration</span>
                      </>
                    )}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button onClick={handleSettingsSave} className="btn btn-primary px-6 md:px-8 flex items-center gap-2" disabled={isSaving}>
          {isSaving ? <><Loader className="w-4 h-4 md:w-5 md:h-5 animate-spin" /><span className="text-sm md:text-base">{t('settings.saving')}</span></> : <><Save className="w-4 h-4 md:w-5 md:h-5" /><span className="text-sm md:text-base">{t('settings.save')}</span></>}
        </button>
      </div>

      {/* Clear Backups Confirmation Dialog */}
      <ConfirmDialog
        isOpen={clearBackupsConfirm}
        onClose={() => setClearBackupsConfirm(false)}
        onConfirm={handleClearBackupsConfirm}
        title="Delete All Backups?"
        message="This will permanently delete all backup records from the database. This action cannot be undone. Your backup files will remain on disk."
        confirmText="Delete All Backups"
        confirmVariant="danger"
        isLoading={isClearing}
      />
    </div>
  )
}
