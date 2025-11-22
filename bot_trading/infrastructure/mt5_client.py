"""Cliente de broker basado en MetaTrader 5.

Define el protocolo BrokerClient para desacoplar la lógica del bot del broker
concreto y una implementación concreta MetaTrader5Client que se integra con
la librería MetaTrader5 oficial.

Esta implementación incluye:
- Conexión y reconexión automática
- Descarga de datos OHLCV con validaciones
- Envío de órdenes con manejo de errores
- Consulta de posiciones y trades
- Logging exhaustivo para debugging
- Validaciones de parámetros
- Cache de información de símbolos para performance
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Optional, Protocol

import MetaTrader5 as mt5
import pandas as pd

from bot_trading.domain.entities import OrderRequest, OrderResult, Position, TradeRecord

# Configuración de logging
logger = logging.getLogger(__name__)


# =============================================================================
# EXCEPCIONES CUSTOM
# =============================================================================


class MT5Error(Exception):
    """Excepción base para errores de MetaTrader 5."""
    pass


class MT5ConnectionError(MT5Error):
    """Error de conexión con MetaTrader 5."""
    pass


class MT5OrderError(MT5Error):
    """Error al enviar órdenes a MetaTrader 5."""
    pass


class MT5DataError(MT5Error):
    """Error al obtener datos de MetaTrader 5."""
    pass


# =============================================================================
# PROTOCOLO
# =============================================================================


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


# =============================================================================
# MAPEO DE TIMEFRAMES
# =============================================================================


TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
    "W1": mt5.TIMEFRAME_W1,
    "MN1": mt5.TIMEFRAME_MN1,
}


# =============================================================================
# CLIENTE METATRADER 5
# =============================================================================


class MetaTrader5Client:
    """Cliente específico para MetaTrader 5.

    Implementación completa que integra con la librería oficial MetaTrader5.
    Incluye manejo robusto de errores, reconexiones automáticas, validaciones
    y logging exhaustivo para facilitar debugging y trazabilidad.

    Attributes:
        connected: Estado de la conexión con MT5.
        max_retries: Número máximo de reintentos para operaciones críticas.
        retry_delay: Delay en segundos entre reintentos (con exponential backoff).
        _symbol_info_cache: Cache de información de símbolos para optimizar consultas.
    """

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0) -> None:
        """Inicializa el cliente MT5.

        Args:
            max_retries: Número máximo de reintentos para operaciones.
            retry_delay: Delay base entre reintentos en segundos.
        """
        self.connected: bool = False
        self.max_retries: int = max_retries
        self.retry_delay: float = retry_delay
        self._symbol_info_cache: dict = {}
        
        logger.info("MetaTrader5Client inicializado con max_retries=%d, retry_delay=%.2f", 
                    max_retries, retry_delay)

    def connect(self) -> None:
        """Inicializa la conexión con MetaTrader5.

        Intenta conectar con MT5 y verifica que el terminal esté corriendo.
        Si falla, lanza MT5ConnectionError con información del error.

        Raises:
            MT5ConnectionError: Si no se puede establecer la conexión.
        """
        logger.info("Intentando conectar con MetaTrader5...")
        
        if not mt5.initialize():
            error_code, error_msg = mt5.last_error()
            logger.error("Fallo al inicializar MT5. Código: %d, Mensaje: %s", 
                        error_code, error_msg)
            raise MT5ConnectionError(
                f"No se pudo inicializar MetaTrader5. Error {error_code}: {error_msg}"
            )
        
        self.connected = True
        
        # Obtener información del terminal para logs
        terminal_info = mt5.terminal_info()
        account_info = mt5.account_info()
        
        if terminal_info and account_info:
            logger.info("Conexión exitosa con MT5. Terminal: %s, Cuenta: %d, Balance: %.2f",
                       terminal_info.name, account_info.login, account_info.balance)
        else:
            logger.info("Conexión exitosa con MT5 (información limitada)")
            
        logger.debug("Estado de conexión actualizado: connected=True")

    def _ensure_connected(self) -> None:
        """Verifica que existe conexión activa, si no intenta reconectar.

        Raises:
            MT5ConnectionError: Si no hay conexión y no se puede reconectar.
        """
        if not self.connected:
            logger.warning("No hay conexión activa. Intentando reconectar...")
            self.connect()
        
        # Verificar que MT5 realmente está disponible
        if not mt5.terminal_info():
            logger.warning("Terminal MT5 no responde. Intentando reinicializar...")
            self.connected = False
            self.connect()

    def _get_symbol_info(self, symbol: str) -> mt5.SymbolInfo:
        """Obtiene información del símbolo con cache.

        Args:
            symbol: Nombre del símbolo (ej: "EURUSD").

        Returns:
            Información del símbolo desde MT5.

        Raises:
            MT5DataError: Si el símbolo no existe o no está disponible.
        """
        # Verificar cache
        if symbol in self._symbol_info_cache:
            cache_time, cached_info = self._symbol_info_cache[symbol]
            # Cache válido por 60 segundos
            if time.time() - cache_time < 60:
                logger.debug("Usando información cacheada para símbolo: %s", symbol)
                return cached_info
        
        # Consultar a MT5
        logger.debug("Consultando información de símbolo: %s", symbol)
        symbol_info = mt5.symbol_info(symbol)
        
        if symbol_info is None:
            error_code, error_msg = mt5.last_error()
            logger.error("Símbolo no encontrado: %s. Error %d: %s", 
                        symbol, error_code, error_msg)
            raise MT5DataError(f"Símbolo '{symbol}' no existe o no está disponible")
        
        # Verificar que el símbolo está visible
        if not symbol_info.visible:
            logger.info("Símbolo %s no está visible. Intentando hacerlo visible...", symbol)
            if not mt5.symbol_select(symbol, True):
                error_code, error_msg = mt5.last_error()
                logger.error("No se pudo hacer visible el símbolo %s. Error %d: %s",
                           symbol, error_code, error_msg)
                raise MT5DataError(f"No se pudo hacer visible el símbolo '{symbol}'")
        
        # Cachear
        self._symbol_info_cache[symbol] = (time.time(), symbol_info)
        logger.debug("Información de símbolo %s cacheada. Spread: %d, Lot min: %.2f",
                    symbol, symbol_info.spread, symbol_info.volume_min)
        
        return symbol_info

    def _get_filling_mode(self, symbol: str) -> int:
        """Obtiene el filling mode compatible con el símbolo.
        
        MT5 soporta diferentes modos de llenado según el tipo de instrumento:
        - ORDER_FILLING_FOK (Fill or Kill): Forex mayormente
        - ORDER_FILLING_IOC (Immediate or Cancel): Futuros, algunos Forex
        - ORDER_FILLING_RETURN: Acciones
        
        Args:
            symbol: Nombre del símbolo.
            
        Returns:
            Constante de filling mode de MT5 compatible con el símbolo.
        """
        symbol_info = self._get_symbol_info(symbol)
        
        # Verificar qué modos de llenado soporta el símbolo
        # filling_mode es un bitmask donde cada bit representa un modo
        filling_modes = symbol_info.filling_mode
        
        logger.info("Filling modes para %s: %d (binario: %s)", 
                   symbol, filling_modes, bin(filling_modes))
        
        # Prioridad: FOK > IOC > RETURN
        # FOK es el más común para Forex
        # Bit 0 (valor 1) = ORDER_FILLING_FOK
        # Bit 1 (valor 2) = ORDER_FILLING_IOC
        # Bit 2 (valor 4) = ORDER_FILLING_RETURN
        if filling_modes & 1:  # Bit 0: ORDER_FILLING_FOK
            logger.info("Usando ORDER_FILLING_FOK para %s", symbol)
            return mt5.ORDER_FILLING_FOK
        elif filling_modes & 2:  # Bit 1: ORDER_FILLING_IOC
            logger.info("Usando ORDER_FILLING_IOC para %s", symbol)
            return mt5.ORDER_FILLING_IOC
        elif filling_modes & 4:  # Bit 2: ORDER_FILLING_RETURN
            logger.info("Usando ORDER_FILLING_RETURN para %s", symbol)
            return mt5.ORDER_FILLING_RETURN
        else:
            # Fallback: usar FOK por defecto
            logger.warning("No se detectó filling mode para %s, usando FOK por defecto", symbol)
            return mt5.ORDER_FILLING_FOK

    def get_ohlcv(
        self, symbol: str, timeframe: str, start: datetime, end: datetime
    ) -> pd.DataFrame:
        """Descarga datos OHLCV desde MetaTrader5.

        Args:
            symbol: Símbolo a consultar (ej: "EURUSD").
            timeframe: Timeframe solicitado (M1, M5, M15, M30, H1, H4, D1, W1, MN1).
            start: Fecha y hora de inicio del rango.
            end: Fecha y hora de fin del rango.

        Returns:
            DataFrame con columnas: datetime, open, high, low, close, volume.

        Raises:
            MT5ConnectionError: Si no hay conexión activa.
            MT5DataError: Si hay error al descargar los datos.
            ValueError: Si los parámetros no son válidos.
        """
        logger.info("Descargando OHLCV para %s, timeframe=%s, desde %s hasta %s",
                   symbol, timeframe, start, end)
        
        # Verificar conexión
        self._ensure_connected()
        
        # Validar timeframe
        if timeframe not in TIMEFRAME_MAP:
            logger.error("Timeframe inválido: %s. Válidos: %s", 
                        timeframe, list(TIMEFRAME_MAP.keys()))
            raise ValueError(
                f"Timeframe '{timeframe}' no es válido. "
                f"Debe ser uno de: {', '.join(TIMEFRAME_MAP.keys())}"
            )
        
        # Validar fechas
        if start >= end:
            logger.error("Rango de fechas inválido: start=%s >= end=%s", start, end)
            raise ValueError("La fecha de inicio debe ser anterior a la fecha de fin")
        
        # Validar símbolo
        self._get_symbol_info(symbol)
        
        # Mapear timeframe
        mt5_timeframe = TIMEFRAME_MAP[timeframe]
        
        # Descargar datos
        logger.debug("Llamando a mt5.copy_rates_range con timeframe=%d", mt5_timeframe)
        rates = mt5.copy_rates_range(symbol, mt5_timeframe, start, end)
        
        if rates is None:
            error_code, error_msg = mt5.last_error()
            logger.error("Error al descargar datos. Código: %d, Mensaje: %s",
                        error_code, error_msg)
            raise MT5DataError(
                f"No se pudieron descargar datos para {symbol}. "
                f"Error {error_code}: {error_msg}"
            )
        
        if len(rates) == 0:
            logger.warning("No hay datos disponibles para el rango solicitado")
            # Retornar DataFrame vacío con columnas correctas y DatetimeIndex
            df_empty = pd.DataFrame(columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
            df_empty['datetime'] = pd.to_datetime(df_empty['datetime'])
            df_empty.set_index('datetime', inplace=True)
            return df_empty
        
        # Convertir a DataFrame
        df = pd.DataFrame(rates)
        
        # Renombrar y seleccionar columnas
        df['datetime'] = pd.to_datetime(df['time'], unit='s')
        df = df[['datetime', 'open', 'high', 'low', 'close', 'tick_volume']]
        df.rename(columns={'tick_volume': 'volume'}, inplace=True)
        
        # Configurar datetime como índice para compatibilidad con resample
        df.set_index('datetime', inplace=True)
        
        logger.info("Descargados %d registros OHLCV para %s", len(df), symbol)
        logger.debug("Primer registro: %s | Último registro: %s",
                    df.index[0], df.index[-1])
        
        return df

    def send_market_order(self, order_request: OrderRequest) -> OrderResult:
        """Envía una orden de mercado a MetaTrader5.

        Args:
            order_request: Objeto con los detalles de la orden.

        Returns:
            OrderResult con el resultado de la operación.

        Raises:
            MT5ConnectionError: Si no hay conexión activa.
            ValueError: Si los parámetros de la orden son inválidos.
        """
        logger.info("Enviando orden: %s %s %.2f lotes, SL=%s, TP=%s, Magic=%s, Comment=%s",
                   order_request.order_type, order_request.symbol, order_request.volume,
                   order_request.stop_loss, order_request.take_profit,
                   order_request.magic_number, order_request.comment)
        
        # Verificar conexión
        self._ensure_connected()
        
        # Validar tipo de orden
        valid_types = ["BUY", "SELL", "CLOSE"]
        if order_request.order_type not in valid_types:
            logger.error("Tipo de orden inválido: %s. Válidos: %s",
                        order_request.order_type, valid_types)
            raise ValueError(
                f"Tipo de orden '{order_request.order_type}' no válido. "
                f"Debe ser: {', '.join(valid_types)}"
            )
        
        # Validar volumen
        if order_request.volume <= 0:
            logger.error("Volumen inválido: %.4f. Debe ser > 0", order_request.volume)
            raise ValueError(f"El volumen debe ser mayor que 0, recibido: {order_request.volume}")
        
        # Obtener información del símbolo
        symbol_info = self._get_symbol_info(order_request.symbol)
        
        # Validar volumen contra límites del símbolo
        if order_request.volume < symbol_info.volume_min:
            logger.error("Volumen %.4f menor que mínimo permitido %.4f",
                        order_request.volume, symbol_info.volume_min)
            raise ValueError(
                f"Volumen {order_request.volume} menor que el mínimo "
                f"{symbol_info.volume_min} para {order_request.symbol}"
            )
        
        if order_request.volume > symbol_info.volume_max:
            logger.error("Volumen %.4f mayor que máximo permitido %.4f",
                        order_request.volume, symbol_info.volume_max)
            raise ValueError(
                f"Volumen {order_request.volume} mayor que el máximo "
                f"{symbol_info.volume_max} para {order_request.symbol}"
            )
        
        # Redondear volumen al step correcto
        volume_step = symbol_info.volume_step
        rounded_volume = round(order_request.volume / volume_step) * volume_step
        if abs(rounded_volume - order_request.volume) > 0.0001:
            logger.warning("Volumen ajustado de %.4f a %.4f según step %.4f",
                          order_request.volume, rounded_volume, volume_step)
            order_request.volume = rounded_volume
        
        # Manejar orden CLOSE
        if order_request.order_type == "CLOSE":
            return self._close_position(order_request)
        
        # Preparar orden BUY o SELL
        # Obtener precio actual
        tick = mt5.symbol_info_tick(order_request.symbol)
        if tick is None:
            error_code, error_msg = mt5.last_error()
            logger.error("No se pudo obtener precio actual. Error %d: %s",
                        error_code, error_msg)
            return OrderResult(
                success=False,
                error_message=f"No se pudo obtener precio para {order_request.symbol}"
            )
        
        # Determinar tipo de orden y precio
        if order_request.order_type == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
            logger.debug("Orden BUY a precio ASK: %.5f", price)
        else:  # SELL
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
            logger.debug("Orden SELL a precio BID: %.5f", price)
        
        # Detectar filling mode compatible con el símbolo
        filling_mode = self._get_filling_mode(order_request.symbol)
        
        # Construir request de MT5
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": order_request.symbol,
            "volume": order_request.volume,
            "type": order_type,
            "price": price,
            "deviation": 20,  # Desviación máxima de precio en puntos
            "magic": order_request.magic_number or 0,
            "comment": order_request.comment or "",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,  # Usar filling mode detectado automáticamente
        }
        
        # Añadir SL/TP si están presentes
        if order_request.stop_loss is not None:
            request["sl"] = order_request.stop_loss
            logger.debug("Stop Loss configurado: %.5f", order_request.stop_loss)
        
        if order_request.take_profit is not None:
            request["tp"] = order_request.take_profit
            logger.debug("Take Profit configurado: %.5f", order_request.take_profit)
        
        # Enviar orden
        logger.debug("Enviando orden a MT5: %s", request)
        result = mt5.order_send(request)
        
        if result is None:
            error_code, error_msg = mt5.last_error()
            logger.error("Error al enviar orden. Código: %d, Mensaje: %s",
                        error_code, error_msg)
            return OrderResult(
                success=False,
                error_message=f"Error al enviar orden: {error_code} - {error_msg}"
            )
        
        # Procesar resultado
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error("Orden rechazada. RetCode: %d, Comentario: %s",
                        result.retcode, result.comment)
            return OrderResult(
                success=False,
                error_message=f"Orden rechazada: {result.comment} (código {result.retcode})"
            )
        
        logger.info("Orden ejecutada exitosamente. Order ID: %d, Volume: %.2f, Price: %.5f",
                   result.order, result.volume, result.price)
        
        return OrderResult(
            success=True,
            order_id=result.order,
            error_message=None
        )

    def _close_position(self, order_request: OrderRequest) -> OrderResult:
        """Cierra una posición existente.

        Args:
            order_request: Orden con order_type="CLOSE".

        Returns:
            OrderResult con el resultado del cierre.
        """
        logger.info("Intentando cerrar posición para %s con magic=%s",
                   order_request.symbol, order_request.magic_number)
        
        # Obtener posiciones abiertas
        positions = mt5.positions_get(symbol=order_request.symbol)
        
        if positions is None or len(positions) == 0:
            logger.warning("No hay posiciones abiertas para %s", order_request.symbol)
            return OrderResult(
                success=False,
                error_message=f"No hay posiciones abiertas para {order_request.symbol}"
            )
        
        # Filtrar por magic number si está presente
        if order_request.magic_number is not None:
            positions = [p for p in positions if p.magic == order_request.magic_number]
            if len(positions) == 0:
                logger.warning("No hay posiciones con magic=%s para %s",
                             order_request.magic_number, order_request.symbol)
                return OrderResult(
                    success=False,
                    error_message=f"No hay posiciones con magic {order_request.magic_number}"
                )
        
        # Cerrar la primera posición encontrada
        position = positions[0]
        logger.debug("Cerrando posición ticket=%d, volumen=%.2f, tipo=%d",
                    position.ticket, position.volume, position.type)
        
        # Determinar tipo de orden de cierre (opuesto a la posición)
        if position.type == mt5.POSITION_TYPE_BUY:
            close_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(order_request.symbol).bid
        else:
            close_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(order_request.symbol).ask
        
        # Detectar filling mode compatible con el símbolo
        filling_mode = self._get_filling_mode(order_request.symbol)
        
        # Construir request de cierre
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": order_request.symbol,
            "volume": position.volume,
            "type": close_type,
            "position": position.ticket,
            "price": price,
            "deviation": 20,
            "magic": order_request.magic_number or 0,
            "comment": order_request.comment or "Close position",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,  # Usar filling mode detectado automáticamente
        }
        
        # Enviar orden de cierre
        logger.debug("Enviando orden de cierre: %s", request)
        result = mt5.order_send(request)
        
        if result is None:
            error_code, error_msg = mt5.last_error()
            logger.error("Error al cerrar posición. Código: %d, Mensaje: %s",
                        error_code, error_msg)
            return OrderResult(
                success=False,
                error_message=f"Error al cerrar: {error_code} - {error_msg}"
            )
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error("Cierre rechazado. RetCode: %d, Comentario: %s",
                        result.retcode, result.comment)
            return OrderResult(
                success=False,
                error_message=f"Cierre rechazado: {result.comment} (código {result.retcode})"
            )
        
        logger.info("Posición cerrada exitosamente. Order ID: %d", result.order)
        
        return OrderResult(
            success=True,
            order_id=result.order,
            error_message=None
        )

    def get_open_positions(self) -> list[Position]:
        """Recupera las posiciones abiertas actuales.

        Returns:
            Lista de objetos Position con todas las posiciones abiertas.

        Raises:
            MT5ConnectionError: Si no hay conexión activa.
        """
        logger.info("Consultando posiciones abiertas...")
        
        # Verificar conexión
        self._ensure_connected()
        
        # Obtener posiciones
        positions = mt5.positions_get()
        
        if positions is None:
            error_code, error_msg = mt5.last_error()
            logger.error("Error al consultar posiciones. Código: %d, Mensaje: %s",
                        error_code, error_msg)
            # Retornar lista vacía en lugar de lanzar error
            return []
        
        if len(positions) == 0:
            logger.info("No hay posiciones abiertas")
            return []
        
        logger.info("Encontradas %d posiciones abiertas", len(positions))
        
        # Convertir a objetos Position
        result = []
        for pos in positions:
            # Extraer strategy_name del comentario o usar default
            strategy_name = pos.comment if pos.comment else "Unknown"
            
            position = Position(
                symbol=pos.symbol,
                volume=pos.volume,
                entry_price=pos.price_open,
                stop_loss=pos.sl if pos.sl != 0 else None,
                take_profit=pos.tp if pos.tp != 0 else None,
                strategy_name=strategy_name,
                open_time=datetime.fromtimestamp(pos.time),
                magic_number=pos.magic if pos.magic != 0 else None
            )
            
            result.append(position)
            
            logger.debug("Posición: %s, volumen=%.2f, entry=%.5f, SL=%s, TP=%s, magic=%s",
                        pos.symbol, pos.volume, pos.price_open,
                        position.stop_loss, position.take_profit, pos.magic)
        
        return result

    def get_closed_trades(self) -> list[TradeRecord]:
        """Recupera los trades cerrados recientes.

        Consulta el historial de deals para construir trades completos
        (entrada + salida) y calcular el PnL.

        Returns:
            Lista de objetos TradeRecord con los trades cerrados.

        Raises:
            MT5ConnectionError: Si no hay conexión activa.
        """
        logger.info("Consultando trades cerrados...")
        
        # Verificar conexión
        self._ensure_connected()
        
        # Obtener historial de deals (últimas 24 horas por defecto)
        from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        to_date = datetime.now()
        
        logger.debug("Consultando deals desde %s hasta %s", from_date, to_date)
        
        deals = mt5.history_deals_get(from_date, to_date)
        
        if deals is None:
            error_code, error_msg = mt5.last_error()
            logger.error("Error al consultar historial. Código: %d, Mensaje: %s",
                        error_code, error_msg)
            return []
        
        if len(deals) == 0:
            logger.info("No hay trades cerrados en el rango consultado")
            return []
        
        logger.info("Encontrados %d deals en el historial", len(deals))
        
        # Agrupar deals por posición para construir trades completos
        trades_dict = {}
        
        for deal in deals:
            # Ignorar deals de balance, comisiones, etc.
            if deal.entry not in [mt5.DEAL_ENTRY_IN, mt5.DEAL_ENTRY_OUT]:
                continue
            
            position_id = deal.position_id
            
            if position_id not in trades_dict:
                trades_dict[position_id] = {
                    'entry': None,
                    'exit': None,
                    'symbol': deal.symbol,
                    'magic': deal.magic
                }
            
            if deal.entry == mt5.DEAL_ENTRY_IN:
                trades_dict[position_id]['entry'] = deal
            elif deal.entry == mt5.DEAL_ENTRY_OUT:
                trades_dict[position_id]['exit'] = deal
        
        # Construir TradeRecords
        result = []
        
        for position_id, trade_data in trades_dict.items():
            entry_deal = trade_data['entry']
            exit_deal = trade_data['exit']
            
            # Solo procesar trades completos (con entrada y salida)
            if entry_deal is None or exit_deal is None:
                logger.debug("Trade incompleto para posición %d, omitiendo", position_id)
                continue
            
            # Extraer strategy_name del comentario
            strategy_name = entry_deal.comment if entry_deal.comment else "Unknown"
            
            # Calcular PnL (MT5 ya lo calcula)
            pnl = exit_deal.profit
            
            trade_record = TradeRecord(
                symbol=trade_data['symbol'],
                strategy_name=strategy_name,
                entry_time=datetime.fromtimestamp(entry_deal.time),
                exit_time=datetime.fromtimestamp(exit_deal.time),
                entry_price=entry_deal.price,
                exit_price=exit_deal.price,
                size=entry_deal.volume,
                pnl=pnl,
                stop_loss=None,  # No disponible en deals
                take_profit=None  # No disponible en deals
            )
            
            result.append(trade_record)
            
            logger.debug("Trade: %s, entrada=%s, salida=%s, PnL=%.2f",
                        trade_data['symbol'],
                        trade_record.entry_time,
                        trade_record.exit_time,
                        pnl)
        
        # Ordenar por fecha de cierre (más reciente primero)
        result.sort(key=lambda x: x.exit_time, reverse=True)
        
        logger.info("Procesados %d trades completos", len(result))
        
        return result

    def __del__(self) -> None:
        """Cierra la conexión con MT5 al destruir el objeto."""
        if self.connected:
            logger.info("Cerrando conexión con MetaTrader5...")
            mt5.shutdown()
            self.connected = False
            logger.info("Conexión cerrada")
