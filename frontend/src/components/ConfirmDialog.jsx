import { AlertTriangle, X } from 'lucide-react'
import clsx from 'clsx'

/**
 * Confirmation Dialog Component
 * Best Practice 11/2025: Always confirm destructive actions
 *
 * @param {boolean} isOpen - Whether dialog is visible
 * @param {function} onClose - Close callback
 * @param {function} onConfirm - Confirm callback
 * @param {string} title - Dialog title
 * @param {string} message - Dialog message
 * @param {string} confirmText - Confirm button text (default: "Confirm")
 * @param {string} confirmVariant - Confirm button variant: "danger" | "warning" | "primary"
 * @param {boolean} isLoading - Show loading state on confirm button
 */
export default function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title = "Are you sure?",
  message,
  confirmText = "Confirm",
  cancelText = "Cancel",
  confirmVariant = "danger",
  isLoading = false,
}) {
  if (!isOpen) return null

  const variantStyles = {
    danger: 'bg-red-600 hover:bg-red-700 focus:ring-red-500',
    warning: 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500',
    primary: 'bg-primary-600 hover:bg-primary-700 focus:ring-primary-500',
  }

  const iconColors = {
    danger: 'bg-red-100 text-red-600',
    warning: 'bg-yellow-100 text-yellow-600',
    primary: 'bg-primary-100 text-primary-600',
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6 transform transition-all"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1 text-gray-400 hover:text-gray-600 rounded-lg transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Icon */}
          <div className={clsx(
            'mx-auto flex items-center justify-center w-12 h-12 rounded-full mb-4',
            iconColors[confirmVariant]
          )}>
            <AlertTriangle className="w-6 h-6" />
          </div>

          {/* Title */}
          <h3 className="text-lg font-semibold text-gray-900 text-center mb-2">
            {title}
          </h3>

          {/* Message */}
          {message && (
            <p className="text-sm text-gray-600 text-center mb-6">
              {message}
            </p>
          )}

          {/* Actions */}
          <div className="flex flex-col-reverse sm:flex-row gap-3 sm:gap-3">
            <button
              onClick={onClose}
              disabled={isLoading}
              className="btn btn-secondary flex-1 justify-center"
            >
              {cancelText}
            </button>
            <button
              onClick={() => {
                onConfirm()
                // Don't auto-close - let the parent handle it
              }}
              disabled={isLoading}
              className={clsx(
                'btn flex-1 justify-center text-white focus:ring-2 focus:ring-offset-2',
                variantStyles[confirmVariant],
                isLoading && 'opacity-75 cursor-not-allowed'
              )}
            >
              {isLoading ? 'Processing...' : confirmText}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
