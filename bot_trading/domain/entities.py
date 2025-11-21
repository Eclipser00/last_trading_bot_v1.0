"""Entidades de dominio principales del bot de trading.

Todas las estructuras de datos críticas viven aquí como dataclasses para
facilitar su uso en distintas capas respetando los principios SOLID.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SymbolConfig:
    """Configuración de un símbolo a operar.

    Attributes:
        name: Nombre del símbolo/ticker en el broker.
        min_timeframe: Timeframe mínimo disponible en el broker.
        lot_size: Tamaño de lote por defecto para operar el símbolo.
    """

    name: str
    min_timeframe: str
    lot_size: float = 0.0


@dataclass
class StrategyConfig:
    """Configuración específica para estrategias.

    Attributes:
        name: Nombre único de la estrategia.
        timeframes: Lista de timeframes que la estrategia necesita.
    """

    name: str
    timeframes: list[str]


@dataclass
class RiskLimits:
    """Límites de riesgo aplicables al bot.

    Attributes:
        dd_global: Drawdown máximo permitido a nivel global (%).
        dd_por_activo: Límite de drawdown por símbolo.
        dd_por_estrategia: Límite de drawdown por estrategia.
        initial_balance: Balance inicial de la cuenta para calcular drawdown correctamente.
    """

    dd_global: Optional[float] = None
    dd_por_activo: dict[str, float] = field(default_factory=dict)
    dd_por_estrategia: dict[str, float] = field(default_factory=dict)
    initial_balance: float = 10000.0


@dataclass
class Position:
    """Representa una posición abierta en el broker.

    Attributes:
        symbol: Símbolo operado.
        volume: Tamaño de la posición.
        entry_price: Precio de entrada.
        stop_loss: Stop loss asociado.
        take_profit: Take profit asociado.
        strategy_name: Estrategia que abrió la posición.
        open_time: Fecha y hora de apertura.
        magic_number: Número mágico único para identificar la estrategia de forma robusta.
    """

    symbol: str
    volume: float
    entry_price: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    strategy_name: str
    open_time: datetime
    magic_number: Optional[int] = None


@dataclass
class TradeRecord:
    """Registro de un trade cerrado para reporting y exportación.

    Attributes:
        symbol: Símbolo operado.
        strategy_name: Estrategia que generó el trade.
        entry_time: Momento de apertura.
        exit_time: Momento de cierre.
        entry_price: Precio de entrada.
        exit_price: Precio de salida.
        size: Volumen operado.
        pnl: Ganancia o pérdida resultante.
        stop_loss: Stop loss usado.
        take_profit: Take profit usado.
    """

    symbol: str
    strategy_name: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    stop_loss: Optional[float]
    take_profit: Optional[float]


@dataclass
class OrderRequest:
    """Solicitud de orden a enviar al broker.

    Attributes:
        symbol: Símbolo a operar.
        volume: Tamaño del lote.
        order_type: Tipo de orden (BUY/SELL/CLOSE).
        stop_loss: Nivel de stop loss.
        take_profit: Nivel de take profit.
        comment: Comentario opcional para trazabilidad.
        magic_number: Número mágico para identificar la estrategia en el broker.
    """

    symbol: str
    volume: float
    order_type: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    comment: str | None = None
    magic_number: Optional[int] = None


@dataclass
class OrderResult:
    """Resultado de una orden enviada al broker.

    Attributes:
        success: Indica si la orden fue aceptada.
        order_id: Identificador devuelto por el broker.
        error_message: Detalle en caso de fallo.
    """

    success: bool
    order_id: Optional[int] = None
    error_message: Optional[str] = None
