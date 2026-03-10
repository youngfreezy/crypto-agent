"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"];
const PAGE_SIZE = 50;

interface Trade {
  symbol: string;
  side: string;
  quantity: number;
  fill_price: number;
  fee: number | null;
  pnl: number | null;
  strategy_name: string | null;
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

export default function TradesPage() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [symbol, setSymbol] = useState(SYMBOLS[0]);
  const [side, setSide] = useState<"buy" | "sell">("buy");
  const [quantity, setQuantity] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function fetchTrades(currentOffset: number) {
    try {
      const data = await api<Trade[]>(
        `/api/trades?limit=${PAGE_SIZE}&offset=${currentOffset}`
      );
      setTrades(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch trades");
    }
  }

  useEffect(() => {
    fetchTrades(offset);
    const interval = setInterval(() => fetchTrades(offset), 10000);
    return () => clearInterval(interval);
  }, [offset]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!quantity || Number(quantity) <= 0) {
      toast.error("Enter a valid quantity");
      return;
    }
    setSubmitting(true);
    try {
      await api("/api/trades", {
        method: "POST",
        body: JSON.stringify({ symbol, side, quantity: Number(quantity) }),
      });
      toast.success(`${side.toUpperCase()} order placed for ${quantity} ${symbol}`);
      setQuantity("");
      fetchTrades(offset);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to place trade"
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Trades</h1>

      {/* Manual trade form */}
      <Card>
        <CardHeader>
          <CardTitle>Place Trade</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-4">
            {/* Symbol select */}
            <div className="space-y-1.5">
              <label className="text-sm text-muted-foreground">Symbol</label>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="flex h-8 rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {SYMBOLS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            {/* Side toggle */}
            <div className="space-y-1.5">
              <label className="text-sm text-muted-foreground">Side</label>
              <div className="flex gap-1">
                <Button
                  type="button"
                  size="sm"
                  variant={side === "buy" ? "default" : "outline"}
                  onClick={() => setSide("buy")}
                  className={
                    side === "buy"
                      ? "bg-green-600 hover:bg-green-700 text-white"
                      : ""
                  }
                >
                  BUY
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant={side === "sell" ? "default" : "outline"}
                  onClick={() => setSide("sell")}
                  className={
                    side === "sell"
                      ? "bg-red-600 hover:bg-red-700 text-white"
                      : ""
                  }
                >
                  SELL
                </Button>
              </div>
            </div>

            {/* Quantity */}
            <div className="space-y-1.5">
              <label className="text-sm text-muted-foreground">Quantity</label>
              <input
                type="number"
                step="any"
                min="0"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder="0.00"
                className="flex h-8 w-32 rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            <Button type="submit" disabled={submitting} size="sm">
              {submitting ? "Placing..." : "Submit"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Error */}
      {error && <p className="text-destructive">Error: {error}</p>}

      {/* Trade history */}
      <Card>
        <CardHeader>
          <CardTitle>Trade History</CardTitle>
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
                <TableHead className="text-right">Fee</TableHead>
                <TableHead className="text-right">P&L</TableHead>
                <TableHead>Strategy</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {trades.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={8}
                    className="text-center text-muted-foreground"
                  >
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
                    <TableCell className="text-right">
                      {t.fee != null ? fmt(t.fee) : "-"}
                    </TableCell>
                    <TableCell
                      className={`text-right ${pnlColor(t.pnl ?? 0)}`}
                    >
                      {t.pnl != null ? fmt(t.pnl) : "-"}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {t.strategy_name ?? "-"}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>

          {/* Pagination */}
          <div className="flex items-center justify-between mt-4">
            <Button
              variant="outline"
              size="sm"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            >
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Showing {offset + 1} - {offset + trades.length}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={trades.length < PAGE_SIZE}
              onClick={() => setOffset(offset + PAGE_SIZE)}
            >
              Next
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
