"""Configuración global y utilidades del bot."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bot_trading.domain.entities import RiskLimits


@dataclass
class BotConfig:
    """Configuración principal del bot de trading."""

    symbols: list[str]
    data_path: Path
    risk_limits: RiskLimits
