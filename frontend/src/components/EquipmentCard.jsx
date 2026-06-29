import { useState } from 'react'
import { RULGauge } from './RULGauge'
import { Activity, AlertTriangle, CheckCircle, XCircle, Wrench } from 'lucide-react'
import clsx from 'clsx'

const STATUS_CONFIG = {
  normal:   { icon: CheckCircle,   color: 'text-teal',     border: 'border-teal/20',     bg: 'bg-teal/5'     },
  warning:  { icon: AlertTriangle, color: 'text-warning',  border: 'border-warning/30',  bg: 'bg-warning/5'  },
  critical: { icon: XCircle,       color: 'text-critical', border: 'border-critical/40', bg: 'bg-critical/5' },
}

export function EquipmentCard({ reading, isSelected, onClick, onMaintenance }) {
  const [busy, setBusy] = useState(false)
  if (!reading) return null

  const status    = reading.status || 'normal'
  const cfg       = STATUS_CONFIG[status] || STATUS_CONFIG.normal
  const Icon      = cfg.icon
  const sensors   = reading.sensors || {}
  const failed    = reading.failed
  const isHealthy = status === 'normal'

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onClick?.()
    }
  }

  const handleMaintenance = async (e) => {
    e.stopPropagation()
    if (busy) return
    setBusy(true)
    try {
      await onMaintenance?.(reading.equipment_id)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      className={clsx(
        'group w-full text-left rounded-xl border p-4 transition-all duration-200 cursor-pointer',
        'hover:border-teal/40 focus:outline-none focus:ring-2 focus:ring-teal/40',
        cfg.border,
        cfg.bg,
        isSelected && 'ring-2 ring-teal/60 border-teal/50',
        failed && 'border-critical/60'
      )}
    >
      {/* Header row */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="font-mono text-[11px] text-subtext tracking-widest uppercase">
            {reading.equipment_id}
          </p>
          <p className="font-display font-semibold text-sm text-text mt-0.5 leading-tight">
            {reading.equipment_name}
          </p>
        </div>
        <Icon className={clsx('w-4 h-4 mt-0.5 shrink-0', cfg.color)} />
      </div>

      {/* RUL Gauge */}
      <div className="flex justify-center my-2">
        <RULGauge rul={reading.rul_predicted ?? 0} size={100} />
      </div>

      {/* Key sensor pills */}
      <div className="grid grid-cols-2 gap-1.5 mt-3">
        {[
          { label: 'Temp',  val: sensors.temperature, unit: '°C' },
          { label: 'Vib',   val: sensors.vibration,   unit: 'mm/s' },
          { label: 'Press', val: sensors.pressure,    unit: 'bar' },
          { label: 'RPM',   val: sensors.rpm,          unit: '' },
        ].map(({ label, val, unit }) => (
          <div key={label} className="bg-surface2 rounded-lg px-2 py-1.5">
            <p className="text-[9px] text-subtext uppercase tracking-wider">{label}</p>
            <p className="font-mono text-xs text-text font-medium">
              {val != null ? val.toFixed(1) : '—'}
              <span className="text-subtext text-[9px] ml-0.5">{unit}</span>
            </p>
          </div>
        ))}
      </div>

      {/* Failed / anomaly badge */}
      {failed ? (
        <div className="mt-2 px-2 py-1 rounded-md bg-critical/10 border border-critical/30 text-critical text-[10px] font-medium flex items-center justify-center gap-1">
          <XCircle className="w-3 h-3 shrink-0" />
          Failed — needs maintenance
        </div>
      ) : reading.is_anomaly && (
        <div className="mt-2 px-2 py-1 rounded-md bg-critical/10 border border-critical/30 text-critical text-[10px] font-medium flex items-center justify-center gap-1">
          <AlertTriangle className="w-3 h-3 shrink-0" />
          Anomaly detected
        </div>
      )}

      {/* Maintenance action — solid + always shown once degraded; on a healthy unit
          it stays quiet (calm by default) and reveals on card hover or keyboard focus. */}
      <button
        onClick={handleMaintenance}
        disabled={busy}
        className={clsx(
          'mt-2 w-full rounded-lg px-2 py-1.5 text-[11px] font-medium tracking-wide',
          'flex items-center justify-center gap-1.5 transition-colors duration-150',
          'focus:outline-none focus:ring-2 focus:ring-teal/50 disabled:opacity-50',
          failed
            ? 'bg-teal text-bg hover:bg-teal/90'
            : 'border border-teal/30 text-teal hover:bg-teal/10',
          // Healthy: hidden until the card is hovered or anything inside it is focused.
          isHealthy &&
            'opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto ' +
            'group-focus-within:opacity-100 group-focus-within:pointer-events-auto ' +
            'focus-visible:opacity-100 focus-visible:pointer-events-auto'
        )}
      >
        <Wrench className={clsx('w-3 h-3 shrink-0', busy && 'animate-spin')} />
        {busy ? 'Servicing…' : 'Perform Maintenance'}
      </button>
    </div>
  )
}
