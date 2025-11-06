import { useState, useEffect } from 'react'
import { Plus, Edit2, Trash2, TestTube, Database } from 'lucide-react'
import { sourcesAPI } from '../services/api'
import clsx from 'clsx'
import { useTranslation } from 'react-i18next'

export default function Sources() {
  const { t } = useTranslation()
  const [sources, setSources] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingSource, setEditingSource] = useState(null)

  useEffect(() => {
    loadSources()
  }, [])

  const loadSources = async () => {
    try {
      const response = await sourcesAPI.getAll()
      setSources(response.data.sources)
      setIsLoading(false)
    } catch (error) {
      console.error('Error loading sources:', error)
      setIsLoading(false)
    }
  }

  const handleDelete = async (sourceId) => {
    if (!confirm(t('common.confirm') + '?')) return

    try {
      await sourcesAPI.delete(sourceId)
      loadSources()
    } catch (error) {
      console.error('Error deleting source:', error)
      alert(t('common.error'))
    }
  }

  const handleTest = async (sourceId) => {
    try {
      await sourcesAPI.test(sourceId)
      alert(t('common.success') + '!')
    } catch (error) {
      console.error('Error testing source:', error)
      alert(t('common.error'))
    }
  }

  const getTypeIcon = (type) => {
    return <Database className="w-5 h-5" />
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
          <h1 className="text-3xl font-bold text-gray-900">{t('sources.title')}</h1>
          <p className="text-gray-600 mt-1">{t('sources.subtitle')}</p>
        </div>
        <button
          onClick={() => {
            setEditingSource(null)
            setShowModal(true)
          }}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          {t('sources.addSource')}
        </button>
      </div>

      {/* Sources Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {sources.map((source) => (
          <div key={source.id} className="card">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-primary-100 rounded-lg">
                  {getTypeIcon(source.type)}
                </div>
                <div>
                  <h3 className="font-bold text-gray-900">{source.name}</h3>
                  <p className="text-sm text-gray-600">{source.type.toUpperCase()}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleTest(source.id)}
                  className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-all"
                  title={t('sources.testConnection')}
                >
                  <TestTube className="w-5 h-5" />
                </button>
                <button
                  onClick={() => {
                    setEditingSource(source)
                    setShowModal(true)
                  }}
                  className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-all"
                  title={t('sources.edit')}
                >
                  <Edit2 className="w-5 h-5" />
                </button>
                <button
                  onClick={() => handleDelete(source.id)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-all"
                  title={t('sources.delete')}
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">{t('sources.status')}</span>
                <span className={clsx(
                  'badge',
                  source.enabled ? 'badge-success' : 'badge-warning'
                )}>
                  {source.enabled ? t('sources.enabled') : t('sources.disabled')}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">{t('sources.priority')}</span>
                <span className="font-medium">{source.priority}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {sources.length === 0 && (
        <div className="card text-center py-12">
          <Database className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">{t('sources.noSources')}</h3>
          <p className="text-gray-600 mb-6">{t('sources.noSourcesHint')}</p>
          <button
            onClick={() => setShowModal(true)}
            className="btn btn-primary inline-flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            {t('sources.addSource')}
          </button>
        </div>
      )}
    </div>
  )
}
