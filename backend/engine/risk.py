from backend.engine.order_book import Order

MAX_POSITION_PCT = 0.20  # 20% of portfolio in a single asset


def check_order(
    order: Order,
    cash_balance: float,
    positions: dict,
    latest_prices: dict,
    portfolio_value: float,
) -> tuple[bool, str]:
    """Validate an order against risk limits. Returns (allowed, reason)."""

    price = latest_prices.get(order.symbol)
    if price is None:
        return False, f"No price available for {order.symbol}"

    if order.side == "buy":
        cost = order.quantity * price
        if cost > cash_balance:
            return False, (
                f"Insufficient cash: need ${cost:.2f}, have ${cash_balance:.2f}"
            )

        # Check max position size after this buy
        current_qty = positions.get(order.symbol, 0.0)
        new_value = (current_qty + order.quantity) * price
        if portfolio_value > 0 and new_value / portfolio_value > MAX_POSITION_PCT:
            return False, (
                f"Position would be {new_value / portfolio_value:.1%} of portfolio, "
                f"exceeds max {MAX_POSITION_PCT:.0%}"
            )

    elif order.side == "sell":
        current_qty = positions.get(order.symbol, 0.0)
        if order.quantity > current_qty:
            return False, (
                f"Insufficient position: want to sell {order.quantity}, "
                f"hold {current_qty}"
            )

    return True, "OK"
