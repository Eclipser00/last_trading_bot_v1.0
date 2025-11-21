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
            
        Raises:
            ValueError: Si el timeframe no está soportado.
            RuntimeError: Si hay errores en el resampleo.
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

        # Validar timeframes soportados
        base_freq = _TIMEFRAME_MAP.get(symbol.min_timeframe)
        if base_freq is None:
            raise ValueError(f"Timeframe base no soportado: {symbol.min_timeframe}")
        
        for tf in frequencies:
            if tf not in _TIMEFRAME_MAP:
                raise ValueError(f"Timeframe solicitado no soportado: {tf}")
            # Validar que el timeframe solicitado sea >= al timeframe base
            if not self._is_timeframe_compatible(symbol.min_timeframe, tf):
                logger.warning(
                    "Timeframe %s no es compatible con timeframe base %s",
                    tf, symbol.min_timeframe
                )

        try:
            raw = self.broker_client.get_ohlcv(symbol.name, symbol.min_timeframe, start, end)
        except Exception as e:
            logger.error("Error descargando datos desde broker: %s", e)
            raise RuntimeError(f"No se pudieron obtener datos para {symbol.name}") from e
        
        # Asegurar que el símbolo esté en attrs
        raw.attrs["symbol"] = symbol.name
        
        if raw.empty:
            logger.warning("No se recibieron datos para %s", symbol.name)
            return {symbol.min_timeframe: raw}
        
        result: dict[str, pd.DataFrame] = {symbol.min_timeframe: raw}

        for tf in frequencies:
            if tf == symbol.min_timeframe:
                continue
            freq = _TIMEFRAME_MAP.get(tf)
            if freq is None:
                continue  # Ya validado anteriormente
            
            try:
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
                # Preservar attrs después del resampleo
                resampled.attrs["symbol"] = symbol.name
                result[tf] = resampled
            except Exception as e:
                logger.error("Error resampleando a %s: %s", tf, e)
                # Continuar con otros timeframes en lugar de fallar completamente
                continue

        return result

    def _is_timeframe_compatible(self, base_tf: str, target_tf: str) -> bool:
        """Verifica si un timeframe objetivo es compatible con el timeframe base.
        
        Args:
            base_tf: Timeframe base disponible.
            target_tf: Timeframe objetivo a generar.
            
        Returns:
            True si target_tf >= base_tf (puede resamplearse).
        """
        tf_order = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
        try:
            base_idx = tf_order.index(base_tf)
            target_idx = tf_order.index(target_tf)
            return target_idx >= base_idx
        except ValueError:
            # Si alguno no está en la lista, asumir compatible
            return True
