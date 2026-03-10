"""Symbol list utilities."""

from backend.shared.config import get_settings


def get_symbols() -> list[str]:
    """Parse the comma-separated SYMBOLS setting into a list of trimmed strings."""
    settings = get_settings()
    return [s.strip() for s in settings.SYMBOLS.split(",") if s.strip()]
