import { useEffect, useRef, useState } from 'react'
import { RULGauge } from './RULGauge'
import { AlertTriangle, CheckCircle, XCircle, Wrench, Check, X } from 'lucide-react'
import clsx from 'clsx'

const STATUS_CONFIG = {
  normal:   { icon: CheckCircle,   color: 'text-normal',   border: 'border-normal/25',   bg: 'bg-normal/5'   },
  warning:  { icon: AlertTriangle, color: 'text-warning',  border: 'border-warning/30',  bg: 'bg-warning/5'  },
  critical: { icon: XCircle,       color: 'text-critical', border: 'border-critical/40', bg: 'bg-critical/5' },
}

export function EquipmentCard({ reading, isSelected, onClick, onMaintenance }) {
  const [busy, setBusy] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const cancelTimer = useRef(null)

  // Clear the auto-cancel timer on unmount so a serviced/removed card doesn't
  // fire setState after teardown.
  useEffect(() => () => clearTimeout(cancelTimer.current), [])

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

  // First click arms an inline confirm (no modal); it auto-disarms after 4s so a
  // stray click never leaves the card in a primed state.
  const arm = (e) => {
    e.stopPropagation()
    if (busy) return
    setConfirming(true)
    clearTimeout(cancelTimer.current)
    cancelTimer.current = setTimeout(() => setConfirming(false), 4000)
  }

  const cancel = (e) => {
    e.stopPropagation()
    clearTimeout(cancelTimer.current)
    setConfirming(false)
  }

  const confirm = async (e) => {
    e.stopPropagation()
    if (busy) return
    clearTimeout(cancelTimer.current)
    setConfirming(false)
    setBusy(true)
    try {
      await onMaintenance?.(reading.equipment_id)
    } catch {
      // Error is surfaced as a toast by the parent; just release the busy state.
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
        'hover:border-brand/40 focus:outline-none focus:ring-2 focus:ring-brand/40',
        cfg.border,
        cfg.bg,
        isSelected && 'ring-2 ring-brand/60 border-brand/50',
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
          it stays quiet (calm by default) and reveals on card hover or keyboard focus.
          First click arms an inline confirm; there is no modal. */}
      <div
        className={clsx(
          'mt-2',
          // Healthy: hidden until the card is hovered/focused — but once armed or
          // servicing, force it visible so the confirm can't vanish on mouse-out.
          isHealthy && !confirming && !busy &&
            'opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto ' +
            'group-focus-within:opacity-100 group-focus-within:pointer-events-auto ' +
            'focus-visible:opacity-100 focus-visible:pointer-events-auto'
        )}
      >
        {confirming ? (
          <div className="flex gap-1.5">
            <button
              onClick={confirm}
              className={clsx(
                'flex-1 rounded-lg px-2 py-1.5 text-[11px] font-semibold tracking-wide',
                'flex items-center justify-center gap-1.5 transition-colors duration-150',
                'bg-brand text-white hover:bg-brand/90',
                'focus:outline-none focus:ring-2 focus:ring-brand/50'
              )}
            >
              <Check className="w-3 h-3 shrink-0" />
              Confirm reset
            </button>
            <button
              onClick={cancel}
              aria-label="Cancel maintenance"
              className={clsx(
                'rounded-lg px-2 py-1.5 border border-border text-subtext',
                'flex items-center justify-center transition-colors duration-150',
                'hover:bg-surface2 hover:text-text',
                'focus:outline-none focus:ring-2 focus:ring-brand/40'
              )}
            >
              <X className="w-3.5 h-3.5 shrink-0" />
            </button>
          </div>
        ) : (
          <button
            onClick={arm}
            disabled={busy}
            className={clsx(
              'w-full rounded-lg px-2 py-1.5 text-[11px] font-medium tracking-wide',
              'flex items-center justify-center gap-1.5 transition-colors duration-150',
              'focus:outline-none focus:ring-2 focus:ring-brand/50 disabled:opacity-60',
              failed
                ? 'bg-brand text-white hover:bg-brand/90'
                : 'border border-brand/30 text-brand hover:bg-brand/10'
            )}
          >
            <Wrench className={clsx('w-3 h-3 shrink-0', busy && 'animate-spin')} />
            {busy ? 'Servicing…' : 'Perform Maintenance'}
          </button>
        )}
      </div>
    </div>
  )
}
