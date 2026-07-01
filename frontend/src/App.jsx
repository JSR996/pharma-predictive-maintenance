import { useWebSocket } from './hooks/useWebSocket'
import { ToastProvider } from './hooks/useToast'
import { Header } from './components/Header'
import { Dashboard } from './components/Dashboard'
import { DashboardSkeleton } from './components/Skeleton'

export default function App() {
  const { readings, history, connected, alerts } = useWebSocket()

  const criticalCount = readings.filter(r => r.status === 'critical').length

  return (
    <ToastProvider>
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
        <>
          {!connected && (
            <div className="mx-auto max-w-screen-2xl px-6 pt-4">
              <p className="text-xs text-subtext">
                Connecting to the sensor stream… make sure{' '}
                <code className="font-mono bg-surface2 px-1 rounded">uvicorn main:app</code> is running on port 8000.
              </p>
            </div>
          )}
          <DashboardSkeleton connected={connected} />
        </>
      )}
    </div>
    </ToastProvider>
  )
}
