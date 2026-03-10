"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface Analysis {
  id: number;
  symbol: string;
  action: string;
  strength: number;
  reasoning: string;
  indicators: Record<string, number> | null;
  model: string;
  input_tokens: number | null;
  output_tokens: number | null;
  latency_ms: number | null;
  created_at: string;
}

function actionColor(action: string) {
  if (action === "buy") return "default";
  if (action === "sell") return "destructive";
  return "secondary";
}

function strengthBar(strength: number) {
  const pct = Math.round(strength * 100);
  const color =
    strength >= 0.7
      ? "bg-green-500"
      : strength >= 0.4
        ? "bg-yellow-500"
        : "bg-muted-foreground";
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-2 rounded-full bg-muted overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-muted-foreground">{pct}%</span>
    </div>
  );
}

export default function AIPage() {
  const [latest, setLatest] = useState<Analysis[]>([]);
  const [history, setHistory] = useState<Analysis[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [l, h] = await Promise.all([
          api<Analysis[]>("/api/ai-analyses/latest"),
          api<Analysis[]>("/api/ai-analyses?limit=30"),
        ]);
        setLatest(l);
        setHistory(h);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch data");
      }
    }

    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">AI Agent</h1>
        <p className="text-destructive">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">AI Agent</h1>

      {/* Latest analysis per symbol */}
      {latest.length === 0 ? (
        <Card>
          <CardContent className="py-8">
            <p className="text-center text-muted-foreground">
              No AI analyses yet. Activate the <code>claude_ai</code> strategy to start autonomous trading.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {latest.map((a) => (
            <Card key={a.symbol}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{a.symbol}</CardTitle>
                  <Badge variant={actionColor(a.action)}>
                    {a.action.toUpperCase()}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Conviction</p>
                  {strengthBar(a.strength)}
                </div>
                <p className="text-sm leading-relaxed">{a.reasoning}</p>
                {a.indicators && (
                  <div className="flex gap-3 text-xs text-muted-foreground">
                    {a.indicators.rsi != null && (
                      <span>RSI: {a.indicators.rsi.toFixed(1)}</span>
                    )}
                    {a.indicators.sma_fast != null && (
                      <span>SMA10: ${a.indicators.sma_fast.toFixed(0)}</span>
                    )}
                    {a.indicators.sma_slow != null && (
                      <span>SMA50: ${a.indicators.sma_slow.toFixed(0)}</span>
                    )}
                  </div>
                )}
                <div className="flex gap-3 text-xs text-muted-foreground pt-1 border-t border-border">
                  {a.latency_ms != null && <span>{a.latency_ms}ms</span>}
                  {a.input_tokens != null && a.output_tokens != null && (
                    <span>{a.input_tokens + a.output_tokens} tokens</span>
                  )}
                  <span>{new Date(a.created_at).toLocaleTimeString()}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Decision timeline */}
      {history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Decision Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {history.map((a) => (
                <div
                  key={a.id}
                  className="flex gap-4 p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
                >
                  <div className="shrink-0 pt-0.5">
                    <Badge variant={actionColor(a.action)} className="w-14 justify-center">
                      {a.action.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm">{a.symbol}</span>
                      {strengthBar(a.strength)}
                    </div>
                    <p className="text-sm text-muted-foreground">{a.reasoning}</p>
                    <div className="flex gap-3 text-xs text-muted-foreground mt-1">
                      <span>{new Date(a.created_at).toLocaleString()}</span>
                      {a.latency_ms != null && <span>{a.latency_ms}ms</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
