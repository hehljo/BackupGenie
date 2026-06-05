import { useState, useEffect } from 'react'
import { Bell, Mail, MessageSquare, Send, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { useTranslation } from 'react-i18next'
import { CardGridSkeleton } from '../components/Skeleton'
import { notificationsAPI } from '../services/api'

export default function Notifications() {
  const { t } = useTranslation()
  const [channels, setChannels] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [isTesting, setIsTesting] = useState({})

  useEffect(() => {
    loadChannels()
  }, [])

  const loadChannels = async () => {
    try {
      const res = await notificationsAPI.getChannels()
      setChannels((res.data.channels || []).map((name) => ({
        id: name,
        name,
        type: name.split('-')[0],
        enabled: true,
        config: {}
      })))
      setIsLoading(false)
    } catch (error) {
      console.error('Error loading channels:', error)
      toast.error('Failed to load notification channels')
      setIsLoading(false)
    }
  }

  const handleTest = async (channelId) => {
    setIsTesting({ ...isTesting, [channelId]: true })
    const loadingToast = toast.loading(`Testing ${channelId}...`)

    try {
      const res = await notificationsAPI.test(channelId)
      toast.success(res.data.message || `Test notification sent via ${channelId}!`, { id: loadingToast })
    } catch (error) {
      console.error('Error testing channel:', error)
      toast.error(`Failed to send test notification`, { id: loadingToast })
    } finally {
      setIsTesting({ ...isTesting, [channelId]: false })
    }
  }

  const getChannelIcon = (type) => {
    const icons = {
      email: Mail,
      telegram: Send,
      discord: MessageSquare,
      ntfy: Bell,
    }
    const Icon = icons[type] || Bell
    return <Icon className="w-5 h-5" />
  }

  const getStatusBadge = (enabled) => {
    if (enabled) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
          <CheckCircle className="w-3.5 h-3.5" />
          Enabled
        </span>
      )
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded-full">
        <XCircle className="w-3.5 h-3.5" />
        Disabled
        </span>
    )
  }

  if (isLoading) {
    return (
      <div className="page-shell">
        {/* Header Skeleton */}
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="space-y-2">
            <div className="h-8 w-56 bg-gray-200 rounded animate-pulse"></div>
            <div className="h-4 w-80 bg-gray-200 rounded animate-pulse"></div>
          </div>
        </div>

        {/* Channels Grid Skeleton */}
        <CardGridSkeleton count={4} />
      </div>
    )
  }

  return (
    <div className="page-shell">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Notifications</h1>
          <p className="text-sm md:text-base text-gray-600 mt-1">
            Manage notification channels for backup events
          </p>
        </div>
      </div>

      {/* Info Banner */}
      <div className="card bg-blue-50 border border-blue-200">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
          <div className="text-sm text-blue-800">
            <p className="font-semibold mb-1">Notification Configuration</p>
            <p>
              Notification channels are configured via environment variables or config files.
              Use this page to test your configured channels.
            </p>
          </div>
        </div>
      </div>

      {/* Channels Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        {channels.map((channel) => (
          <div key={channel.id} className="card">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-primary-100 rounded-lg">
                  {getChannelIcon(channel.type)}
                </div>
                <div>
                  <h3 className="font-bold text-gray-900">{channel.name}</h3>
                  <p className="text-sm text-gray-600">{channel.type.toUpperCase()}</p>
                </div>
              </div>
              {getStatusBadge(channel.enabled)}
            </div>

            {channel.enabled && channel.config && Object.keys(channel.config).length > 0 && (
              <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                <p className="text-xs font-semibold text-gray-700 mb-2">Configuration</p>
                <div className="space-y-1">
                  {Object.entries(channel.config).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-xs">
                      <span className="text-gray-600">{key.replace(/_/g, ' ')}</span>
                      <span className="text-gray-900 font-mono truncate ml-2 max-w-[60%]">
                        {key.toLowerCase().includes('password') || key.toLowerCase().includes('token')
                          ? '••••••••'
                          : value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {channel.enabled && (
              <button
                onClick={() => handleTest(channel.id)}
                disabled={isTesting[channel.id]}
                className="btn btn-secondary w-full flex items-center justify-center gap-2"
              >
                <Send className="w-4 h-4" />
                {isTesting[channel.id] ? 'Sending...' : 'Send Test Notification'}
              </button>
            )}

            {!channel.enabled && (
              <div className="text-center py-4 text-sm text-gray-500">
                Configure this channel in your environment variables or config file to enable
              </div>
            )}
          </div>
        ))}
      </div>

      {channels.length === 0 && (
        <div className="card text-center py-12">
          <Bell className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No Notification Channels</h3>
          <p className="text-gray-600 mb-6">
            Configure notification channels to receive backup alerts
          </p>
        </div>
      )}

      {/* Keyboard Shortcuts Modal */}
    </div>
  )
}
