import { AlertTriangle, XCircle, Info, Bell } from 'lucide-react'
import clsx from 'clsx'

const SEVERITY_CONFIG = {
  critical: { icon: XCircle,       color: 'text-critical', bg: 'bg-critical/10', border: 'border-critical/30' },
  warning:  { icon: AlertTriangle, color: 'text-warning',  bg: 'bg-warning/10',  border: 'border-warning/30'  },
  info:     { icon: Info,          color: 'text-teal',     bg: 'bg-teal/10',     border: 'border-teal/20'     },
}

function timeAgo(iso) {
  if (!iso) return ''
  const diff = (Date.now() - new Date(iso).getTime()) / 1000
  if (diff < 60)  return `${Math.round(diff)}s ago`
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`
  return `${Math.round(diff / 3600)}h ago`
}

export function AlertFeed({ alerts }) {
  const cfg = (severity) => SEVERITY_CONFIG[severity] || SEVERITY_CONFIG.info

  return (
    <div className="bg-surface border border-border rounded-xl p-4 h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Bell className="w-4 h-4 text-subtext" />
          <h2 className="font-display font-semibold text-sm text-text">Alert Feed</h2>
        </div>
        <span className="text-[10px] font-mono text-muted px-2 py-0.5 rounded bg-surface2">
          {alerts.length} active
        </span>
      </div>

      {alerts.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-muted gap-2">
          <Info className="w-6 h-6 opacity-30" />
          <p className="text-xs">All systems normal</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-2 pr-1">
          {alerts.map((alert) => {
            const c = cfg(alert.severity)
            const Icon = c.icon
            return (
              <div
                key={alert.id}
                className={clsx(
                  'flex gap-2.5 p-2.5 rounded-lg border text-xs',
                  c.bg, c.border
                )}
              >
                <Icon className={clsx('w-3.5 h-3.5 mt-0.5 shrink-0', c.color)} />
                <div className="min-w-0">
                  <p className={clsx('font-medium leading-snug', c.color)}>
                    {alert.equipment_name || alert.equipment_id}
                  </p>
                  <p className="text-subtext text-[11px] mt-0.5 leading-snug">
                    {alert.message}
                  </p>
                  <p className="text-muted text-[10px] mt-1 font-mono">
                    {timeAgo(alert.timestamp)}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
