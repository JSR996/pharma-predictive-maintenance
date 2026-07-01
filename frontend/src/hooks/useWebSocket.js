import { useState, useEffect, useRef, useCallback } from 'react'

// Fall back to a relative WS URL derived from the page: same host as the site and
// wss when served over HTTPS (e.g. a dev tunnel), routed to the backend via the Vite
// `/ws` proxy. Locally this resolves to ws://localhost:5173/ws/sensors.
const WS_URL = import.meta.env.VITE_WS_URL ||
  `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/sensors`
const MAX_HISTORY = 60  // 60 data points per sensor (~90s at 1.5s interval)

export function useWebSocket() {
  const [readings, setReadings] = useState([])        // latest snapshot (all equipment)
  const [history, setHistory] = useState({})          // { equipmentId: [...last 60 readings] }
  const [connected, setConnected] = useState(false)
  const [alerts, setAlerts] = useState([])
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)  // array of equipment readings

        setReadings(data)

        // Update per-equipment history
        setHistory(prev => {
          const next = { ...prev }
          for (const reading of data) {
            const id = reading.equipment_id
            const existing = prev[id] || []
            next[id] = [...existing.slice(-MAX_HISTORY + 1), reading]
          }
          return next
        })

        // Surface new critical/warning alerts
        const newAlerts = data
          .filter(r => r.status !== 'normal')
          .map(r => ({
            id:           `${r.equipment_id}-${r.timestamp}`,
            equipment_id: r.equipment_id,
            equipment_name: r.equipment_name,
            severity:     r.status,
            message:      r.status === 'critical'
              ? `RUL critical: ${r.rul_predicted} cycles remaining`
              : `Warning: RUL ${r.rul_predicted} cycles — inspect soon`,
            timestamp:    r.timestamp,
            anomaly:      r.is_anomaly,
          }))

        if (newAlerts.length > 0) {
          setAlerts(prev => {
            const combined = [...newAlerts, ...prev]
            // deduplicate by equipment_id + severity; keep latest
            const seen = new Set()
            return combined
              .filter(a => {
                const key = `${a.equipment_id}-${a.severity}`
                if (seen.has(key)) return false
                seen.add(key)
                return true
              })
              .slice(0, 30)
          })
        }
      } catch (e) {
        console.error('WS parse error:', e)
      }
    }

    ws.onclose = () => {
      setConnected(false)
      reconnectTimer.current = setTimeout(connect, 3000)
    }

    ws.onerror = () => ws.close()
  }, [])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  return { readings, history, connected, alerts }
}
