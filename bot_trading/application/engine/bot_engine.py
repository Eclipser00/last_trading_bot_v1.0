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

            required_timeframes = set()
            for strategy in self.strategies:
                required_timeframes.update(strategy.timeframes)
            
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
        
        Asegura que haya suficientes datos para calcular indicadores técnicos.
        Por ejemplo, para MA(200) en timeframe alto necesitamos 200+ velas.
        
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
        
        # Usar al menos 500 velas del timeframe más alto
        # (suficiente para MA(200) con margen)
        max_minutes = 1
        for tf in timeframes:
            minutes = tf_minutes.get(tf, 1)
            if minutes > max_minutes:
                max_minutes = minutes
        
        # Ventana = 500 velas del timeframe más alto
        data_window = timedelta(minutes=max_minutes * 500)
        logger.debug("Ventana de datos calculada: %s para timeframes %s", 
                     data_window, timeframes)
        return data_window
