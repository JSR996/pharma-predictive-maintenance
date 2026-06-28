/**
 * RUL Gauge — the signature visual element of PharmaGuard.
 * Renders a degradation arc: full teal = healthy, sweeps to critical red.
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

  const endDeg = START_DEG + TOTAL_DEG * (1 - pct)

  // Color interpolation: teal (#00D4AA) → warning (#F59E0B) → critical (#EF4444)
  function getColor(pct) {
    if (pct > 0.5) {
      // teal → warning
      const t = (pct - 0.5) / 0.5
      const r = Math.round(0 + t * 0)
      const g = Math.round(212 + t * (158 - 212))
      const b = Math.round(170 + t * (11 - 170))
      return `rgb(${239 - Math.round((1-t)*239)},${Math.round(158 + t*(212-158))},${Math.round(11 + t*(170-11))})`
    }
    // warning → critical
    const t = pct / 0.5
    return pct < 0.2 ? '#EF4444' : pct < 0.4 ? '#F59E0B' : '#00D4AA'
  }

  const color = pct < 0.12 ? '#EF4444' : pct < 0.32 ? '#F59E0B' : '#00D4AA'
  const trackPath  = describeArc(START_DEG, START_DEG + TOTAL_DEG, r)
  const activePath = pct > 0.005 ? describeArc(START_DEG, START_DEG + TOTAL_DEG * pct, r) : null

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Track */}
        <path
          d={trackPath}
          fill="none"
          stroke="#1F2937"
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
            style={{ filter: `drop-shadow(0 0 4px ${color}88)` }}
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
          fill="#6B7280"
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
