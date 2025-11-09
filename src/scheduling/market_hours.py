from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MarketHours:
    """Define ventanas operativas por símbolo."""

    sessions_by_symbol: dict[str, list[tuple[str, str]]]

    def is_open(self, symbol: str) -> bool:
        """Indica si el mercado está abierto para el símbolo dado."""
        raise NotImplementedError()

    def next_session_open(self, symbol: str) -> str:
        """Devuelve la próxima apertura del símbolo."""
        raise NotImplementedError()

    def next_session_close(self, symbol: str) -> str:
        """Devuelve el próximo cierre del símbolo."""
        raise NotImplementedError()
