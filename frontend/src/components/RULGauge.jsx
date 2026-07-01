/**
 * RUL Gauge — the signature visual element of PharmaGuard.
 * Renders a degradation arc: full green = healthy, sweeps to critical red.
 */
export function RULGauge({ rul, cap = 125, size = 120 }) {
  const pct = Math.max(0, Math.min(1, rul / cap))

  const cx = size / 2
  const cy = size / 2
  const r  = size * 0.38
  const strokeW = size * 0.07

  // Arc spans 220° (from 160° to 20°, going clockwise)
  const START_DEG = 160
  const TOTAL_DEG = 220

  function polarToXY(angleDeg, radius) {
    const rad = (angleDeg * Math.PI) / 180
    return {
      x: cx + radius * Math.cos(rad),
      y: cy + radius * Math.sin(rad),
    }
  }

  function describeArc(startDeg, endDeg, radius) {
    const s = polarToXY(startDeg, radius)
    const e = polarToXY(endDeg, radius)
    const large = endDeg - startDeg > 180 ? 1 : 0
    return `M ${s.x} ${s.y} A ${radius} ${radius} 0 ${large} 1 ${e.x} ${e.y}`
  }

  // Status step: critical red → warning amber → healthy green (thresholds mirror predict_rul)
  const color = pct < 0.12 ? '#DC2626' : pct < 0.32 ? '#D97706' : '#16A34A'
  const trackPath  = describeArc(START_DEG, START_DEG + TOTAL_DEG, r)
  const activePath = pct > 0.005 ? describeArc(START_DEG, START_DEG + TOTAL_DEG * pct, r) : null

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Track */}
        <path
          d={trackPath}
          fill="none"
          stroke="#E2E8F0"
          strokeWidth={strokeW}
          strokeLinecap="round"
        />
        {/* Active arc */}
        {activePath && (
          <path
            d={activePath}
            fill="none"
            stroke={color}
            strokeWidth={strokeW}
            strokeLinecap="round"
          />
        )}
        {/* RUL number */}
        <text
          x={cx}
          y={cy - 4}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={color}
          fontSize={size * 0.18}
          fontFamily="'Space Grotesk', sans-serif"
          fontWeight="700"
        >
          {Math.round(rul)}
        </text>
        {/* Label */}
        <text
          x={cx}
          y={cy + size * 0.14}
          textAnchor="middle"
          fill="#5B7089"
          fontSize={size * 0.09}
          fontFamily="Inter, sans-serif"
          letterSpacing="0.08em"
        >
          CYCLES
        </text>
      </svg>
    </div>
  )
}
