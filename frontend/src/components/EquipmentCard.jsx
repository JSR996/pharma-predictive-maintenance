import { RULGauge } from './RULGauge'
import { Activity, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'
import clsx from 'clsx'

const STATUS_CONFIG = {
  normal:   { icon: CheckCircle,   color: 'text-teal',     border: 'border-teal/20',     bg: 'bg-teal/5'     },
  warning:  { icon: AlertTriangle, color: 'text-warning',  border: 'border-warning/30',  bg: 'bg-warning/5'  },
  critical: { icon: XCircle,       color: 'text-critical', border: 'border-critical/40', bg: 'bg-critical/5' },
}

export function EquipmentCard({ reading, isSelected, onClick }) {
  if (!reading) return null

  const status  = reading.status || 'normal'
  const cfg     = STATUS_CONFIG[status] || STATUS_CONFIG.normal
  const Icon    = cfg.icon
  const sensors = reading.sensors || {}

  return (
    <button
      onClick={onClick}
      className={clsx(
        'w-full text-left rounded-xl border p-4 transition-all duration-200',
        'hover:border-teal/40 focus:outline-none focus:ring-2 focus:ring-teal/40',
        cfg.border,
        cfg.bg,
        isSelected && 'ring-2 ring-teal/60 border-teal/50'
      )}
    >
      {/* Header row */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="font-mono text-[11px] text-muted tracking-widest uppercase">
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
            <p className="text-[9px] text-muted uppercase tracking-wider">{label}</p>
            <p className="font-mono text-xs text-text font-medium">
              {val != null ? val.toFixed(1) : '—'}
              <span className="text-muted text-[9px] ml-0.5">{unit}</span>
            </p>
          </div>
        ))}
      </div>

      {/* Anomaly badge */}
      {reading.is_anomaly && (
        <div className="mt-2 px-2 py-1 rounded-md bg-critical/10 border border-critical/30 text-critical text-[10px] font-medium text-center">
          ⚠ Anomaly detected
        </div>
      )}
    </button>
  )
}
