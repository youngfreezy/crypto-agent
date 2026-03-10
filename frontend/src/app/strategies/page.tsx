"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const AVAILABLE_SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"];

interface Strategy {
  name: string;
  description: string;
  active_symbols: string[];
}

export default function StrategiesPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<Record<string, boolean>>({});

  async function fetchStrategies() {
    try {
      const data = await api<Strategy[]>("/api/strategies");
      setStrategies(data);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch strategies"
      );
    }
  }

  useEffect(() => {
    fetchStrategies();
    const interval = setInterval(fetchStrategies, 10000);
    return () => clearInterval(interval);
  }, []);

  async function toggleSymbol(
    strategyName: string,
    symbol: string,
    activate: boolean
  ) {
    const key = `${strategyName}-${symbol}`;
    setLoading((prev) => ({ ...prev, [key]: true }));
    try {
      const action = activate ? "activate" : "deactivate";
      await api(`/api/strategies/${strategyName}/${action}`, {
        method: "POST",
        body: JSON.stringify({ symbol }),
      });
      toast.success(
        `${activate ? "Activated" : "Deactivated"} ${symbol} on ${strategyName}`
      );
      fetchStrategies();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to update strategy"
      );
    } finally {
      setLoading((prev) => ({ ...prev, [key]: false }));
    }
  }

  if (error) {
    return (
      <div className="text-destructive">
        <h1 className="text-2xl font-bold mb-4">Strategies</h1>
        <p>Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Strategies</h1>

      {strategies.length === 0 ? (
        <p className="text-muted-foreground">No strategies configured.</p>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {strategies.map((s) => (
            <Card key={s.name}>
              <CardHeader>
                <CardTitle>{s.name}</CardTitle>
                <CardDescription>{s.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Active symbols */}
                {s.active_symbols.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {s.active_symbols.map((sym) => (
                      <Badge key={sym} variant="secondary">
                        {sym}
                      </Badge>
                    ))}
                  </div>
                )}

                {/* Symbol toggle buttons */}
                <div className="space-y-2">
                  {AVAILABLE_SYMBOLS.map((sym) => {
                    const isActive = s.active_symbols.includes(sym);
                    const key = `${s.name}-${sym}`;
                    return (
                      <div
                        key={sym}
                        className="flex items-center justify-between"
                      >
                        <span className="text-sm">{sym}</span>
                        <Button
                          size="sm"
                          variant={isActive ? "destructive" : "default"}
                          disabled={loading[key]}
                          onClick={() =>
                            toggleSymbol(s.name, sym, !isActive)
                          }
                        >
                          {loading[key]
                            ? "..."
                            : isActive
                            ? "Deactivate"
                            : "Activate"}
                        </Button>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
