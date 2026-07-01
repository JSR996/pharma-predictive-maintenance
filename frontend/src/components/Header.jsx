import { Wifi, WifiOff } from 'lucide-react'

export function Header({ connected, criticalCount }) {
  return (
    <header className="sticky top-0 z-50 border-b border-border bg-surface shadow-sm">
      <div className="mx-auto max-w-screen-2xl px-6 py-3 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div>
            <h1 className="font-display font-bold text-base text-text leading-none">
              PharmaGuard
            </h1>
            <p className="text-[10px] text-subtext tracking-widest uppercase mt-0.5">
              Predictive Maintenance
            </p>
          </div>
        </div>

        {/* Status pills */}
        <div className="flex items-center gap-3">
          {criticalCount > 0 && (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-critical/10 border border-critical/30 text-critical text-xs font-medium pulse-critical">
              <span className="w-1.5 h-1.5 rounded-full bg-critical inline-block" />
              {criticalCount} Critical
            </span>
          )}

          <span
            className={`flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-medium ${
              connected
                ? 'bg-brand/10 border-brand/30 text-brand'
                : 'bg-muted/10 border-border text-subtext'
            }`}
          >
            {connected ? (
              <Wifi className="w-3 h-3" />
            ) : (
              <WifiOff className="w-3 h-3" />
            )}
            {connected ? 'Live' : 'Reconnecting…'}
          </span>
        </div>
      </div>
    </header>
  )
}
