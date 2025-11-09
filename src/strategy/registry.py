from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from src.strategy.base import StrategyBase


@dataclass(slots=True)
class StrategyRegistry:
    """Gestiona el ciclo de vida de las estrategias registradas."""

    strategies: list[StrategyBase] = field(default_factory=list)
    enabled: set[str] = field(default_factory=set)

    def register(self, strategy: StrategyBase) -> None:
        """Añade una estrategia al registro centralizado."""
        raise NotImplementedError()

    def enable(self, name: str) -> None:
        """Marca una estrategia como habilitada."""
        raise NotImplementedError()

    def disable(self, name: str) -> None:
        """Marca una estrategia como deshabilitada."""
        raise NotImplementedError()

    def iterate(self) -> Iterable[StrategyBase]:
        """Itera sobre las estrategias activas."""
        raise NotImplementedError()
