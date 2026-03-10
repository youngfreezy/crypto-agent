"""Anthropic SDK wrapper for autonomous market analysis."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Optional

import anthropic

from backend.shared.config import get_settings

logger = logging.getLogger(__name__)

_client: Optional[anthropic.Anthropic] = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        settings = get_settings()
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


SYSTEM_PROMPT = """You are an autonomous quantitative crypto trader managing a paper trading portfolio.

Your job: analyze the market data provided and decide whether to BUY, SELL, or HOLD for the given symbol.

Decision framework:
- Be conservative. Most of the time, HOLD is the right call.
- Only BUY when multiple indicators align (trend + momentum + volume confirmation).
- Only SELL when you have a position AND see clear reversal signals or risk.
- Never chase pumps or panic sell. Look for confluence.
- Consider your existing positions — don't double down blindly.
- Factor in fees (0.1%) and slippage (0.05%) when assessing if a trade is worth it.

You MUST respond with exactly one JSON object, nothing else:
{"action": "buy" | "sell" | "hold", "strength": 0.0 to 1.0, "reasoning": "2-3 sentence explanation"}

strength guidelines:
- 0.1-0.3: weak signal, borderline
- 0.4-0.6: moderate conviction
- 0.7-0.9: strong signal, high confidence
- 1.0: extremely rare, only for obvious setups"""


def build_user_prompt(
    symbol: str,
    candles: list[dict],
    indicators: dict,
    portfolio: dict,
    recent_trades: list[dict],
    all_prices: dict,
) -> str:
    """Build the dynamic user prompt with market context."""
    # Price action summary from last 60 candles
    if candles:
        current = candles[-1]["close"]
        high_1h = max(c["high"] for c in candles)
        low_1h = min(c["low"] for c in candles)
        vol_sum = sum(c["volume"] for c in candles)
        open_1h = candles[0]["open"]
        change_pct = ((current - open_1h) / open_1h) * 100 if open_1h else 0
    else:
        current = high_1h = low_1h = vol_sum = change_pct = 0

    # Format positions
    positions_str = "None"
    if portfolio.get("positions"):
        pos_lines = []
        for p in portfolio["positions"]:
            pnl = p.get("unrealized_pnl", 0)
            pos_lines.append(
                f"  {p['symbol']}: {p['quantity']:.6f} @ ${p['avg_entry']:.2f} "
                f"(unrealized P&L: ${pnl:.2f})"
            )
        positions_str = "\n".join(pos_lines)

    # Format recent trades
    trades_str = "None"
    if recent_trades:
        trade_lines = []
        for t in recent_trades:
            pnl_str = f", P&L: ${t['pnl']:.2f}" if t.get("pnl") else ""
            trade_lines.append(
                f"  {t['side'].upper()} {t['symbol']} {t['quantity']:.6f} @ ${t['fill_price']:.2f}{pnl_str}"
            )
        trades_str = "\n".join(trade_lines)

    # Cross-symbol prices
    market_lines = []
    for sym, price in sorted(all_prices.items()):
        market_lines.append(f"  {sym}: ${price:.2f}")
    market_str = "\n".join(market_lines) if market_lines else "  No data"

    return f"""SYMBOL: {symbol}

PRICE ACTION (last {len(candles)} 1m candles):
  Current: ${current:.2f}
  1h High: ${high_1h:.2f}
  1h Low: ${low_1h:.2f}
  1h Change: {change_pct:+.2f}%
  1h Volume: {vol_sum:.2f}

TECHNICAL INDICATORS:
  SMA(10): ${indicators.get('sma_fast', 0):.2f}
  SMA(50): ${indicators.get('sma_slow', 0):.2f}
  RSI(14): {indicators.get('rsi', 50):.1f}
  Price vs SMA(50): {'above' if current > indicators.get('sma_slow', current) else 'below'}

PORTFOLIO:
  Cash: ${portfolio.get('cash', 0):.2f}
  Total Value: ${portfolio.get('total_value', 0):.2f}
  Positions:
{positions_str}

RECENT TRADES (by this strategy):
{trades_str}

MARKET OVERVIEW:
{market_str}

What is your decision for {symbol}?"""


def analyze_market(
    symbol: str,
    candles: list[dict],
    indicators: dict,
    portfolio: dict,
    recent_trades: list[dict],
    all_prices: dict,
) -> Optional[dict]:
    """Call Claude to analyze market conditions and return a trading decision.

    Returns dict with keys: action, strength, reasoning, input_tokens, output_tokens, latency_ms
    or None on error.
    """
    user_prompt = build_user_prompt(
        symbol, candles, indicators, portfolio, recent_trades, all_prices
    )

    start = time.time()
    try:
        client = get_client()
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except anthropic.APIError as e:
        logger.error("Claude API error for %s: %s", symbol, e)
        return None
    except Exception as e:
        logger.error("Unexpected error calling Claude for %s: %s", symbol, e)
        return None

    latency_ms = int((time.time() - start) * 1000)

    # Extract text from response
    text = ""
    for block in response.content:
        if block.type == "text":
            text = block.text
            break

    if not text:
        logger.warning("Empty response from Claude for %s", symbol)
        return None

    # Parse JSON — try direct parse, then extract from markdown code block
    result = _parse_json_response(text)
    if result is None:
        logger.warning("Failed to parse Claude response for %s: %s", symbol, text[:200])
        return None

    # Validate and normalize
    action = result.get("action", "hold").lower()
    if action not in ("buy", "sell", "hold"):
        action = "hold"

    strength = result.get("strength", 0.5)
    try:
        strength = max(0.0, min(1.0, float(strength)))
    except (ValueError, TypeError):
        strength = 0.5

    reasoning = result.get("reasoning", "No reasoning provided")

    return {
        "action": action,
        "strength": strength,
        "reasoning": reasoning,
        "market_summary": user_prompt,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "latency_ms": latency_ms,
    }


def _parse_json_response(text: str) -> Optional[dict]:
    """Try to parse JSON from Claude's response, handling markdown code blocks."""
    # Try direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding JSON object in text
    match = re.search(r"\{[^{}]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None
