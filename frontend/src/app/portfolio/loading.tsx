export default function PortfolioLoading() {
  return (
    <div className="space-y-6">
      <div className="h-8 w-36 animate-pulse rounded bg-muted" />

      {/* Cash card skeleton */}
      <div className="rounded-xl bg-card ring-1 ring-foreground/10 p-4 space-y-3">
        <div className="h-4 w-24 animate-pulse rounded bg-muted" />
        <div className="h-8 w-32 animate-pulse rounded bg-muted" />
      </div>

      {/* Positions table skeleton */}
      <div className="rounded-xl bg-card ring-1 ring-foreground/10 p-4 space-y-3">
        <div className="h-5 w-24 animate-pulse rounded bg-muted" />
        <div className="space-y-2">
          <div className="h-10 w-full animate-pulse rounded bg-muted" />
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-12 w-full animate-pulse rounded bg-muted" />
          ))}
        </div>
      </div>
    </div>
  );
}
