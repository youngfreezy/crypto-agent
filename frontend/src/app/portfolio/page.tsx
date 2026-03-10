"use client";

import { useEffect, useState } from "react";
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

interface Position {
  symbol: string;
  quantity: number;
  avg_entry: number;
  current_price: number;
  unrealized_pnl: number;
}

interface Portfolio {
  cash: number;
  positions: Position[];
  total_value: number;
  unrealized_pnl: number;
  realized_pnl: number;
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

export default function PortfolioPage() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await api<Portfolio>("/api/portfolio");
        setPortfolio(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch portfolio");
      }
    }

    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className="text-destructive">
        <h1 className="text-2xl font-bold mb-4">Portfolio</h1>
        <p>Error: {error}</p>
      </div>
    );
  }

  if (!portfolio) return null;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Portfolio</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm text-muted-foreground font-normal">
            Cash Balance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold">{fmt(portfolio.cash)}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Positions</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Symbol</TableHead>
                <TableHead className="text-right">Quantity</TableHead>
                <TableHead className="text-right">Avg Entry</TableHead>
                <TableHead className="text-right">Current Price</TableHead>
                <TableHead className="text-right">Value</TableHead>
                <TableHead className="text-right">Unrealized P&L</TableHead>
                <TableHead className="text-right">% of Portfolio</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {portfolio.positions.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={7}
                    className="text-center text-muted-foreground"
                  >
                    No open positions.
                  </TableCell>
                </TableRow>
              ) : (
                portfolio.positions.map((p) => {
                  const value = p.quantity * p.current_price;
                  const pct =
                    portfolio.total_value > 0
                      ? (value / portfolio.total_value) * 100
                      : 0;
                  return (
                    <TableRow key={p.symbol}>
                      <TableCell className="font-medium">{p.symbol}</TableCell>
                      <TableCell className="text-right">{p.quantity.toFixed(6)}</TableCell>
                      <TableCell className="text-right">
                        {fmt(p.avg_entry)}
                      </TableCell>
                      <TableCell className="text-right">
                        {fmt(p.current_price)}
                      </TableCell>
                      <TableCell className="text-right">
                        {fmt(value)}
                      </TableCell>
                      <TableCell
                        className={`text-right ${pnlColor(p.unrealized_pnl)}`}
                      >
                        {fmt(p.unrealized_pnl)}
                      </TableCell>
                      <TableCell className="text-right">
                        {pct.toFixed(1)}%
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
