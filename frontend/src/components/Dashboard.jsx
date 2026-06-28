import { useState } from 'react'
import { EquipmentCard } from './EquipmentCard'
import { SensorChartsGrid } from './SensorChart'
import { AlertFeed } from './AlertFeed'
import { RULGauge } from './RULGauge'
import { Activity, Cpu, Zap } from 'lucide-react'
import clsx from 'clsx'

export function Dashboard({ readings, history, alerts, connected }) {
  const [selectedId, setSelectedId] = useState(null)

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
      {/* KPI Strip */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {[
          { label: 'Critical',  count: criticalCount, color: 'text-critical', bg: 'bg-critical/10', icon: Zap      },
          { label: 'Warning',   count: warningCount,  color: 'text-warning',  bg: 'bg-warning/10',  icon: Activity },
          { label: 'Normal',    count: normalCount,   color: 'text-teal',     bg: 'bg-teal/10',     icon: Cpu      },
        ].map(({ label, count, color, bg, icon: Icon }) => (
          <div key={label} className={clsx('rounded-xl border border-border p-4 flex items-center gap-4', bg)}>
            <Icon className={clsx('w-6 h-6', color)} />
            <div>
              <p className={clsx('font-display font-bold text-2xl leading-none', color)}>{count}</p>
              <p className="text-xs text-muted mt-1">{label} equipment</p>
            </div>
          </div>
        ))}
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-12 gap-4">

        {/* Equipment cards — left column */}
        <div className="col-span-3 space-y-3">
          <h2 className="font-display font-semibold text-xs text-muted uppercase tracking-widest mb-2">
            Equipment ({readings.length})
          </h2>
          {readings.map(r => (
            <EquipmentCard
              key={r.equipment_id}
              reading={r}
              isSelected={r.equipment_id === activeId}
              onClick={() => setSelectedId(r.equipment_id)}
            />
          ))}
        </div>

        {/* Sensor charts — middle */}
        <div className="col-span-6 space-y-4">
          {selectedReading ? (
            <>
              {/* Selected equipment header */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-mono text-[10px] text-muted tracking-widest uppercase">
                    {selectedReading.equipment_id}
                  </p>
                  <h2 className="font-display font-bold text-lg text-text">
                    {selectedReading.equipment_name}
                  </h2>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <p className="text-[10px] text-muted uppercase tracking-wider">Anomaly Score</p>
                    <p className={clsx(
                      'font-mono font-bold text-lg',
                      selectedReading.anomaly_score > 0.6 ? 'text-critical' :
                      selectedReading.anomaly_score > 0.3 ? 'text-warning' : 'text-teal'
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
              <div className="bg-surface border border-border rounded-xl p-4">
                <div className="flex justify-between text-xs text-muted mb-2">
                  <span>Equipment Health</span>
                  <span>{(100 - (selectedReading.degradation_pct ?? 0)).toFixed(1)}% remaining</span>
                </div>
                <div className="w-full h-2 bg-surface2 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${100 - (selectedReading.degradation_pct ?? 0)}%`,
                      background: selectedReading.status === 'critical' ? '#EF4444'
                                : selectedReading.status === 'warning'  ? '#F59E0B'
                                : '#00D4AA',
                      boxShadow: `0 0 8px ${
                        selectedReading.status === 'critical' ? '#EF444488'
                        : selectedReading.status === 'warning' ? '#F59E0B88'
                        : '#00D4AA44'
                      }`,
                    }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-muted mt-1">
                  <span>Cycle {selectedReading.cycle}</span>
                  <span>{selectedReading.rul_predicted} cycles to maintenance</span>
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-64 text-muted text-sm">
              {connected ? 'Select an equipment unit' : 'Connecting to sensor stream…'}
            </div>
          )}
        </div>

        {/* Alert feed — right column */}
        <div className="col-span-3 h-full" style={{ minHeight: '600px' }}>
          <AlertFeed alerts={alerts} />
        </div>
      </div>
    </main>
  )
}
