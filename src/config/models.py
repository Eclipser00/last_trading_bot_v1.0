from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Config:
    """Parámetros de configuración del bot."""

    symbols: list[str] = field(default_factory=list)
    timeframe: str | None = None
    max_account_drawdown: float | None = None
    max_symbol_drawdown: float | None = None
    max_account_exposure: float | None = None
    max_symbol_exposure: float | None = None
    risk_per_trade: float | None = None
    commissions: dict[str, float] = field(default_factory=dict)
    slippage: dict[str, float] = field(default_factory=dict)
    financing: dict[str, float] = field(default_factory=dict)
    market_schedule: dict[str, Any] = field(default_factory=dict)
    storage_paths: dict[str, Path] = field(default_factory=dict)
    log_level: str | None = None
    heartbeat_ms: int | None = None

    def validate(self) -> None:
        """Verifica que los valores cumplan con las reglas del negocio."""
        raise NotImplementedError()

    @classmethod
    def from_file(cls, path: Path) -> Config:
        """Construye la configuración a partir de un archivo externo."""
        raise NotImplementedError()

    def to_file(self, path: Path) -> None:
        """Persiste la configuración en un archivo."""
        raise NotImplementedError()
