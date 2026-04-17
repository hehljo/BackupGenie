import { useState, useEffect, useCallback } from 'react'
import {
  Archive, Search, Filter, RotateCcw, CheckCircle, XCircle, AlertCircle,
  Clock, ChevronDown, ChevronUp, FileText, X, Loader2, Eye, EyeOff,
  HardDrive, Database, RefreshCw, Calendar, SlidersHorizontal
} from 'lucide-react'
import { backupAPI, restoreAPI, settingsAPI } from '../services/api'
import clsx from 'clsx'
import { formatDistanceToNow, format } from 'date-fns'
import { useTranslation } from 'react-i18next'
import ConfirmDialog from '../components/ConfirmDialog'

const STATUS_ALL = 'all'
const STATUS_RESTORABLE = 'restorable'

const RESTORABLE_TYPES = ['supabase']

export default function Backups() {
  const { t } = useTranslation()

  // Data
  const [allBackups, setAllBackups] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const limit = 50

  // Filters
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState(STATUS_ALL)
  const [typeFilter, setTypeFilter] = useState(STATUS_ALL)
  const [quickFilter, setQuickFilter] = useState(null) // 'restorable' | null
  const [expandedLogs, setExpandedLogs] = useState({})

  // Restore
  const [restoreModal, setRestoreModal] = useState(null)
  const [restoreBackups, setRestoreBackups] = useState([])
  const [restoreLoading, setRestoreLoading] = useState(false)
  const [restoreForm, setRestoreForm] = useState({
    backup_path: '', profile: '', target_connection_string: '',
    target_db_password: '', restore_storage: false, target_service_role_key: '',
  })
  const [supabaseProfiles, setSupabaseProfiles] = useState([])
  const [useManualConnection, setUseManualConnection] = useState(false)
  const [showRestorePassword, setShowRestorePassword] = useState(false)
  const [showServiceKey, setShowServiceKey] = useState(false)
  const [restoreStatus, setRestoreStatus] = useState(null)
  const [restoreResult, setRestoreResult] = useState(null)
  const [confirmRestore, setConfirmRestore] = useState(false)

  useEffect(() => { loadBackups() }, [page])

  const loadBackups = async () => {
    setIsLoading(true)
    try {
      const res = await backupAPI.getHistory(limit, page * limit)
      setAllBackups(res.data.backups || [])
      setTotal(res.data.total || 0)
    } catch (e) {
      console.error(e)
    }
    setIsLoading(false)
  }

  // ── Derived: flatten to source-level rows ──────────────────────────────────
  const rows = []
  for (const backup of allBackups) {
    if (!backup.sources?.length) {
      rows.push({ backup, source: null })
    } else {
      for (const source of backup.sources) {
        rows.push({ backup, source })
      }
    }
  }

  const sourceTypes = [...new Set(rows.map(r => r.source?.source_type).filter(Boolean))]

  const filtered = rows.filter(({ backup, source }) => {
    const q = search.toLowerCase()
    if (q) {
      const name = source?.source_name || ''
      const type = source?.source_type || ''
      const id = backup.backup_id || ''
      if (!name.toLowerCase().includes(q) && !type.toLowerCase().includes(q) && !id.includes(q)) return false
    }
    if (statusFilter !== STATUS_ALL) {
      const s = source ? source.status : backup.status
      if (s !== statusFilter) return false
    }
    if (typeFilter !== STATUS_ALL && source?.source_type !== typeFilter) return false
    if (quickFilter === STATUS_RESTORABLE) {
      if (!source || !RESTORABLE_TYPES.includes(source.source_type)) return false
      if (source.status !== 'completed') return false
    }
    return true
  })

  // Group by source name for display
  const grouped = {}
  for (const row of filtered) {
    const key = row.source?.source_name || row.backup.backup_id
    if (!grouped[key]) grouped[key] = { sourceName: key, sourceType: row.source?.source_type || 'unknown', rows: [] }
    grouped[key].rows.push(row)
  }
  const groups = Object.values(grouped)

  // ── Restore ────────────────────────────────────────────────────────────────
  const openRestoreModal = async (sourceId, sourceType) => {
    setRestoreModal({ sourceId, sourceType })
    setRestoreLoading(true)
    setRestoreStatus(null)
    setRestoreResult(null)
    setUseManualConnection(false)
    setRestoreForm({ backup_path: '', profile: '', target_connection_string: '', target_db_password: '', restore_storage: false, target_service_role_key: '' })

    try {
      const [restoresRes, credsRes] = await Promise.all([
        restoreAPI.getAvailable(sourceId),
        settingsAPI.getCredentials().catch(() => ({ data: {} })),
      ])
      const backupList = restoresRes.data.backups || []
      const profiles = credsRes.data?.supabase?.profiles || []
      setRestoreBackups(backupList)
      setSupabaseProfiles(profiles)
      setRestoreForm(prev => ({
        ...prev,
        backup_path: backupList[0]?.path || '',
        profile: profiles[0]?.profile || '',
      }))
    } catch (e) {
      setRestoreBackups([])
    }
    setRestoreLoading(false)
  }

  const handleRestore = async () => {
    setConfirmRestore(false)
    setRestoreStatus('starting')
    try {
      const res = await restoreAPI.start(restoreForm)
      const restoreId = res.data.restore_id
      setRestoreStatus('running')

      const pollInterval = setInterval(async () => {
        try {
          const s = await restoreAPI.getStatus(restoreId)
          const data = s.data
          if (data.logs) setRestoreResult(prev => ({ ...prev, logs: data.logs }))
          if (data.status !== 'running') {
            clearInterval(pollInterval)
            setRestoreStatus(data.status)
            setRestoreResult(data)
          }
        } catch (_) {}
      }, 2000)
    } catch (error) {
      setRestoreStatus('failed')
      setRestoreResult({ error: error.response?.data?.error || 'Restore fehlgeschlagen' })
    }
  }

  // ── Helpers ────────────────────────────────────────────────────────────────
  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B'
    const k = 1024, sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return (bytes / Math.pow(k, i)).toFixed(1) + ' ' + sizes[i]
  }

  const formatDuration = (s) => {
    if (!s) return '—'
    const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60
    if (h > 0) return `${h}h ${m}m`
    if (m > 0) return `${m}m ${sec}s`
    return `${sec}s`
  }

  const statusIcon = (status, size = 'w-4 h-4') => {
    switch (status) {
      case 'completed': return <CheckCircle className={clsx(size, 'text-green-600')} />
      case 'failed':    return <XCircle className={clsx(size, 'text-red-600')} />
      case 'partial':   return <AlertCircle className={clsx(size, 'text-yellow-600')} />
      default:          return <Clock className={clsx(size, 'text-blue-600')} />
    }
  }

  const statusBadge = (status) => ({
    completed: 'badge-success', running: 'badge-info', failed: 'badge-error', partial: 'badge-warning',
  }[status] || 'badge-info')

  const typeIcon = (type) => {
    if (type === 'supabase') return <Database className="w-4 h-4 text-emerald-600" />
    return <HardDrive className="w-4 h-4 text-gray-400" />
  }

  const restorableCount = rows.filter(r => r.source && RESTORABLE_TYPES.includes(r.source.source_type) && r.source.status === 'completed').length

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">{t('backups.title')}</h1>
          <p className="text-sm text-gray-500 mt-1">{t('backups.subtitle')}</p>
        </div>
        <button onClick={loadBackups} className="btn btn-secondary flex items-center gap-2">
          <RefreshCw className="w-4 h-4" />
          {t('common.refresh')}
        </button>
      </div>

      {/* Quick Filters */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setQuickFilter(null)}
          className={clsx('px-3 py-1.5 rounded-full text-sm font-medium transition-colors',
            !quickFilter ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          )}
        >
          {t('backups.filterAll')} <span className="ml-1 opacity-70">{rows.length}</span>
        </button>
        <button
          onClick={() => setQuickFilter(STATUS_RESTORABLE)}
          className={clsx('px-3 py-1.5 rounded-full text-sm font-medium transition-colors flex items-center gap-1.5',
            quickFilter === STATUS_RESTORABLE ? 'bg-emerald-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          )}
        >
          <RotateCcw className="w-3.5 h-3.5" />
          {t('backups.filterRestorable')} <span className="ml-1 opacity-70">{restorableCount}</span>
        </button>
      </div>

      {/* Search + Filters */}
      <div className="card p-4 space-y-3">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              className="input pl-9"
              placeholder={t('backups.searchPlaceholder')}
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            {search && (
              <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          <select
            className="input sm:w-40"
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
          >
            <option value={STATUS_ALL}>{t('backups.allStatuses')}</option>
            <option value="completed">{t('dashboard.status.completed')}</option>
            <option value="failed">{t('dashboard.status.failed')}</option>
            <option value="partial">{t('dashboard.status.partial')}</option>
          </select>

          <select
            className="input sm:w-40"
            value={typeFilter}
            onChange={e => setTypeFilter(e.target.value)}
          >
            <option value={STATUS_ALL}>{t('backups.allTypes')}</option>
            {sourceTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>

        {(search || statusFilter !== STATUS_ALL || typeFilter !== STATUS_ALL || quickFilter) && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <SlidersHorizontal className="w-4 h-4" />
            <span>{filtered.length} {t('backups.resultsOf')} {rows.length}</span>
            <button
              onClick={() => { setSearch(''); setStatusFilter(STATUS_ALL); setTypeFilter(STATUS_ALL); setQuickFilter(null) }}
              className="text-primary-600 hover:underline"
            >
              {t('backups.resetFilters')}
            </button>
          </div>
        )}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
        </div>
      ) : groups.length === 0 ? (
        <div className="card text-center py-14">
          <Archive className="w-14 h-14 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900">{t('backups.noResults')}</h3>
          <p className="text-sm text-gray-500 mt-1">{t('backups.noResultsHint')}</p>
        </div>
      ) : (
        <div className="space-y-4">
          {groups.map(group => (
            <div key={group.sourceName} className="card overflow-hidden">
              {/* Group Header */}
              <div className="flex items-center gap-3 px-5 py-3 bg-gray-50 border-b border-gray-100">
                {typeIcon(group.sourceType)}
                <span className="font-semibold text-gray-900">{group.sourceName}</span>
                <span className="text-xs text-gray-400 bg-gray-200 rounded-full px-2 py-0.5">{group.sourceType}</span>
                <span className="ml-auto text-xs text-gray-400">{group.rows.length} {t('backups.entries')}</span>
              </div>

              {/* Rows */}
              <div className="divide-y divide-gray-100">
                {group.rows.map(({ backup, source }) => {
                  const status = source ? source.status : backup.status
                  const logKey = source ? `${backup.backup_id}-${source.source_id}` : backup.backup_id
                  const isRestorable = source && RESTORABLE_TYPES.includes(source.source_type) && source.status === 'completed'

                  return (
                    <div key={logKey} className="px-5 py-3">
                      <div className="flex items-center gap-3 flex-wrap">
                        {statusIcon(status)}

                        {/* Date */}
                        <div className="flex items-center gap-1.5 text-sm text-gray-700 min-w-[140px]">
                          <Calendar className="w-3.5 h-3.5 text-gray-400" />
                          <span title={format(new Date(backup.started_at), 'dd.MM.yyyy HH:mm:ss')}>
                            {formatDistanceToNow(new Date(backup.started_at), { addSuffix: true })}
                          </span>
                        </div>

                        {/* Stats */}
                        <div className="flex items-center gap-4 text-xs text-gray-500 flex-1">
                          {source ? (
                            <>
                              <span>{source.files_synced ?? '—'} files</span>
                              <span>{formatBytes(source.size_synced)}</span>
                            </>
                          ) : (
                            <>
                              <span>{backup.sources_count} sources</span>
                              <span>{formatBytes(backup.total_size)}</span>
                              <span>{formatDuration(backup.duration)}</span>
                            </>
                          )}
                        </div>

                        {/* Badge + Actions */}
                        <div className="flex items-center gap-2">
                          <span className={clsx('badge text-xs', statusBadge(status))}>
                            {t(`dashboard.status.${status}`)}
                          </span>

                          {isRestorable && (
                            <button
                              onClick={() => openRestoreModal(source.source_id, source.source_type)}
                              className="flex items-center gap-1 text-xs font-medium text-emerald-700 hover:text-emerald-900 bg-emerald-50 hover:bg-emerald-100 px-2 py-1 rounded-md transition-colors"
                            >
                              <RotateCcw className="w-3 h-3" />
                              Restore
                            </button>
                          )}

                          {(source?.logs || source?.error_message || backup.error_message) && (
                            <button
                              onClick={() => setExpandedLogs(prev => ({ ...prev, [logKey]: !prev[logKey] }))}
                              className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-700"
                            >
                              <FileText className="w-3.5 h-3.5" />
                              {expandedLogs[logKey] ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Log drawer */}
                      {expandedLogs[logKey] && (
                        <div className="mt-2 ml-7">
                          {(source?.error_message || backup.error_message) && (
                            <div className="mb-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700 font-mono whitespace-pre-wrap">
                              {source?.error_message || backup.error_message}
                            </div>
                          )}
                          {source?.logs ? (
                            <pre className="text-xs text-gray-600 font-mono whitespace-pre-wrap max-h-48 overflow-y-auto bg-gray-50 p-2 rounded border">
                              {source.logs}
                            </pre>
                          ) : (
                            <p className="text-xs text-gray-400 italic">No logs</p>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {total > limit && (
        <div className="flex items-center justify-center gap-3">
          <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0} className="btn btn-secondary disabled:opacity-50">
            {t('common.previous')}
          </button>
          <span className="text-sm text-gray-600">{t('history.page', { current: page + 1, total: Math.ceil(total / limit) })}</span>
          <button onClick={() => setPage(p => p + 1)} disabled={(page + 1) * limit >= total} className="btn btn-secondary disabled:opacity-50">
            {t('common.next')}
          </button>
        </div>
      )}

      {/* ── Restore Modal ─────────────────────────────────────────────────── */}
      {restoreModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="fixed inset-0 bg-black/50" onClick={() => !restoreStatus && setRestoreModal(null)} />
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="relative bg-white rounded-xl shadow-xl w-full max-w-lg">
              <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between rounded-t-xl">
                <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  <RotateCcw className="w-5 h-5" /> Supabase Restore
                </h2>
                {!restoreStatus && (
                  <button onClick={() => setRestoreModal(null)} className="p-2 hover:bg-gray-100 rounded-lg">
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>

              <div className="p-6 space-y-4">
                {/* Status display */}
                {restoreStatus && (
                  <div className={clsx('p-4 rounded-lg border',
                    restoreStatus === 'running' || restoreStatus === 'starting' ? 'bg-blue-50 border-blue-200' :
                    restoreStatus === 'completed' ? 'bg-green-50 border-green-200' :
                    restoreStatus === 'partial' ? 'bg-yellow-50 border-yellow-200' :
                    'bg-red-50 border-red-200'
                  )}>
                    <div className="flex items-center gap-3">
                      {(restoreStatus === 'running' || restoreStatus === 'starting') && <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />}
                      {restoreStatus === 'completed' && <CheckCircle className="w-5 h-5 text-green-600" />}
                      {restoreStatus === 'partial' && <AlertCircle className="w-5 h-5 text-yellow-600" />}
                      {restoreStatus === 'failed' && <XCircle className="w-5 h-5 text-red-600" />}
                      <div>
                        <p className="font-semibold text-gray-900">
                          {restoreStatus === 'starting' && 'Restore wird gestartet...'}
                          {restoreStatus === 'running' && 'Restore läuft...'}
                          {restoreStatus === 'completed' && 'Restore erfolgreich!'}
                          {restoreStatus === 'partial' && 'Restore teilweise erfolgreich'}
                          {restoreStatus === 'failed' && 'Restore fehlgeschlagen'}
                        </p>
                        {restoreResult?.steps_total && (
                          <p className="text-sm text-gray-600">{restoreResult.steps_completed}/{restoreResult.steps_total} Schritte</p>
                        )}
                      </div>
                    </div>
                    {restoreResult?.errors?.length > 0 && (
                      <div className="mt-3 space-y-1">
                        {restoreResult.errors.map((err, i) => <p key={i} className="text-xs text-red-700">{err}</p>)}
                      </div>
                    )}
                    {restoreResult?.error && <p className="mt-2 text-sm text-red-700">{restoreResult.error}</p>}
                    {restoreResult?.logs && (
                      <pre className="mt-3 text-xs text-gray-600 font-mono whitespace-pre-wrap max-h-48 overflow-y-auto bg-white p-2 rounded border">
                        {restoreResult.logs}
                      </pre>
                    )}
                    {['completed', 'partial', 'failed'].includes(restoreStatus) && (
                      <button onClick={() => { setRestoreModal(null); setRestoreStatus(null); setRestoreResult(null) }} className="mt-3 btn btn-secondary text-sm">
                        Schließen
                      </button>
                    )}
                  </div>
                )}

                {/* Form */}
                {!restoreStatus && (
                  <>
                    <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                      <p className="text-sm text-amber-800">
                        <strong>⚠️ Achtung:</strong> Restore überschreibt Daten im Ziel-Projekt. Nur auf leere oder Test-Projekte anwenden!
                      </p>
                    </div>

                    {/* Backup selection */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Backup auswählen</label>
                      {restoreLoading ? (
                        <div className="flex items-center gap-2 text-gray-500"><Loader2 className="w-4 h-4 animate-spin" /> Lade Backups...</div>
                      ) : restoreBackups.length === 0 ? (
                        <p className="text-sm text-gray-500">Keine Backups gefunden</p>
                      ) : (
                        <select className="input" value={restoreForm.backup_path} onChange={e => setRestoreForm(p => ({ ...p, backup_path: e.target.value }))}>
                          {restoreBackups.map(b => (
                            <option key={b.path} value={b.path}>{b.filename} ({formatBytes(b.size)}) — {new Date(b.created).toLocaleString()}</option>
                          ))}
                        </select>
                      )}
                    </div>

                    {/* Profile / Manual */}
                    {!useManualConnection ? (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Ziel-Profil *</label>
                        {supabaseProfiles.length === 0 ? (
                          <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                            <p className="text-sm text-amber-800">Kein Supabase-Profil. Leg eins unter <strong>Settings → Credentials</strong> an.</p>
                          </div>
                        ) : (
                          <>
                            <select className="input" value={restoreForm.profile} onChange={e => setRestoreForm(p => ({ ...p, profile: e.target.value }))}>
                              {supabaseProfiles.map(p => <option key={p.profile} value={p.profile}>{p.profile}</option>)}
                            </select>
                            <p className="text-xs text-gray-500 mt-1">Connection String + DB-Passwort kommen aus dem Profil.</p>
                          </>
                        )}
                        <button type="button" onClick={() => setUseManualConnection(true)} className="mt-2 text-xs text-blue-600 hover:text-blue-800 underline">
                          Manuell Connection String eingeben
                        </button>
                      </div>
                    ) : (
                      <>
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <label className="block text-sm font-medium text-gray-700">Ziel Connection String *</label>
                            <button type="button" onClick={() => setUseManualConnection(false)} className="text-xs text-blue-600 hover:text-blue-800 underline">
                              Profil verwenden
                            </button>
                          </div>
                          <input type="text" className="input font-mono text-sm" value={restoreForm.target_connection_string}
                            onChange={e => setRestoreForm(p => ({ ...p, target_connection_string: e.target.value }))}
                            placeholder="postgresql://postgres.xxxxx:[YOUR-PASSWORD]@..." />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Ziel-DB Password</label>
                          <div className="relative">
                            <input type={showRestorePassword ? 'text' : 'password'} className="input pr-10"
                              value={restoreForm.target_db_password} onChange={e => setRestoreForm(p => ({ ...p, target_db_password: e.target.value }))}
                              placeholder="Wird in [YOUR-PASSWORD] eingesetzt" />
                            <button type="button" onClick={() => setShowRestorePassword(v => !v)} className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-500">
                              {showRestorePassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                            </button>
                          </div>
                        </div>
                      </>
                    )}

                    {/* Storage toggle */}
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input type="checkbox" className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        checked={restoreForm.restore_storage} onChange={e => setRestoreForm(p => ({ ...p, restore_storage: e.target.checked }))} />
                      <span className="text-sm text-gray-700">Storage-Objekte wiederherstellen</span>
                    </label>

                    {/* Service key — only manual mode */}
                    {restoreForm.restore_storage && useManualConnection && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Ziel-Service Role Key</label>
                        <div className="relative">
                          <input type={showServiceKey ? 'text' : 'password'} className="input pr-10"
                            value={restoreForm.target_service_role_key} onChange={e => setRestoreForm(p => ({ ...p, target_service_role_key: e.target.value }))}
                            placeholder="eyJ..." />
                          <button type="button" onClick={() => setShowServiceKey(v => !v)} className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-500">
                            {showServiceKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-3 pt-2">
                      <button onClick={() => setRestoreModal(null)} className="btn btn-secondary flex-1">Abbrechen</button>
                      <button
                        onClick={() => setConfirmRestore(true)}
                        disabled={!restoreForm.backup_path || (useManualConnection ? !restoreForm.target_connection_string : !restoreForm.profile)}
                        className="btn btn-primary flex-1 disabled:opacity-50"
                      >
                        <RotateCcw className="w-4 h-4 mr-2" /> Restore starten
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      <ConfirmDialog
        isOpen={confirmRestore}
        title="Restore bestätigen"
        message={`Daten werden auf das Ziel-Projekt wiederhergestellt. ${restoreForm.restore_storage ? 'Storage-Objekte werden ebenfalls überschrieben!' : ''} Fortfahren?`}
        confirmText="Ja, Restore starten"
        cancelText="Abbrechen"
        onConfirm={handleRestore}
        onClose={() => setConfirmRestore(false)}
        confirmVariant="danger"
      />
    </div>
  )
}
