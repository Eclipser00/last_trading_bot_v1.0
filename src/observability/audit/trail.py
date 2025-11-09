from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.order import Order
from src.domain.entities.signal import Signal
from src.domain.entities.risk import RiskDecision


@dataclass(slots=True)
class AuditTrail:
    """Registra eventos clave para auditoría posterior."""

    def record_order(self, order: Order) -> None:
        """Persiste información relevante de la orden."""
        raise NotImplementedError()

    def record_signal(self, signal: Signal) -> None:
        """Registra una señal generada por una estrategia."""
        raise NotImplementedError()

    def record_risk(self, decision: RiskDecision) -> None:
        """Registra el resultado de una evaluación de riesgo."""
        raise NotImplementedError()

    def record_fill(self, fill_event: object) -> None:
        """Registra detalles de una ejecución en el broker."""
        raise NotImplementedError()
