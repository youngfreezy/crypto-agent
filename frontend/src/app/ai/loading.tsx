export default function AILoading() {
  return (
    <div className="space-y-6">
      <div className="h-8 w-28 animate-pulse rounded bg-muted" />

      {/* Latest analysis cards skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="rounded-xl bg-card ring-1 ring-foreground/10 p-4 space-y-3">
            <div className="flex justify-between">
              <div className="h-5 w-24 animate-pulse rounded bg-muted" />
              <div className="h-5 w-14 animate-pulse rounded bg-muted" />
            </div>
            <div className="h-2 w-20 animate-pulse rounded bg-muted" />
            <div className="space-y-1">
              <div className="h-4 w-full animate-pulse rounded bg-muted" />
              <div className="h-4 w-3/4 animate-pulse rounded bg-muted" />
            </div>
          </div>
        ))}
      </div>

      {/* Timeline skeleton */}
      <div className="rounded-xl bg-card ring-1 ring-foreground/10 p-4 space-y-3">
        <div className="h-5 w-36 animate-pulse rounded bg-muted" />
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-20 w-full animate-pulse rounded bg-muted" />
        ))}
      </div>
    </div>
  );
}
