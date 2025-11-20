"""Cliente de broker basado en MetaTrader 5.

Define el protocolo BrokerClient para desacoplar la lógica del bot del broker
concreto y una implementación concreta MetaTrader5Client que se integrará con
la librería MetaTrader5 en el futuro.
"""
from __future__ import annotations

from datetime import datetime
from typing import Protocol

import pandas as pd

from bot_trading.domain.entities import OrderRequest, OrderResult, Position, TradeRecord


class BrokerClient(Protocol):
    """Protocolo para clientes de broker.

    Cualquier implementación concreta debe proveer los métodos indicados para
    ser utilizada por el bot sin depender de la librería específica.
    """

    def connect(self) -> None:
        """Realiza la conexión con el broker."""

    def get_ohlcv(
        self, symbol: str, timeframe: str, start: datetime, end: datetime
    ) -> pd.DataFrame:
        """Obtiene datos OHLCV para un símbolo y timeframe."""

    def send_market_order(self, order_request: OrderRequest) -> OrderResult:
        """Envía una orden a mercado y devuelve el resultado."""

    def get_open_positions(self) -> list[Position]:
        """Recupera las posiciones abiertas."""

    def get_closed_trades(self) -> list[TradeRecord]:
        """Recupera trades cerrados recientes."""


class MetaTrader5Client:
    """Cliente específico para MetaTrader 5.

    Esta implementación se deja como esqueleto preparado para integrar llamadas
    reales a la librería MetaTrader5 cuando se configure el entorno. Se incluyen
    logs y puntos de extensión para manejo de reconexiones y errores.
    """

    def __init__(self) -> None:
        self.connected: bool = False

    def connect(self) -> None:
        """Inicializa la conexión con MetaTrader5."""
        raise NotImplementedError(
            "Debería realizar la conexión con MetaTrader5 y autenticar la sesión."
        )

    def get_ohlcv(
        self, symbol: str, timeframe: str, start: datetime, end: datetime
    ) -> pd.DataFrame:
        """Descarga datos OHLCV desde MetaTrader5.

        Debería manejar reconexiones y validaciones de parámetros.
        """
        raise NotImplementedError(
            "Debería descargar datos desde MetaTrader5 respetando el timeframe solicitado."
        )

    def send_market_order(self, order_request: OrderRequest) -> OrderResult:
        """Envía una orden de mercado a MetaTrader5.

        Se debe validar la respuesta, manejar errores y reintentos.
        """
        raise NotImplementedError(
            "Debería enviar la orden a MetaTrader5 y devolver el resultado interpretado."
        )

    def get_open_positions(self) -> list[Position]:
        """Recupera las posiciones abiertas actuales."""
        raise NotImplementedError(
            "Debería consultar las posiciones abiertas desde MetaTrader5."
        )

    def get_closed_trades(self) -> list[TradeRecord]:
        """Recupera los trades cerrados recientes."""
        raise NotImplementedError(
            "Debería consultar el historial de trades cerrados desde MetaTrader5."
        )
