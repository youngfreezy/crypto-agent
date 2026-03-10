"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const CandleChart = dynamic(() => import("@/components/candle-chart"), {
  ssr: false,
  loading: () => (
    <div className="h-[400px] w-full animate-pulse rounded-lg bg-muted" />
  ),
});

const SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"];

interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

function fmt(n: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n);
}

export default function MarketPage() {
  const [activeSymbol, setActiveSymbol] = useState(SYMBOLS[0]);
  const [prices, setPrices] = useState<Record<string, number>>({});
  const [candles, setCandles] = useState<Candle[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchPrices() {
      try {
        const data = await api<Record<string, number>>("/api/market/prices");
        setPrices(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch prices");
      }
    }

    fetchPrices();
    const interval = setInterval(fetchPrices, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    async function fetchCandles() {
      try {
        const data = await api<Candle[]>(
          `/api/market/candles?symbol=${encodeURIComponent(activeSymbol)}&limit=200`
        );
        setCandles(data);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch candles"
        );
      }
    }

    fetchCandles();
    const interval = setInterval(fetchCandles, 10000);
    return () => clearInterval(interval);
  }, [activeSymbol]);

  const chartData = candles.map((c) => ({
    time: Math.floor(new Date(c.timestamp).getTime() / 1000) as unknown as string,
    open: c.open,
    high: c.high,
    low: c.low,
    close: c.close,
  }));

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Market</h1>

      {error && <p className="text-destructive">Error: {error}</p>}

      <Tabs
        defaultValue={SYMBOLS[0]}
        onValueChange={(val) => setActiveSymbol(val as string)}
      >
        <TabsList>
          {SYMBOLS.map((s) => (
            <TabsTrigger key={s} value={s}>
              {s}
            </TabsTrigger>
          ))}
        </TabsList>

        {SYMBOLS.map((s) => (
          <TabsContent key={s} value={s}>
            <div className="space-y-4">
              {/* Current price */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm text-muted-foreground font-normal">
                    {s} Price
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-4xl font-bold">
                    {prices[s] != null ? fmt(prices[s]) : "--"}
                  </p>
                </CardContent>
              </Card>

              {/* Candlestick chart */}
              <Card>
                <CardHeader>
                  <CardTitle>Price Chart</CardTitle>
                </CardHeader>
                <CardContent>
                  {s === activeSymbol && chartData.length > 0 ? (
                    <CandleChart data={chartData} />
                  ) : (
                    <div className="h-[400px] flex items-center justify-center text-muted-foreground">
                      Loading chart data...
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
