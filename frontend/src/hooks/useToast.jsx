import { createContext, useCallback, useContext, useRef, useState } from 'react'
import { CheckCircle, XCircle, Info, X } from 'lucide-react'

/**
 * Minimal toast system — a few lines of native React, no dependency.
 * Surfaces the result of operator actions (e.g. maintenance) so success and,
 * critically, failure are never silent. The viewport is an aria-live region so
 * screen readers announce each toast; entrance motion is gated by the global
 * prefers-reduced-motion block in index.css.
 */
const ToastContext = createContext(null)

const ICON = {
  success: { Icon: CheckCircle, color: 'text-normal' },
  error:   { Icon: XCircle,     color: 'text-critical' },
  info:    { Icon: Info,        color: 'text-brand' },
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const idRef = useRef(0)

  const dismiss = useCallback((id) => {
    setToasts((t) => t.filter((x) => x.id !== id))
  }, [])

  const toast = useCallback((message, kind = 'info', ttl = 3500) => {
    const id = ++idRef.current
    setToasts((t) => [...t, { id, message, kind }])
    if (ttl > 0) setTimeout(() => dismiss(id), ttl)
    return id
  }, [dismiss])

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div
        className="fixed bottom-4 right-4 z-toast flex flex-col gap-2 w-[min(20rem,calc(100vw-2rem))]"
        role="status"
        aria-live="polite"
      >
        {toasts.map(({ id, message, kind }) => {
          const { Icon, color } = ICON[kind] || ICON.info
          return (
            <div
              key={id}
              className="toast-in flex items-start gap-2.5 rounded-lg border border-border bg-surface shadow-md px-3 py-2.5"
            >
              <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${color}`} />
              <p className="flex-1 min-w-0 text-xs text-text leading-snug">{message}</p>
              <button
                onClick={() => dismiss(id)}
                aria-label="Dismiss"
                className="shrink-0 text-subtext hover:text-text focus:outline-none focus:ring-2 focus:ring-brand/40 rounded"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within a ToastProvider')
  return ctx
}
