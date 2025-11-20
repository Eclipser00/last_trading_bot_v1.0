"""Servicios para descarga y resampleo de datos de mercado."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Iterable

import pandas as pd

from bot_trading.domain.entities import SymbolConfig
from bot_trading.infrastructure.mt5_client import BrokerClient

logger = logging.getLogger(__name__)

_TIMEFRAME_MAP = {
    "M1": "1min",
    "M5": "5min",
    "M15": "15min",
    "H1": "1H",
    "H4": "4H",
    "D1": "1D",
}


class MarketDataService:
    """Servicio encargado de obtener y resamplear datos OHLCV.

    Trabaja con el BrokerClient para descargar el timeframe mínimo disponible y
    generar las series agregadas solicitadas por las estrategias.
    """

    def __init__(self, broker_client: BrokerClient) -> None:
        self.broker_client = broker_client

    def get_resampled_data(
        self,
        symbol: SymbolConfig,
        target_timeframes: Iterable[str],
        start: datetime,
        end: datetime,
    ) -> dict[str, pd.DataFrame]:
        """Descarga y resamplea datos al conjunto de timeframes deseado.

        Args:
            symbol: Configuración del símbolo.
            target_timeframes: Timeframes a generar.
            start: Fecha de inicio de los datos.
            end: Fecha de fin de los datos.

        Returns:
            Diccionario {timeframe: DataFrame} con las velas resampleadas.
        """
        logger.debug(
            "Solicitando datos para %s desde %s hasta %s en timeframe base %s",
            symbol.name,
            start,
            end,
            symbol.min_timeframe,
        )
        frequencies = set(target_timeframes)
        frequencies.add(symbol.min_timeframe)

        base_freq = _TIMEFRAME_MAP.get(symbol.min_timeframe)
        if base_freq is None:
            raise ValueError(f"Timeframe base no soportado: {symbol.min_timeframe}")

        raw = self.broker_client.get_ohlcv(symbol.name, symbol.min_timeframe, start, end)
        raw.attrs["symbol"] = symbol.name
        if raw.empty:
            logger.warning("No se recibieron datos para %s", symbol.name)
        result: dict[str, pd.DataFrame] = {symbol.min_timeframe: raw}

        for tf in frequencies:
            if tf == symbol.min_timeframe:
                continue
            freq = _TIMEFRAME_MAP.get(tf)
            if freq is None:
                raise ValueError(f"Timeframe solicitado no soportado: {tf}")
            logger.debug("Resampleando %s a frecuencia %s", tf, freq)
            resampled = raw.resample(freq).agg(
                {
                    "open": "first",
                    "high": "max",
                    "low": "min",
                    "close": "last",
                    "volume": "sum",
                }
            ).dropna()
            resampled.attrs["symbol"] = symbol.name
            result[tf] = resampled

        return result
