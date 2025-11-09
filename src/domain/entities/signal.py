from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Signal:
    """Representa una intención de operación emitida por una estrategia."""

    symbol: str
    side: str
    strength: float
    reason: str
    entry_type: str
    price_reference: float | None
    time_to_live: int | None
    stop_loss: float | None
    take_profit: float | None
    generated_at: datetime

    def is_valid(self, current_time: datetime, market_hours: object) -> bool:
        """Determina si la señal permanece vigente según el contexto."""
        raise NotImplementedError()
