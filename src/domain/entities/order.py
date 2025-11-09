from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Order:
    """Representa una instrucción de trading enviada al broker."""

    order_id: str
    symbol: str
    side: str
    size: float
    order_type: str
    price: float | None
    stop_loss: float | None
    take_profit: float | None
    status: str
    strategy_tag: str | None
    created_at: datetime

    def mark_working(self) -> None:
        """Marca la orden como en estado de ejecución pendiente."""
        raise NotImplementedError()

    def mark_filled(self) -> None:
        """Marca la orden como ejecutada por completo."""
        raise NotImplementedError()

    def mark_canceled(self) -> None:
        """Marca la orden como cancelada."""
        raise NotImplementedError()
