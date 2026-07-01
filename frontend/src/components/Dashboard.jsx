import { useState } from 'react'
import { EquipmentCard } from './EquipmentCard'
import { SensorChartsGrid } from './SensorChart'
import { AlertFeed } from './AlertFeed'
import { RULGauge } from './RULGauge'
import { InfoHint } from './InfoHint'
import { api } from '../utils/api'
import { useToast } from '../hooks/useToast'
import clsx from 'clsx'

export function Dashboard({ readings, history, alerts, connected }) {
  const [selectedId, setSelectedId] = useState(null)
  const toast = useToast()

  // Operator maintenance action — resets a unit to a fresh, healthy engine. The
  // WebSocket broadcast refreshes the card on the next tick, so no local state.
  // Result is surfaced as a toast (never silent); the error is re-thrown so the
  // card can clear its own busy state.
  const handleMaintenance = async (id) => {
    const name = readings.find(r => r.equipment_id === id)?.equipment_name || id
    try {
      await api.replaceEquipment(id)
      toast(`${name} serviced — fresh unit online`, 'success')
    } catch (e) {
      console.error('maintenance failed:', e)
      toast(`Couldn't service ${name} — ${e?.message || 'request failed'}`, 'error')
      throw e
    }
  }

  // Auto-select first critical equipment if nothing selected
  const activeId = selectedId ||
    readings.find(r => r.status === 'critical')?.equipment_id ||
    readings[0]?.equipment_id

  const selectedReading = readings.find(r => r.equipment_id === activeId)
  const selectedHistory = history[activeId] || []

  const criticalCount = readings.filter(r => r.status === 'critical').length
  const warningCount  = readings.filter(r => r.status === 'warning').length
  const normalCount   = readings.filter(r => r.status === 'normal').length

  return (
    <main className="mx-auto max-w-screen-2xl px-6 py-6">
      {/* Fleet status — one instrument readout, not three stat tiles */}
      <div className="mb-6 rounded-xl border border-border bg-surface px-5 py-4 shadow-sm">
        <div className="flex items-center justify-between gap-6 flex-wrap">
          {/* Headline: total + worst-case state */}
          <div className="flex items-baseline gap-3">
            <span className="font-display font-bold text-3xl text-text leading-none tabular-nums">
              {readings.length}
            </span>
            <div>
              <p className="font-display font-semibold text-xs text-subtext uppercase tracking-widest">
                Fleet Status
              </p>
              <p className="text-xs text-subtext mt-0.5">
                {criticalCount > 0
                  ? `${criticalCount} unit${criticalCount > 1 ? 's' : ''} need attention`
                  : warningCount > 0
                  ? `${warningCount} unit${warningCount > 1 ? 's' : ''} degrading`
                  : 'All units nominal'}
              </p>
            </div>
          </div>

          {/* Legend: count per state, dimmed when zero */}
          <div className="flex items-center gap-4">
            {[
              { label: 'Normal',   count: normalCount,   dot: 'bg-normal',   text: 'text-normal'   },
              { label: 'Warning',  count: warningCount,  dot: 'bg-warning',  text: 'text-warning'  },
              { label: 'Critical', count: criticalCount, dot: 'bg-critical', text: 'text-critical' },
            ].map(({ label, count, dot, text }) => (
              <div key={label} className={clsx('flex items-center gap-1.5', count === 0 && 'opacity-40')}>
                <span className={clsx('w-1.5 h-1.5 rounded-full', dot)} />
                <span className={clsx('font-mono text-sm font-semibold tabular-nums', text)}>{count}</span>
                <span className="text-[10px] text-subtext uppercase tracking-wider">{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Segmented health meter — a healthy fleet reads as a full green bar */}
        <div className="mt-3 h-1.5 rounded-full overflow-hidden bg-surface2 flex gap-px">
          {[
            { count: normalCount,   color: '#16A34A' },
            { count: warningCount,  color: '#D97706' },
            { count: criticalCount, color: '#DC2626' },
          ]
            .filter((s) => s.count > 0)
            .map((s, i) => (
              <div
                key={i}
                style={{
                  width: `${(s.count / readings.length) * 100}%`,
                  background: s.color,
                }}
              />
            ))}
        </div>
      </div>

      {/* Main grid — single column on mobile, 3-pane on large screens */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">

        {/* Equipment cards — left column. Responsive card grid on small screens,
            single-column rail on desktop. */}
        <div className="lg:col-span-3">
          <h2 className="font-display font-semibold text-xs text-subtext uppercase tracking-widest mb-2">
            Equipment ({readings.length})
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-1 gap-3">
            {readings.map(r => (
              <EquipmentCard
                key={r.equipment_id}
                reading={r}
                isSelected={r.equipment_id === activeId}
                onClick={() => setSelectedId(r.equipment_id)}
                onMaintenance={handleMaintenance}
              />
            ))}
          </div>
        </div>

        {/* Sensor charts — middle */}
        <div className="lg:col-span-6 space-y-4">
          {selectedReading ? (
            <>
              {/* Selected equipment header — stacks on mobile so the name and the
                  anomaly/gauge readout never collide. */}
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <p className="font-mono text-[10px] text-subtext tracking-widest uppercase">
                    {selectedReading.equipment_id}
                  </p>
                  <h2 className="font-display font-bold text-lg text-text truncate">
                    {selectedReading.equipment_name}
                  </h2>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <div className="text-right">
                    <p className="text-[10px] text-subtext uppercase tracking-wider">
                      Anomaly Score
                      <InfoHint
                        align="right"
                        className="ml-1"
                        text="How far current sensor readings sit from this unit's healthy baseline. 0% is normal; higher means increasingly abnormal."
                      />
                    </p>
                    <p className={clsx(
                      'font-mono font-bold text-lg',
                      selectedReading.anomaly_score > 0.6 ? 'text-critical' :
                      selectedReading.anomaly_score > 0.3 ? 'text-warning' : 'text-normal'
                    )}>
                      {(selectedReading.anomaly_score * 100).toFixed(1)}%
                    </p>
                  </div>
                  <RULGauge rul={selectedReading.rul_predicted ?? 0} size={90} />
                </div>
              </div>

              {/* Charts */}
              <SensorChartsGrid historyData={selectedHistory} />

              {/* Degradation bar */}
              <div className="bg-surface border border-border rounded-xl p-4 shadow-sm">
                <div className="flex justify-between text-xs text-subtext mb-2">
                  <span className="flex items-center">
                    Equipment Health
                    <InfoHint
                      className="ml-1"
                      text="Based on RUL — Remaining Useful Life, the model's estimate of how many operating cycles this unit has left before it needs maintenance."
                    />
                  </span>
                  <span>{(100 - (selectedReading.degradation_pct ?? 0)).toFixed(1)}% remaining</span>
                </div>
                <div className="w-full h-2 bg-surface2 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${100 - (selectedReading.degradation_pct ?? 0)}%`,
                      background: selectedReading.status === 'critical' ? '#DC2626'
                                : selectedReading.status === 'warning'  ? '#D97706'
                                : '#16A34A',
                    }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-subtext mt-1">
                  <span>Cycle {selectedReading.cycle}</span>
                  <span>{selectedReading.rul_predicted} cycles to maintenance</span>
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-64 text-subtext text-sm">
              {connected ? 'Select an equipment unit' : 'Connecting to sensor stream…'}
            </div>
          )}
        </div>

        {/* Alert feed — right column */}
        <div className="lg:col-span-3 lg:min-h-[600px]">
          <AlertFeed alerts={alerts} />
        </div>
      </div>
    </main>
  )
}
