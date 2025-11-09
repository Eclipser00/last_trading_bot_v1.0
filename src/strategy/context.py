from __future__ import annotations

from dataclasses import dataclass

from src.data.store import DataStore
from src.portfolio.portfolio import Portfolio
from src.config.models import Config
from src.scheduling.clock import Clock


@dataclass(slots=True)
class StrategyContext:
    """Provee utilidades y vistas para las estrategias."""

    data_store: DataStore
    portfolio_view: Portfolio
    config: Config
    clock: Clock

    def current_position(self, symbol: str) -> object:
        """Obtiene la posición actual para el símbolo solicitado."""
        raise NotImplementedError()

    def realized_pnl(self, symbol: str) -> float:
        """Calcula el PnL realizado para el símbolo."""
        raise NotImplementedError()

    def volatility(self, symbol: str) -> float:
        """Calcula la volatilidad estimada para el símbolo."""
        raise NotImplementedError()
