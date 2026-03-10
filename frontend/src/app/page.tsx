"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

const EquityChart = dynamic(() => import("@/components/equity-chart"), {
  ssr: false,
  loading: () => (
    <div className="h-[350px] w-full animate-pulse rounded-lg bg-muted" />
  ),
});

interface Portfolio {
  cash: number;
  positions: Record<string, unknown>[];
  total_value: number;
  unrealized_pnl: number;
  realized_pnl: number;
}

interface HistoryPoint {
  total_value: number;
  created_at: string;
}

interface Trade {
  symbol: string;
  side: string;
  quantity: number;
  fill_price: number;
  pnl: number | null;
  created_at: string;
}

interface AIAnalysis {
  symbol: string;
  action: string;
  strength: number;
  reasoning: string;
  created_at: string;
}

function fmt(n: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(n);
}

function pnlColor(n: number) {
  if (n > 0) return "text-green-400";
  if (n < 0) return "text-red-400";
  return "text-muted-foreground";
}

export default function DashboardPage() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [history, setHistory] = useState<{ time: string; value: number }[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [aiLatest, setAiLatest] = useState<AIAnalysis[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [p, h, t, ai] = await Promise.all([
          api<Portfolio>("/api/portfolio"),
          api<HistoryPoint[]>("/api/portfolio/history"),
          api<Trade[]>("/api/trades?limit=5"),
          api<AIAnalysis[]>("/api/ai-analyses/latest").catch(() => []),
        ]);
        setPortfolio(p);
        setHistory(
          h.map((pt) => ({
            time: Math.floor(new Date(pt.created_at).getTime() / 1000) as unknown as string,
            value: pt.total_value,
          }))
        );
        setTrades(t);
        setAiLatest(ai);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch data");
      }
    }

    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className="text-destructive">
        <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
        <p>Error: {error}</p>
      </div>
    );
  }

  if (!portfolio) {
    return null; // loading.tsx handles this
  }

  const stats = [
    { label: "Total Value", value: fmt(portfolio.total_value) },
    { label: "Cash Balance", value: fmt(portfolio.cash) },
    {
      label: "Unrealized P&L",
      value: fmt(portfolio.unrealized_pnl),
      color: pnlColor(portfolio.unrealized_pnl),
    },
    {
      label: "Realized P&L",
      value: fmt(portfolio.realized_pnl),
      color: pnlColor(portfolio.realized_pnl),
    },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s) => (
          <Card key={s.label}>
            <CardHeader>
              <CardTitle className="text-sm text-muted-foreground font-normal">
                {s.label}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className={`text-2xl font-bold ${s.color ?? ""}`}>{s.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Equity curve */}
      <Card>
        <CardHeader>
          <CardTitle>Equity Curve</CardTitle>
        </CardHeader>
        <CardContent>
          {history.length > 0 ? (
            <EquityChart data={history} />
          ) : (
            <p className="text-muted-foreground text-sm">No history data yet.</p>
          )}
        </CardContent>
      </Card>

      {/* AI Agent latest */}
      {aiLatest.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>AI Agent Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {aiLatest.map((a) => (
                <div key={a.symbol} className="p-3 rounded-lg bg-muted/30 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-sm">{a.symbol}</span>
                    <Badge
                      variant={
                        a.action === "buy"
                          ? "default"
                          : a.action === "sell"
                            ? "destructive"
                            : "secondary"
                      }
                    >
                      {a.action.toUpperCase()}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-2">
                    {a.reasoning}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(a.created_at).toLocaleTimeString()}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent trades */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>Symbol</TableHead>
                <TableHead>Side</TableHead>
                <TableHead className="text-right">Quantity</TableHead>
                <TableHead className="text-right">Price</TableHead>
                <TableHead className="text-right">P&L</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {trades.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground">
                    No trades yet.
                  </TableCell>
                </TableRow>
              ) : (
                trades.map((t, i) => (
                  <TableRow key={i}>
                    <TableCell>
                      {new Date(t.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="font-medium">{t.symbol}</TableCell>
                    <TableCell>
                      <Badge
                        variant={t.side === "buy" ? "default" : "destructive"}
                      >
                        {t.side.toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">{t.quantity.toFixed(6)}</TableCell>
                    <TableCell className="text-right">
                      {fmt(t.fill_price)}
                    </TableCell>
                    <TableCell
                      className={`text-right ${pnlColor(t.pnl ?? 0)}`}
                    >
                      {t.pnl != null ? fmt(t.pnl) : "-"}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
