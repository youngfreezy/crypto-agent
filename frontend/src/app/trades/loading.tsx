export default function TradesLoading() {
  return (
    <div className="space-y-6">
      <div className="h-8 w-28 animate-pulse rounded bg-muted" />

      {/* Trade form skeleton */}
      <div className="rounded-xl bg-card ring-1 ring-foreground/10 p-4 space-y-3">
        <div className="h-5 w-24 animate-pulse rounded bg-muted" />
        <div className="flex gap-4">
          <div className="h-8 w-32 animate-pulse rounded bg-muted" />
          <div className="h-8 w-24 animate-pulse rounded bg-muted" />
          <div className="h-8 w-32 animate-pulse rounded bg-muted" />
          <div className="h-8 w-20 animate-pulse rounded bg-muted" />
        </div>
      </div>

      {/* Table skeleton */}
      <div className="rounded-xl bg-card ring-1 ring-foreground/10 p-4 space-y-3">
        <div className="h-5 w-28 animate-pulse rounded bg-muted" />
        <div className="space-y-2">
          <div className="h-10 w-full animate-pulse rounded bg-muted" />
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-12 w-full animate-pulse rounded bg-muted" />
          ))}
        </div>
      </div>
    </div>
  );
}
