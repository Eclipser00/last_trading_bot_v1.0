"""Tests del motor principal del bot."""
from datetime import datetime, timedelta

import pandas as pd

from bot_trading.application.engine.bot_engine import TradingBot
from bot_trading.application.engine.order_executor import OrderExecutor
from bot_trading.application.risk_management import RiskManager
from bot_trading.application.strategies.base import Strategy
from bot_trading.application.engine.signals import Signal, SignalType
from bot_trading.domain.entities import OrderResult, SymbolConfig, RiskLimits
from bot_trading.infrastructure.data_fetcher import MarketDataService


class FakeBroker:
    """Implementación falsa de BrokerClient para pruebas de integración."""

    def __init__(self) -> None:
        self.orders_sent: list = []

    def connect(self) -> None:
        return None

    def get_ohlcv(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> pd.DataFrame:
        index = pd.date_range(start=start, end=end, freq="1min")
        data = {"open": [1.0] * len(index), "high": [1.0] * len(index), "low": [1.0] * len(index), "close": [1.0] * len(index), "volume": [1] * len(index)}
        return pd.DataFrame(data, index=index)

    def send_market_order(self, order_request):
        self.orders_sent.append(order_request)
        return OrderResult(success=True, order_id=len(self.orders_sent))

    def get_open_positions(self):
        return []

    def get_closed_trades(self):
        return []


class DummyStrategy:
    """Estrategia que siempre emite una señal de compra."""

    name = "dummy"
    timeframes = ["M1"]

    def generate_signals(self, data_by_timeframe):
        return [
            Signal(
                symbol="EURUSD",
                strategy_name=self.name,
                timeframe="M1",
                signal_type=SignalType.BUY,
                size=0.01,
                stop_loss=None,
                take_profit=None,
            )
        ]


def test_trading_bot_run_once_ejecuta_flujo_basico() -> None:
    """run_once debe descargar datos, evaluar riesgo y enviar órdenes."""
    broker = FakeBroker()
    market_data = MarketDataService(broker)
    risk_manager = RiskManager(RiskLimits())
    executor = OrderExecutor(broker)
    bot = TradingBot(
        broker_client=broker,
        market_data_service=market_data,
        risk_manager=risk_manager,
        order_executor=executor,
        strategies=[DummyStrategy()],
        symbols=[SymbolConfig(name="EURUSD", min_timeframe="M1", lot_size=0.01)],
    )

    now = datetime(2023, 1, 1, 0, 10)
    bot.run_once(now=now)

    assert len(broker.orders_sent) == 1
