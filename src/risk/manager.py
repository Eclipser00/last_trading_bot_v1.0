from __future__ import annotations

from dataclasses import dataclass

from src.config.models import Config
from src.portfolio.portfolio import Portfolio
from src.domain.entities.signal import Signal
from src.domain.entities.order import Order
from src.domain.entities.risk import RiskDecision


@dataclass(slots=True)
class RiskManager:
    """Evalúa señales y órdenes contra límites de riesgo."""

    config: Config
    portfolio: Portfolio

    def check_signal(self, signal: Signal) -> RiskDecision:
        """Determina si una señal cumple con las reglas de riesgo."""
        raise NotImplementedError()

    def position_sizing(self, signal: Signal) -> float:
        """Calcula el tamaño de posición recomendado para la señal."""
        raise NotImplementedError()

    def check_account_limits(self) -> bool:
        """Verifica si los límites de cuenta se respetan."""
        raise NotImplementedError()

    def check_symbol_limits(self, symbol: str) -> bool:
        """Verifica los límites específicos del símbolo."""
        raise NotImplementedError()

    def check_exposure_after(self, order: Order) -> bool:
        """Evalúa exposición posterior a la ejecución de la orden."""
        raise NotImplementedError()

    def register_fill(self, fill_event: object) -> None:
        """Actualiza los medidores de riesgo tras una ejecución."""
        raise NotImplementedError()

    def daily_reset(self) -> None:
        """Reinicia métricas diarias de riesgo cuando corresponde."""
        raise NotImplementedError()
