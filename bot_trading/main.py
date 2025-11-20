"""Punto de entrada principal del bot de trading."""
from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd

from bot_trading.application.engine.bot_engine import TradingBot
from bot_trading.application.engine.order_executor import OrderExecutor
from bot_trading.application.risk_management import RiskManager
from bot_trading.application.strategies.simple_example_strategy import SimpleExampleStrategy
from bot_trading.domain.entities import RiskLimits, SymbolConfig
from bot_trading.infrastructure.data_fetcher import MarketDataService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FakeBroker:
    """Broker simulado para ejecutar el ejemplo sin conexiones reales."""

    def __init__(self) -> None:
        self.orders_sent: list = []

    def connect(self) -> None:
        logger.info("Simulando conexión a broker")

    def get_ohlcv(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> pd.DataFrame:
        index = pd.date_range(start=start, end=end, freq="1min")
        data = {
            "open": [1.0] * len(index),
            "high": [1.0] * len(index),
            "low": [1.0] * len(index),
            "close": [float(i) for i in range(len(index))],
            "volume": [1] * len(index),
        }
        df = pd.DataFrame(data, index=index)
        df.attrs["symbol"] = symbol
        return df

    def send_market_order(self, order_request):
        self.orders_sent.append(order_request)
        logger.info("Orden simulada enviada: %s", order_request)
        from bot_trading.domain.entities import OrderResult

        return OrderResult(success=True, order_id=len(self.orders_sent))

    def get_open_positions(self):
        return []

    def get_closed_trades(self):
        return []


def main() -> None:
    """Ejecuta un ejemplo mínimo del bot.

    En esta fase inicial se utilizan mocks para demostrar el flujo sin tocar el
    broker real.
    """
    broker = FakeBroker()
    market_data_service = MarketDataService(broker)
    risk_manager = RiskManager(RiskLimits(dd_global=1000))
    order_executor = OrderExecutor(broker)
    strategy = SimpleExampleStrategy(name="simple", timeframes=["M1"])
    symbols = [SymbolConfig(name="EURUSD", min_timeframe="M1", lot_size=0.01)]

    bot = TradingBot(
        broker_client=broker,
        market_data_service=market_data_service,
        risk_manager=risk_manager,
        order_executor=order_executor,
        strategies=[strategy],
        symbols=symbols,
    )

    bot.run_once(now=datetime.utcnow())
    logger.info("Órdenes enviadas en ejemplo: %d", len(broker.orders_sent))


if __name__ == "__main__":
    main()
