"""Estrategia de ejemplo muy simple para pruebas iniciales."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd

from bot_trading.application.engine.signals import Signal, SignalType
from bot_trading.application.strategies.base import Strategy

logger = logging.getLogger(__name__)


@dataclass
class SimpleExampleStrategy:
    """Plantilla de estrategia basada en un cruce de medias simplificado.
    
    Permite filtrar símbolos específicos mediante allowed_symbols.
    Si allowed_symbols es None, la estrategia opera todos los símbolos disponibles.
    """

    name: str
    timeframes: list[str]
    allowed_symbols: Optional[list[str]] = None  # Lista de símbolos permitidos (None = todos)

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
        
        # Filtrar por símbolos permitidos si está configurado
        if self.allowed_symbols is not None and symbol_name not in self.allowed_symbols:
            logger.debug(
                "Estrategia %s ignora símbolo %s (no está en allowed_symbols: %s)",
                self.name, symbol_name, self.allowed_symbols
            )
            return signals  # Retornar lista vacía si el símbolo no está permitido
        
        if close_series.iloc[-1] > close_series.iloc[-2]:
            # Calcular stop loss y take profit básicos
            current_price = float(close_series.iloc[-1])
            stop_loss = current_price * 0.9975  # 0.25% abajo
            take_profit = current_price * 1.005  # 0.5% arriba
            
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
