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
        symbol_name = data.attrs.get("symbol", "UNKNOWN")
        
        # Validar que tenemos un símbolo válido
        if not symbol_name or symbol_name == "UNKNOWN":
            logger.warning("Símbolo no disponible en attrs del DataFrame")
            return signals
        
        if close_series.iloc[-1] > close_series.iloc[-2]:
            # Calcular stop loss y take profit básicos
            current_price = float(close_series.iloc[-1])
            stop_loss = current_price * 0.99  # 1% abajo
            take_profit = current_price * 1.02  # 2% arriba
            
            signals.append(
                Signal(
                    symbol=symbol_name,
                    strategy_name=self.name,
                    timeframe=tf,
                    signal_type=SignalType.BUY,
                    size=0.01,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                )
            )
            logger.debug("Señal BUY generada para %s en %s", symbol_name, tf)
        else:
            logger.debug("No se genera señal operable en %s", tf)
        return signals
