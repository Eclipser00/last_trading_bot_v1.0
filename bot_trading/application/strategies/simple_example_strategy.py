"""Estrategia de ejemplo muy simple para pruebas iniciales."""
from __future__ import annotations

import logging
from dataclasses import dataclass
import pandas as pd

from bot_trading.application.engine.signals import Signal, SignalType
from bot_trading.application.strategies.base import Strategy

logger = logging.getLogger(__name__)


@dataclass
class SimpleExampleStrategy:
    """Plantilla de estrategia basada en un cruce de medias simplificado."""

    name: str
    timeframes: list[str]

    def generate_signals(self, data_by_timeframe: dict[str, pd.DataFrame]) -> list[Signal]:
        """Genera señales dummy para guiar el flujo del bot."""
        signals: list[Signal] = []
        if not self.timeframes:
            return signals
        tf = self.timeframes[0]
        data = data_by_timeframe.get(tf)
        if data is None or len(data) < 2:
            logger.debug("Datos insuficientes para generar señal en %s", tf)
            return signals

        close_series = data["close"]
        symbol_name = data.attrs.get("symbol", "")
        if close_series.iloc[-1] > close_series.iloc[-2]:
            signals.append(
                Signal(
                    symbol=symbol_name,
                    strategy_name=self.name,
                    timeframe=tf,
                    signal_type=SignalType.BUY,
                    size=0.01,
                    stop_loss=None,
                    take_profit=None,
                )
            )
        else:
            logger.debug("No se genera señal operable en %s", tf)
        return signals
