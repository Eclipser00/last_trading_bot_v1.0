"""Motor principal del bot de trading."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from bot_trading.application.engine.order_executor import OrderExecutor
from bot_trading.application.engine.signals import SignalType
from bot_trading.application.risk_management import RiskManager
from bot_trading.application.strategy_registry import StrategyRegistry
from bot_trading.application.strategies.base import Strategy
from bot_trading.domain.entities import OrderRequest, SymbolConfig, TradeRecord
from bot_trading.infrastructure.data_fetcher import MarketDataService

logger = logging.getLogger(__name__)


@dataclass
class TradingBot:
    """Coordina la ejecución completa del bot."""

    broker_client: object
    market_data_service: MarketDataService
    risk_manager: RiskManager
    order_executor: OrderExecutor
    strategies: list[Strategy]
    symbols: list[SymbolConfig]
    trade_history: list[TradeRecord] = field(default_factory=list)
    strategy_registry: StrategyRegistry = field(default_factory=StrategyRegistry)
    
    def __post_init__(self) -> None:
        """Inicializa el registro de estrategias después de la construcción."""
        # Registrar todas las estrategias al iniciar
        for strategy in self.strategies:
            self.strategy_registry.register_strategy(strategy.name)

    def run_once(self, now: datetime | None = None) -> None:
        """Ejecuta un ciclo completo del bot una sola vez."""
        current_time = now or datetime.now(timezone.utc)
        logger.info("Iniciando ciclo del bot en %s", current_time)
        
        # Sincronizar estado de órdenes abiertas con el broker
        self.order_executor.sync_state()
        
        # Actualizar trade_history con trades cerrados del broker
        self._update_trade_history()
        
        if not self.risk_manager.check_bot_risk_limits(self.trade_history):
            logger.warning("Bot bloqueado por límites globales de riesgo")
            return

        for symbol in self.symbols:
            if not self.risk_manager.check_symbol_risk_limits(symbol.name, self.trade_history):
                logger.info("Símbolo %s bloqueado por riesgo", symbol.name)
                continue

            # Calcular timeframes requeridos SOLO para estrategias que operan este símbolo
            required_timeframes = set()
            for strategy in self.strategies:
                # Verificar si la estrategia puede operar este símbolo
                # Si allowed_symbols no existe o es None, la estrategia opera todos los símbolos
                can_operate = True
                if hasattr(strategy, 'allowed_symbols') and strategy.allowed_symbols is not None:
                    can_operate = symbol.name in strategy.allowed_symbols
                
                if can_operate:
                    required_timeframes.update(strategy.timeframes)
            
            # Si no hay timeframes requeridos para este símbolo, saltar
            if not required_timeframes:
                logger.debug("No hay estrategias que operen %s, saltando", symbol.name)
                continue
            
            # Filtrar timeframes incompatibles con el min_timeframe del símbolo
            # Solo mantener timeframes >= min_timeframe
            compatible_timeframes = set()
            tf_order = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
            try:
                min_tf_idx = tf_order.index(symbol.min_timeframe)
                for tf in required_timeframes:
                    if tf in tf_order:
                        tf_idx = tf_order.index(tf)
                        if tf_idx >= min_tf_idx:
                            compatible_timeframes.add(tf)
                    else:
                        # Si no está en la lista, incluir por seguridad
                        compatible_timeframes.add(tf)
            except ValueError:
                # Si min_timeframe no está en la lista, usar todos
                compatible_timeframes = required_timeframes
            
            required_timeframes = compatible_timeframes
            
            if not required_timeframes:
                logger.warning(
                    "No hay timeframes compatibles para %s (min_timeframe=%s). "
                    "Las estrategias requieren timeframes incompatibles.",
                    symbol.name, symbol.min_timeframe
                )
                continue
            
            # Calcular ventana de datos necesaria basada en estrategias
            data_window = self._calculate_data_window(required_timeframes)
            
            try:
                data_by_timeframe = self.market_data_service.get_resampled_data(
                    symbol=symbol,
                    target_timeframes=required_timeframes,
                    start=current_time - data_window,
                    end=current_time,
                )
            except Exception as e:
                logger.error("Error obteniendo datos para %s: %s", symbol.name, e)
                continue

            for strategy in self.strategies:
                if not self.risk_manager.check_strategy_risk_limits(
                    strategy.name, self.trade_history
                ):
                    logger.info(
                        "Estrategia %s bloqueada por riesgo", strategy.name
                    )
                    continue

                signals = strategy.generate_signals(data_by_timeframe)
                logger.debug(
                    "Estrategia %s generó %d señales para %s",
                    strategy.name,
                    len(signals),
                    symbol.name,
                )
                
                # Obtener Magic Number de la estrategia (debe estar registrada)
                magic_number = self.strategy_registry.get_magic_number(strategy.name)
                if magic_number is None:
                    logger.error(
                        "Estrategia %s no tiene Magic Number asignado. Registrándola ahora.",
                        strategy.name
                    )
                    magic_number = self.strategy_registry.register_strategy(strategy.name)
                
                for signal in signals:
                    if signal.signal_type in {SignalType.BUY, SignalType.SELL}:
                        # Verificar si ya existe una posición abierta
                        if self.order_executor.has_open_position(
                            signal.symbol, 
                            strategy.name,
                            magic_number
                        ):
                            logger.debug(
                                "Orden %s ignorada: ya existe posición abierta para %s con estrategia %s",
                                signal.signal_type.value,
                                signal.symbol,
                                strategy.name,
                            )
                            continue
                        
                        order_request = OrderRequest(
                            symbol=signal.symbol,
                            volume=signal.size,
                            order_type=signal.signal_type.value,
                            stop_loss=signal.stop_loss,
                            take_profit=signal.take_profit,
                            comment=f"{signal.strategy_name}-{signal.timeframe}",
                            magic_number=magic_number,
                        )
                        result = self.order_executor.execute_order(order_request)
                        if result.success:
                            logger.info("Orden ejecutada exitosamente: %s", result.order_id)
                    elif signal.signal_type == SignalType.CLOSE:
                        # Verificar existencia antes de intentar cerrar
                        if not self.order_executor.has_open_position(
                            signal.symbol, 
                            strategy.name,
                            magic_number
                        ):
                            logger.debug(
                                "Señal CLOSE ignorada: no existe posición abierta para %s", 
                                signal.symbol
                            )
                            continue

                        order_request = OrderRequest(
                            symbol=signal.symbol,
                            volume=signal.size,
                            order_type=signal.signal_type.value,
                            stop_loss=signal.stop_loss,
                            take_profit=signal.take_profit,
                            comment=f"{signal.strategy_name}-{signal.timeframe}",
                            magic_number=magic_number,
                        )
                        self.order_executor.execute_order(order_request)
                    else:
                        logger.debug(
                            "Señal %s ignorada por ser tipo %s",
                            signal,
                            signal.signal_type,
                        )

    def run_forever(self, sleep_seconds: int = 60) -> None:
        """Ejecuta el bot en bucle infinito con pausas."""
        import time

        while True:
            self.run_once()
            time.sleep(sleep_seconds)

    def run_synchronized(self, timeframe_minutes: int = 1, wait_after_close: int = 5) -> None:
        """Ejecuta el bot sincronizado con el cierre de velas.
        
        Espera hasta que cierre la vela del timeframe especificado, luego espera
        wait_after_close segundos adicionales antes de ejecutar el ciclo.
        
        Esta función es ideal para operar en múltiples timeframes ya que sincroniza
        con el cierre de velas del timeframe base (típicamente M1).
        
        Args:
            timeframe_minutes: Duración de la vela en minutos (1=M1, 5=M5, 15=M15, 60=H1, etc.).
            wait_after_close: Segundos a esperar después del cierre de la vela.
        
        Ejemplo para M1:
            - Vela cierra a las 17:21:00
            - Espera hasta 17:21:05 (5 seg después)
            - Ejecuta run_once()
            - Espera hasta 17:22:05 (próxima vela + 5 seg)
            - Repite
        
        Ejemplo para M5:
            - Vela cierra a las 17:20:00, 17:25:00, 17:30:00...
            - Espera 5 seg después de cada cierre
            - Ejecuta run_once()
        """
        import time
        
        logger.info("="*80)
        logger.info("Iniciando bucle sincronizado con velas de %d minutos", timeframe_minutes)
        logger.info("Esperando %d segundos después del cierre de cada vela", wait_after_close)
        logger.info("Presiona Ctrl+C para detener el bot")
        logger.info("="*80)
        
        while True:
            try:
                # Calcular cuánto falta para el próximo cierre de vela
                now = datetime.now(timezone.utc)
                
                # Calcular el próximo cierre según el timeframe
                if timeframe_minutes == 1:
                    # Para M1: próximo minuto
                    next_close = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
                elif timeframe_minutes == 5:
                    # Para M5: próximo múltiplo de 5 minutos
                    minutes_to_add = 5 - (now.minute % 5)
                    if minutes_to_add == 5:
                        minutes_to_add = 0
                    next_close = now.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_add)
                elif timeframe_minutes == 15:
                    # Para M15: próximo múltiplo de 15 minutos
                    minutes_to_add = 15 - (now.minute % 15)
                    if minutes_to_add == 15:
                        minutes_to_add = 0
                    next_close = now.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_add)
                elif timeframe_minutes == 30:
                    # Para M30: próximo múltiplo de 30 minutos
                    minutes_to_add = 30 - (now.minute % 30)
                    if minutes_to_add == 30:
                        minutes_to_add = 0
                    next_close = now.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_add)
                elif timeframe_minutes == 60:
                    # Para H1: próxima hora
                    next_close = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                elif timeframe_minutes == 240:
                    # Para H4: próxima hora múltiplo de 4
                    hours_to_add = 4 - (now.hour % 4)
                    if hours_to_add == 4:
                        hours_to_add = 0
                    next_close = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=hours_to_add)
                else:
                    # Genérico: próximo múltiplo del timeframe
                    minutes_to_add = timeframe_minutes - (now.minute % timeframe_minutes)
                    if minutes_to_add == timeframe_minutes:
                        minutes_to_add = 0
                    next_close = now.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_add)
                
                # Añadir tiempo de espera después del cierre
                execution_time = next_close + timedelta(seconds=wait_after_close)
                
                # Calcular segundos a esperar
                wait_seconds = (execution_time - now).total_seconds()
                
                if wait_seconds > 0:
                    logger.info(
                        "Esperando %.1f segundos hasta %s (cierre de vela + %d seg)",
                        wait_seconds, execution_time.strftime("%H:%M:%S"), wait_after_close
                    )
                    time.sleep(wait_seconds)
                elif wait_seconds < -1:
                    # Si ya pasó el tiempo, calcular el siguiente
                    logger.debug("Tiempo de ejecución ya pasó, calculando siguiente vela...")
                    continue
                
                # Ejecutar ciclo del bot
                logger.info("-"*80)
                logger.info("Ejecutando ciclo de trading en %s", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
                logger.info("-"*80)
                self.run_once()
                
            except KeyboardInterrupt:
                logger.info("\n⚠️ Bucle interrumpido por el usuario")
                break
            except Exception as e:
                logger.error("❌ Error en bucle sincronizado: %s", e, exc_info=True)
                # Esperar un poco antes de reintentar para evitar loops infinitos de errores
                logger.info("Esperando 10 segundos antes de reintentar...")
                time.sleep(10)

    def _update_trade_history(self) -> None:
        """Actualiza el historial de trades con los cerrados del broker.
        
        Usa una tupla con entry_time, exit_time, symbol y strategy_name para identificar
        trades únicos de forma más robusta.
        """
        try:
            closed_trades = self.broker_client.get_closed_trades()
            # Agregar solo los nuevos trades que no estén ya en el historial
            # Usar strategy_name en lugar de magic_number ya que TradeRecord no lo tiene
            existing_trades = {
                (t.entry_time, t.exit_time, t.symbol, t.strategy_name) 
                for t in self.trade_history
            }
            for trade in closed_trades:
                trade_key = (trade.entry_time, trade.exit_time, trade.symbol, trade.strategy_name)
                if trade_key not in existing_trades:
                    self.trade_history.append(trade)
                    logger.debug("Trade cerrado agregado al historial: %s", trade)
        except NotImplementedError:
            # El broker simulado no implementa get_closed_trades
            logger.debug("Broker no soporta get_closed_trades, historial no actualizado")
        except Exception as e:
            logger.error("Error actualizando historial de trades: %s", e)

    def _calculate_data_window(self, timeframes: set[str]) -> timedelta:
        """Calcula la ventana de tiempo necesaria para los timeframes solicitados.
        
        Asegura que haya suficientes datos para calcular indicadores técnicos,
        pero limitando la ventana para ser compatible con MetaTrader5.
        
        MT5 tiene límites en la cantidad de datos históricos que puede descargar
        en una sola consulta, especialmente para timeframes pequeños.
        
        Args:
            timeframes: Conjunto de timeframes requeridos.
            
        Returns:
            Timedelta con la ventana de datos necesaria.
        """
        # Mapeo de timeframe a minutos
        tf_minutes = {
            "M1": 1,
            "M5": 5,
            "M15": 15,
            "M30": 30,
            "H1": 60,
            "H4": 240,
            "D1": 1440,
        }
        
        # Límites de velas por timeframe (compatibles con MT5)
        # IMPORTANTE: Estos valores deben considerar que descargamos desde el timeframe
        # MÍNIMO y lo remuestreamos. Por ello, para timeframes altos usamos ventanas
        # más cortas para no exceder los límites de MT5 al descargar el timeframe base.
        max_candles_by_tf = {
            "M1": 1440,    # 1 día de datos (suficiente para análisis intraday)
            "M5": 1440,    # 5 días de datos
            "M15": 1000,   # ~10 días de datos
            "M30": 720,    # ~15 días de datos
            "H1": 500,     # ~20 días de datos
            "H4": 500,     # ~50 días de datos (12000 velas M1 = aprox. 8 días)
            "D1": 500,     # ~200 días de datos
        }
        
        # Encontrar el timeframe más alto (más lento)
        max_minutes = 1
        max_tf = "M1"
        for tf in timeframes:
            minutes = tf_minutes.get(tf, 1)
            if minutes > max_minutes:
                max_minutes = minutes
                max_tf = tf
        
        # Usar el límite de velas apropiado para ese timeframe
        max_candles = max_candles_by_tf.get(max_tf, 500)
        
        # Ventana = número de velas * duración de cada vela
        data_window = timedelta(minutes=max_minutes * max_candles)
        
        logger.debug(
            "Ventana de datos calculada: %s (%d velas de %s) para timeframes %s",
            data_window, max_candles, max_tf, timeframes
        )
        
        return data_window
