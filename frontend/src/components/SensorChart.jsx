import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'

const SENSORS = [
  { key: 'temperature', label: 'Temperature', unit: '°C',   color: '#F59E0B', domain: [40, 100] },
  { key: 'vibration',   label: 'Vibration',   unit: 'mm/s', color: '#EF4444', domain: [0, 3]   },
  { key: 'pressure',    label: 'Pressure',    unit: 'bar',  color: '#00D4AA', domain: [8, 22]  },
  { key: 'rpm',         label: 'RPM',         unit: '',     color: '#66E6CC', domain: [2600, 3800] },
]

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface border border-border rounded-lg px-3 py-2 text-xs shadow-xl">
      <p className="text-subtext mb-1 font-mono">{label}</p>
      {payload.map(p => (
        <p key={p.dataKey} style={{ color: p.color }} className="font-medium">
          {p.name}: {p.value?.toFixed(2)}
        </p>
      ))}
    </div>
  )
}

export function SensorChart({ sensorKey, historyData, label, unit, color, domain }) {
  const chartData = historyData.map((r, i) => ({
    t:   i,
    val: r.sensors?.[sensorKey],
    ts:  r.timestamp ? new Date(r.timestamp).toLocaleTimeString() : '',
  }))

  return (
    <div className="bg-surface border border-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-medium text-subtext uppercase tracking-widest">{label}</p>
        <span className="font-mono text-xs px-2 py-0.5 rounded bg-surface2 text-subtext">
          {unit}
        </span>
      </div>
      <ResponsiveContainer width="100%" height={110}>
        <LineChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
          <XAxis dataKey="ts" tick={{ fontSize: 9, fill: '#9CA3AF' }} interval="preserveStartEnd" />
          <YAxis domain={domain} tick={{ fontSize: 9, fill: '#9CA3AF' }} />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="val"
            name={label}
            stroke={color}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function SensorChartsGrid({ historyData }) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {SENSORS.map(s => (
        <SensorChart key={s.key} sensorKey={s.key} historyData={historyData} {...s} />
      ))}
    </div>
  )
}
