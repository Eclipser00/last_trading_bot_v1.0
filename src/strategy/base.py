from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from src.domain.entities.signal import Signal
from src.strategy.context import StrategyContext


@dataclass(slots=True)
class StrategyBase(ABC):
    """Clase base para estrategias de trading."""

    name: str
    symbols: list[str]
    params: dict[str, Any] = field(default_factory=dict)
    state: dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    def on_bar(self, context: StrategyContext) -> list[Signal]:
        """Genera señales a partir del contexto de mercado."""
        raise NotImplementedError()

    @abstractmethod
    def on_fill(self, fill_event: Any) -> None:
        """Recibe notificaciones de ejecuciones para actualizar el estado."""
        raise NotImplementedError()

    @abstractmethod
    def on_start(self) -> None:
        """Inicializa recursos antes de comenzar a operar."""
        raise NotImplementedError()

    @abstractmethod
    def on_stop(self) -> None:
        """Libera recursos al finalizar la operación."""
        raise NotImplementedError()

    @abstractmethod
    def health_check(self) -> None:
        """Evalúa el estado interno de la estrategia."""
        raise NotImplementedError()

    @abstractmethod
    def describe(self) -> dict[str, Any]:
        """Entrega metadatos descriptivos de la estrategia."""
        raise NotImplementedError()
