from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.entities.position import Position
from src.domain.entities.order import Order


@dataclass(slots=True)
class Portfolio:
    """Mantiene el estado financiero y operacional del bot."""

    positions: dict[str, Position] = field(default_factory=dict)
    orders: dict[str, Order] = field(default_factory=dict)
    cash: float | None = None
    equity: float | None = None
    margin_used: float | None = None
    exposure_by_symbol: dict[str, float] = field(default_factory=dict)
    history: list[object] = field(default_factory=list)

    def update_from_broker(self, broker_state: object) -> None:
        """Sincroniza el estado local con la información del broker."""
        raise NotImplementedError()

    def get_exposure(self, symbol: str | None = None) -> float:
        """Devuelve la exposición agregada o por símbolo."""
        raise NotImplementedError()

    def estimate_pnl(self, symbol: str) -> float:
        """Estima el PnL del símbolo utilizando datos recientes."""
        raise NotImplementedError()

    def apply_fill(self, fill_event: object) -> None:
        """Actualiza el portafolio tras una ejecución."""
        raise NotImplementedError()

    def close_all(self) -> None:
        """Cierra todas las posiciones abiertas."""
        raise NotImplementedError()
