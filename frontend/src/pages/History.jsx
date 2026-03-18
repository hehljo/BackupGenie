import { useState, useEffect } from 'react'
import { Clock, CheckCircle, XCircle, AlertCircle, ChevronDown, ChevronUp, FileText } from 'lucide-react'
import { backupAPI } from '../services/api'
import clsx from 'clsx'
import { formatDistanceToNow } from 'date-fns'
import { useTranslation } from 'react-i18next'

export default function History() {
  const { t } = useTranslation()
  const [backups, setBackups] = useState([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [page, setPage] = useState(0)
  const [expandedLogs, setExpandedLogs] = useState({})
  const limit = 10

  useEffect(() => {
    loadHistory()
  }, [page])

  const loadHistory = async () => {
    setIsLoading(true)
    try {
      const response = await backupAPI.getHistory(limit, page * limit)
      setBackups(response.data.backups)
      setTotal(response.data.total)
      setIsLoading(false)
    } catch (error) {
      console.error('Error loading history:', error)
      setIsLoading(false)
    }
  }

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const formatDuration = (seconds) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`
    }
    return `${secs}s`
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />
      case 'partial':
        return <AlertCircle className="w-5 h-5 text-yellow-600" />
      default:
        return <Clock className="w-5 h-5 text-blue-600" />
    }
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
    <div className="space-y-4 md:space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">{t('history.title')}</h1>
        <p className="text-sm md:text-base text-gray-600 mt-1">{t('history.subtitle')}</p>
      </div>

      {/* History List */}
      <div className="space-y-3 md:space-y-4">
        {backups.map((backup) => (
          <div key={backup.backup_id} className="card">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                {getStatusIcon(backup.status)}
                <div>
                  <p className="font-semibold text-gray-900">
                    Backup {backup.backup_id.substring(0, 8)}
                  </p>
                  <p className="text-sm text-gray-600">
                    {formatDistanceToNow(new Date(backup.started_at), { addSuffix: true })}
                  </p>
                </div>
              </div>
              <span className={clsx('badge', getStatusBadge(backup.status))}>
                {t(`dashboard.status.${backup.status}`)}
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 mb-3 md:mb-4">
              <div>
                <p className="text-xs md:text-sm text-gray-600">{t('history.started')}</p>
                <p className="text-sm md:text-base font-medium text-gray-900 truncate">
                  {new Date(backup.started_at).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-xs md:text-sm text-gray-600">{t('history.duration')}</p>
                <p className="text-sm md:text-base font-medium text-gray-900">
                  {backup.duration ? formatDuration(backup.duration) : 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-xs md:text-sm text-gray-600">{t('history.sources')}</p>
                <p className="text-sm md:text-base font-medium text-gray-900">{backup.sources_count}</p>
              </div>
              <div>
                <p className="text-xs md:text-sm text-gray-600">{t('history.totalSize')}</p>
                <p className="text-sm md:text-base font-medium text-gray-900">{formatBytes(backup.total_size)}</p>
              </div>
            </div>

            {backup.sources && backup.sources.length > 0 && (
              <div className="border-t border-gray-200 pt-4">
                <p className="text-sm font-medium text-gray-700 mb-3">{t('history.sourceDetails')}</p>
                <div className="space-y-2">
                  {backup.sources.map((source) => (
                    <div key={source.source_id} className="bg-gray-50 rounded-lg overflow-hidden">
                      <div className="flex items-center justify-between text-sm p-3">
                        <div className="flex items-center gap-3">
                          <div className={clsx(
                            'w-2 h-2 rounded-full',
                            source.status === 'completed' ? 'bg-green-500' :
                            source.status === 'failed' ? 'bg-red-500' :
                            'bg-blue-500'
                          )}></div>
                          <span className="font-medium">{source.source_name}</span>
                          <span className="text-gray-500">({source.source_type})</span>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="text-gray-600">
                            {source.files_synced} files • {formatBytes(source.size_synced)}
                          </span>
                          <span className={clsx('badge text-xs', getStatusBadge(source.status))}>
                            {t(`dashboard.status.${source.status}`)}
                          </span>
                          {(source.logs || source.error_message) && (
                            <button
                              onClick={() => setExpandedLogs(prev => ({
                                ...prev,
                                [`${backup.backup_id}-${source.source_id}`]: !prev[`${backup.backup_id}-${source.source_id}`]
                              }))}
                              className="text-gray-400 hover:text-gray-600"
                            >
                              {expandedLogs[`${backup.backup_id}-${source.source_id}`] ? (
                                <ChevronUp className="w-4 h-4" />
                              ) : (
                                <ChevronDown className="w-4 h-4" />
                              )}
                            </button>
                          )}
                        </div>
                      </div>
                      {expandedLogs[`${backup.backup_id}-${source.source_id}`] && (
                        <div className="border-t border-gray-200 p-3">
                          {source.error_message && (
                            <div className="mb-2 p-2 bg-red-50 rounded text-xs text-red-700 font-mono">
                              {source.error_message}
                            </div>
                          )}
                          {source.logs && (
                            <pre className="text-xs text-gray-600 font-mono whitespace-pre-wrap max-h-48 overflow-y-auto bg-white p-2 rounded border">
                              {source.logs}
                            </pre>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {backups.length === 0 && (
        <div className="card text-center py-12">
          <Clock className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">{t('history.noHistory')}</h3>
          <p className="text-gray-600">{t('dashboard.startBackup')}</p>
        </div>
      )}

      {/* Pagination */}
      {total > limit && (
        <div className="flex flex-col sm:flex-row items-center justify-center gap-2 md:gap-3">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="btn btn-secondary disabled:opacity-50 w-full sm:w-auto"
          >
            {t('history.previous')}
          </button>
          <span className="text-sm md:text-base text-gray-600">
            {t('history.page', { current: page + 1, total: Math.ceil(total / limit) })}
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={(page + 1) * limit >= total}
            className="btn btn-secondary disabled:opacity-50 w-full sm:w-auto"
          >
            {t('history.next')}
          </button>
        </div>
      )}
    </div>
  )
}
