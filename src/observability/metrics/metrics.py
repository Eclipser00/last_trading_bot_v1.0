from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Metrics:
    """Gestiona métricas operativas y de desempeño."""

    def update_equity_curve(self) -> None:
        """Actualiza la curva de equity con el estado más reciente."""
        raise NotImplementedError()

    def update_drawdowns(self) -> None:
        """Recalcula los drawdowns actuales del portafolio."""
        raise NotImplementedError()

    def exposure_gauges(self) -> None:
        """Actualiza indicadores de exposición por símbolo y global."""
        raise NotImplementedError()

    def export_snapshots(self) -> None:
        """Exporta instantáneas de métricas para análisis externo."""
        raise NotImplementedError()
