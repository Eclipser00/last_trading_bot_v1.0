from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Position:
    """Representa una posición abierta en el portafolio."""

    position_id: str
    symbol: str
    side: str
    size: float
    average_price: float
    unrealized_pnl: float
    stop_loss: float | None
    take_profit: float | None
    opened_at: datetime

    def update_mark_to_market(self, quote: float) -> None:
        """Actualiza métricas de mark-to-market para la posición."""
        raise NotImplementedError()

    def set_stop_loss(self, price: float) -> None:
        """Define el nuevo nivel de stop loss."""
        raise NotImplementedError()

    def set_take_profit(self, price: float) -> None:
        """Define el nuevo nivel de take profit."""
        raise NotImplementedError()

    def risk_notional(self) -> float:
        """Calcula el nocional en riesgo asociado a la posición."""
        raise NotImplementedError()
