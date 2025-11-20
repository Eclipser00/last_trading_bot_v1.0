"""Motor principal del bot de trading."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from bot_trading.application.engine.order_executor import OrderExecutor
from bot_trading.application.engine.signals import SignalType
from bot_trading.application.risk_management import RiskManager
from bot_trading.application.strategies.base import Strategy
from bot_trading.domain.entities import OrderRequest, SymbolConfig
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
    trade_history: list = field(default_factory=list)

    def run_once(self, now: datetime | None = None) -> None:
        """Ejecuta un ciclo completo del bot una sola vez."""
        current_time = now or datetime.utcnow()
        logger.info("Iniciando ciclo del bot en %s", current_time)
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
            data_by_timeframe = self.market_data_service.get_resampled_data(
                symbol=symbol,
                target_timeframes=required_timeframes,
                start=current_time - timedelta(minutes=30),
                end=current_time,
            )

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
                for signal in signals:
                    if signal.signal_type in {SignalType.BUY, SignalType.SELL, SignalType.CLOSE}:
                        order_request = OrderRequest(
                            symbol=signal.symbol,
                            volume=signal.size,
                            order_type=signal.signal_type.value,
                            stop_loss=signal.stop_loss,
                            take_profit=signal.take_profit,
                            comment=f"{signal.strategy_name}-{signal.timeframe}",
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
