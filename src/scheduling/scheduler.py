from __future__ import annotations

from dataclasses import dataclass

from src.scheduling.clock import Clock


@dataclass(slots=True)
class Scheduler:
    """Coordina el ritmo del ciclo de ejecución."""

    clock: Clock

    def should_run(self) -> bool:
        """Determina si el ciclo debe ejecutarse en el instante actual."""
        raise NotImplementedError()

    def wait_next(self) -> None:
        """Orquesta la espera hasta el siguiente ciclo permitido."""
        raise NotImplementedError()
