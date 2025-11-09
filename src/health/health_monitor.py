from __future__ import annotations

from dataclasses import dataclass

from src.data.feed import DataFeed
from src.broker.protocols import BrokerAdapter


@dataclass(slots=True)
class HealthMonitor:
    """Supervisa la salud operativa de servicios críticos."""

    data_feed: DataFeed
    broker: BrokerAdapter

    def watch_connectivity(self) -> None:
        """Monitoriza la conectividad con el broker."""
        raise NotImplementedError()

    def watch_staleness(self) -> None:
        """Verifica la frescura de los datos recibidos."""
        raise NotImplementedError()

    def auto_reconnect(self) -> None:
        """Intenta restablecer conexiones fallidas."""
        raise NotImplementedError()

    def alerting(self) -> None:
        """Dispara alertas cuando se detectan anomalías."""
        raise NotImplementedError()
