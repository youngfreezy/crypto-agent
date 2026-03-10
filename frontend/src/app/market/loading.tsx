export default function MarketLoading() {
  return (
    <div className="space-y-6">
      <div className="h-8 w-28 animate-pulse rounded bg-muted" />

      {/* Tabs skeleton */}
      <div className="flex gap-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-8 w-24 animate-pulse rounded-lg bg-muted" />
        ))}
      </div>

      {/* Price card skeleton */}
      <div className="rounded-xl bg-card ring-1 ring-foreground/10 p-4 space-y-3">
        <div className="h-4 w-28 animate-pulse rounded bg-muted" />
        <div className="h-12 w-48 animate-pulse rounded bg-muted" />
      </div>

      {/* Chart skeleton */}
      <div className="rounded-xl bg-card ring-1 ring-foreground/10 p-4 space-y-3">
        <div className="h-5 w-24 animate-pulse rounded bg-muted" />
        <div className="h-[400px] w-full animate-pulse rounded bg-muted" />
      </div>
    </div>
  );
}
