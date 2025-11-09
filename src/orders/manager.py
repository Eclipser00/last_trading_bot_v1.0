from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from src.broker.protocols import BrokerAdapter
from src.risk.manager import RiskManager
from src.portfolio.portfolio import Portfolio
from src.domain.entities.signal import Signal
from src.domain.entities.order import Order


@dataclass(slots=True)
class OrderManager:
    """Transforma señales en órdenes y gestiona su ciclo de vida."""

    broker: BrokerAdapter
    risk: RiskManager
    portfolio: Portfolio
    pending_queue: deque[Order] = field(default_factory=deque)

    def signal_to_order(self, signal: Signal) -> Order:
        """Construye una orden ejecutable a partir de una señal aprobada."""
        raise NotImplementedError()

    def route(self, order: Order) -> str:
        """Envía la orden al broker y devuelve su identificador."""
        raise NotImplementedError()

    def amend(self, order_id: str, **new_params) -> None:  # type: ignore[no-untyped-def]
        """Modifica los parámetros de una orden existente."""
        raise NotImplementedError()

    def cancel(self, order_id: str) -> None:
        """Solicita la cancelación de una orden."""
        raise NotImplementedError()

    def sync_with_broker(self) -> None:
        """Reconcilia el estado local con la información del broker."""
        raise NotImplementedError()

    def on_fill(self, fill_event: object) -> None:
        """Procesa un fill reportado por el broker."""
        raise NotImplementedError()
