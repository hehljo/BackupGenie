import { useState, useEffect } from 'react'
import { Play, Clock, CheckCircle, XCircle, HardDrive, Database } from 'lucide-react'
import { backupAPI, sourcesAPI } from '../services/api'
import clsx from 'clsx'
import { useTranslation } from 'react-i18next'

export default function Dashboard() {
  const { t } = useTranslation()
  const [stats, setStats] = useState(null)
  const [sources, setSources] = useState([])
  const [isStarting, setIsStarting] = useState(false)
  const [recentBackups, setRecentBackups] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 10000) // Refresh every 10 seconds
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      const [statsRes, sourcesRes, historyRes] = await Promise.all([
        backupAPI.getStats(),
        sourcesAPI.getAll(),
        backupAPI.getHistory(5, 0)
      ])

      setStats(statsRes.data)
      setSources(sourcesRes.data.sources)
      setRecentBackups(historyRes.data.backups)
      setIsLoading(false)
    } catch (error) {
      console.error('Error loading data:', error)
      setIsLoading(false)
    }
  }

  const handleStartBackup = async () => {
    setIsStarting(true)
    try {
      await backupAPI.start({ parallel: 2, notify: true })
      setTimeout(loadData, 2000) // Reload after 2 seconds
    } catch (error) {
      console.error('Error starting backup:', error)
      alert(t('common.error'))
    } finally {
      setIsStarting(false)
    }
  }

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const getStatusBadge = (status) => {
    const badges = {
      completed: 'badge-success',
      running: 'badge-info',
      failed: 'badge-error',
      partial: 'badge-warning',
    }
    return badges[status] || 'badge-info'
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">{t('common.loading')}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{t('dashboard.title')}</h1>
          <p className="text-gray-600 mt-1">{t('dashboard.subtitle')}</p>
        </div>
        <button
          onClick={handleStartBackup}
          disabled={isStarting || stats?.running > 0}
          className={clsx(
            'btn btn-primary flex items-center gap-2',
            (isStarting || stats?.running > 0) && 'opacity-50 cursor-not-allowed'
          )}
        >
          <Play className="w-5 h-5" />
          {isStarting ? t('common.loading') : t('dashboard.startBackup')}
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">{t('dashboard.stats.totalBackups')}</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {stats?.total_backups || 0}
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <HardDrive className="w-8 h-8 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">{t('dashboard.stats.successful')}</p>
              <p className="text-3xl font-bold text-green-600 mt-2">
                {stats?.successful || 0}
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">{t('dashboard.stats.failed')}</p>
              <p className="text-3xl font-bold text-red-600 mt-2">
                {stats?.failed || 0}
              </p>
            </div>
            <div className="p-3 bg-red-100 rounded-lg">
              <XCircle className="w-8 h-8 text-red-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">{t('dashboard.stats.totalSize')}</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {formatBytes(stats?.total_size_bytes || 0)}
              </p>
            </div>
            <div className="p-3 bg-purple-100 rounded-lg">
              <Database className="w-8 h-8 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Sources Overview */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">{t('dashboard.backupSources')}</h2>
        <div className="space-y-3">
          {sources.filter(s => s.enabled).map((source) => (
            <div key={source.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className={clsx(
                  'w-3 h-3 rounded-full',
                  source.enabled ? 'bg-green-500' : 'bg-gray-300'
                )}></div>
                <div>
                  <p className="font-medium text-gray-900">{source.name}</p>
                  <p className="text-sm text-gray-600">{source.type.toUpperCase()}</p>
                </div>
              </div>
              <span className="badge badge-success">{t('dashboard.active')}</span>
            </div>
          ))}
          {sources.filter(s => s.enabled).length === 0 && (
            <p className="text-gray-500 text-center py-4">{t('dashboard.noSources')}</p>
          )}
        </div>
      </div>

      {/* Recent Backups */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">{t('dashboard.recentBackups')}</h2>
        <div className="space-y-3">
          {recentBackups.map((backup) => (
            <div key={backup.backup_id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-4">
                <Clock className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="font-medium text-gray-900">
                    {new Date(backup.started_at).toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-600">
                    {backup.sources_count} {t('dashboard.recentBackups').toLowerCase()} • {formatBytes(backup.total_size)}
                  </p>
                </div>
              </div>
              <span className={clsx('badge', getStatusBadge(backup.status))}>
                {t(`dashboard.status.${backup.status}`)}
              </span>
            </div>
          ))}
          {recentBackups.length === 0 && (
            <p className="text-gray-500 text-center py-4">{t('dashboard.noBackups')}</p>
          )}
        </div>
      </div>
    </div>
  )
}
