from backend.strategies.base import Strategy
from backend.strategies.rsi import RSIStrategy
from backend.strategies.sma_crossover import SMACrossoverStrategy

_strategies: dict[str, Strategy] = {}
_active: dict[str, set[str]] = {}


def register(strategy: Strategy) -> None:
    _strategies[strategy.name] = strategy


def get_strategy(name: str) -> Strategy:
    if name not in _strategies:
        raise KeyError(f"Strategy '{name}' not found. Available: {list(_strategies.keys())}")
    return _strategies[name]


def list_strategies() -> list[dict]:
    return [{"name": s.name, "description": s.description} for s in _strategies.values()]


def activate(strategy_name: str, symbol: str) -> None:
    get_strategy(strategy_name)  # validate existence
    _active.setdefault(strategy_name, set()).add(symbol)


def deactivate(strategy_name: str, symbol: str) -> None:
    get_strategy(strategy_name)  # validate existence
    if strategy_name in _active:
        _active[strategy_name].discard(symbol)
        if not _active[strategy_name]:
            del _active[strategy_name]


def get_active() -> dict[str, list[str]]:
    return {name: sorted(symbols) for name, symbols in _active.items()}


# Register built-in strategies at module load time
register(SMACrossoverStrategy())
register(RSIStrategy())

# Register AI strategy only if API key is configured
from backend.shared.config import get_settings as _get_settings

if _get_settings().ANTHROPIC_API_KEY:
    from backend.strategies.claude_strategy import ClaudeStrategy
    register(ClaudeStrategy())
