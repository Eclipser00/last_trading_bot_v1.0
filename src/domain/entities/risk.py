from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RiskDecision:
    """Resultado de la evaluación de riesgo para una señal u orden."""

    status: str
    adjusted_size: float | None
    notes: str | None
