from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from src.broker.protocols import BrokerAdapter
from src.data.store import DataStore


@dataclass(slots=True)
class DataFeed:
    """Gestiona la ingesta de datos de mercado."""

    broker: BrokerAdapter
    data_store: DataStore
    subscribed: set[str] = field(default_factory=set)

    def prime_history(self, symbols: Iterable[str], timeframe: str, bars_back: int) -> None:
        """Obtiene historial inicial para cada símbolo requerido."""
        raise NotImplementedError()

    def poll(self) -> None:
        """Consulta el broker para incorporar nuevas observaciones."""
        raise NotImplementedError()

    def resample_if_needed(self) -> None:
        """Aplica resampleo cuando los datos lo requieren."""
        raise NotImplementedError()
