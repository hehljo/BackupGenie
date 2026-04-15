import { Link, useLocation } from 'react-router-dom'
import { Home, Database, History, Settings, LogOut, HardDrive, Menu, X, Bell, FileText } from 'lucide-react'
import clsx from 'clsx'
import { useTranslation } from 'react-i18next'
import { useState, useEffect } from 'react'
import LanguageSwitcher from './LanguageSwitcher'

const navigation = [
  { name: 'dashboard', href: '/', icon: Home },
  { name: 'sources', href: '/sources', icon: Database },
  { name: 'history', href: '/history', icon: History },
  { name: 'notifications', href: '/notifications', icon: Bell },
  { name: 'logs', href: '/logs', icon: FileText },
  { name: 'settings', href: '/settings', icon: Settings },
]

export default function Layout({ children, onLogout }) {
  const location = useLocation()
  const { t } = useTranslation()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  // Close mobile menu when route changes
  useEffect(() => {
    setIsMobileMenuOpen(false)
  }, [location.pathname])

  // Prevent scroll when mobile menu is open
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isMobileMenuOpen])

  const SidebarContent = () => (
    <>
      {/* Logo */}
      <div className="px-6 py-5 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary-100 rounded-lg">
            <HardDrive className="w-6 h-6 text-primary-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">{t('app.name')}</h1>
            <p className="text-xs text-gray-500">Backup Manager</p>
          </div>
        </div>
        <div className="mt-3">
          <LanguageSwitcher />
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href
          const Icon = item.icon

          return (
            <Link
              key={item.name}
              to={item.href}
              className={clsx(
                'flex items-center gap-3 px-4 py-3 rounded-lg transition-all',
                isActive
                  ? 'bg-primary-50 text-primary-700 font-medium'
                  : 'text-gray-700 hover:bg-gray-100'
              )}
            >
              <Icon className="w-5 h-5" />
              {t(`nav.${item.name}`)}
            </Link>
          )
        })}
      </nav>

      {/* Logout + Version */}
      <div className="p-4 border-t border-gray-200">
        <button
          onClick={onLogout}
          className="flex items-center gap-3 w-full px-4 py-3 text-red-600 hover:bg-red-50 rounded-lg transition-all"
        >
          <LogOut className="w-5 h-5" />
          {t('nav.logout')}
        </button>
        <p className="text-xs text-gray-400 text-center mt-2">v1.4.0</p>
      </div>
    </>
  )

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-40 bg-white border-b border-gray-200">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-primary-100 rounded-lg">
              <HardDrive className="w-5 h-5 text-primary-600" />
            </div>
            <h1 className="text-lg font-bold text-gray-900">{t('app.name')}</h1>
          </div>
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Toggle menu"
          >
            {isMobileMenuOpen ? (
              <X className="w-6 h-6 text-gray-700" />
            ) : (
              <Menu className="w-6 h-6 text-gray-700" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Menu Backdrop */}
      {isMobileMenuOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-40 transition-opacity"
          onClick={() => setIsMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile Sidebar Drawer */}
      <div
        className={clsx(
          'md:hidden fixed inset-y-0 left-0 z-50 w-72 bg-white transform transition-transform duration-300 ease-in-out flex flex-col',
          isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <SidebarContent />
      </div>

      {/* Desktop Sidebar */}
      <div className="hidden md:flex md:fixed md:inset-y-0 md:left-0 md:w-64 md:flex-col bg-white border-r border-gray-200">
        <SidebarContent />
      </div>

      {/* Main content */}
      <div className="md:pl-64 pt-16 md:pt-0">
        <main className="p-4 md:p-8">
          {children}
        </main>
      </div>
    </div>
  )
}
