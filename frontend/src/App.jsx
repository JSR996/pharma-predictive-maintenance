import { useWebSocket } from './hooks/useWebSocket'
import { Header } from './components/Header'
import { Dashboard } from './components/Dashboard'

export default function App() {
  const { readings, history, connected, alerts } = useWebSocket()

  const criticalCount = readings.filter(r => r.status === 'critical').length

  return (
    <div className="min-h-screen bg-bg text-text font-body">
      <Header connected={connected} criticalCount={criticalCount} />
      {readings.length > 0 ? (
        <Dashboard
          readings={readings}
          history={history}
          alerts={alerts}
          connected={connected}
        />
      ) : (
        <div className="flex flex-col items-center justify-center min-h-[80vh] gap-4 text-muted">
          <div className="w-8 h-8 border-2 border-teal/30 border-t-teal rounded-full animate-spin" />
          <p className="text-sm">
            {connected ? 'Waiting for sensor data…' : 'Connecting to PharmaGuard backend…'}
          </p>
          <p className="text-xs text-muted/60">
            Make sure <code className="font-mono bg-surface2 px-1 rounded">uvicorn main:app</code> is running on port 8000
          </p>
        </div>
      )}
    </div>
  )
}
