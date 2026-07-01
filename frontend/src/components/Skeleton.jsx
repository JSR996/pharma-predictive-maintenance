/**
 * Loading skeleton that mirrors the dashboard shell — a product-register loading
 * state (structure placeholders, not a spinner in empty space). The pulse is
 * neutralized by the global prefers-reduced-motion block in index.css.
 */
function Block({ className = '' }) {
  return <div className={`bg-surface2 rounded animate-pulse ${className}`} />
}

function CardSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-surface p-4 shadow-sm">
      <div className="flex items-start justify-between mb-3">
        <div className="space-y-1.5">
          <Block className="h-2.5 w-16" />
          <Block className="h-3 w-24" />
        </div>
        <Block className="h-4 w-4 rounded-full" />
      </div>
      <div className="flex justify-center my-3">
        <Block className="h-[100px] w-[100px] rounded-full" />
      </div>
      <div className="grid grid-cols-2 gap-1.5 mt-3">
        {Array.from({ length: 4 }).map((_, i) => <Block key={i} className="h-9" />)}
      </div>
    </div>
  )
}

export function DashboardSkeleton({ connected }) {
  return (
    <main className="mx-auto max-w-screen-2xl px-6 py-6" aria-busy="true" aria-live="polite">
      <span className="sr-only">
        {connected ? 'Waiting for sensor data' : 'Connecting to PharmaGuard backend'}
      </span>

      {/* Fleet status bar */}
      <div className="mb-6 rounded-xl border border-border bg-surface px-5 py-4 shadow-sm">
        <div className="flex items-center justify-between gap-6">
          <Block className="h-8 w-40" />
          <Block className="h-4 w-48" />
        </div>
        <Block className="h-1.5 w-full mt-4 rounded-full" />
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-3">
          <Block className="h-3 w-28 mb-3" />
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-1 gap-3">
            {Array.from({ length: 5 }).map((_, i) => <CardSkeleton key={i} />)}
          </div>
        </div>

        <div className="lg:col-span-6 space-y-4">
          <div className="flex items-center justify-between">
            <Block className="h-6 w-48" />
            <Block className="h-[90px] w-[90px] rounded-full" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="rounded-xl border border-border bg-surface p-4 shadow-sm">
                <Block className="h-3 w-24 mb-3" />
                <Block className="h-[110px] w-full" />
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-3">
          <div className="rounded-xl border border-border bg-surface p-4 shadow-sm h-full lg:min-h-[600px]">
            <Block className="h-4 w-28 mb-4" />
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => <Block key={i} className="h-14" />)}
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
