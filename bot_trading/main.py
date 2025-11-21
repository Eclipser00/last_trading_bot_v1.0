"""Punto de entrada principal del bot de trading."""
from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# Permite ejecutar este archivo directamente (Run File) asegurando que el paquete este en sys.path.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bot_trading.application.engine.bot_engine import TradingBot
from bot_trading.application.engine.order_executor import OrderExecutor
from bot_trading.application.risk_management import RiskManager
from bot_trading.application.strategies.simple_example_strategy import SimpleExampleStrategy
from bot_trading.domain.entities import RiskLimits, SymbolConfig
from bot_trading.infrastructure.data_fetcher import MarketDataService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FakeBroker:
    """Broker simulado para ejecutar el ejemplo sin conexiones reales.
    
    Mantiene el estado de posiciones abiertas para evitar abrir infinitas órdenes
    en el mismo símbolo/estrategia.
    """

    def __init__(self) -> None:
        self.orders_sent: list = []
        self.open_positions: list = []
        self.closed_trades: list = []

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
        from bot_trading.domain.entities import OrderResult, Position, TradeRecord
        
        self.orders_sent.append(order_request)
        order_id = len(self.orders_sent)
        logger.info("Orden simulada enviada: %s (ID: %d, Magic: %s)", 
                   order_request, order_id, order_request.magic_number)
        
        # Simular apertura o cierre de posiciones
        if order_request.order_type in {"BUY", "SELL"}:
            # Crear una posición abierta simulada
            position = Position(
                symbol=order_request.symbol,
                volume=order_request.volume,
                entry_price=1.0,  # Precio simulado
                stop_loss=order_request.stop_loss,
                take_profit=order_request.take_profit,
                strategy_name=order_request.comment or "unknown",
                open_time=datetime.now(timezone.utc),
                magic_number=order_request.magic_number
            )
            self.open_positions.append(position)
            logger.info("Posición simulada abierta: %s %s (Magic: %s)", 
                       order_request.order_type, order_request.symbol, order_request.magic_number)
        
        elif order_request.order_type == "CLOSE":
            # Cerrar posiciones del símbolo y magic number especificados
            # Si tiene magic_number, solo cerrar las de esa estrategia (método robusto)
            if order_request.magic_number is not None:
                positions_to_close = [
                    p for p in self.open_positions 
                    if p.symbol == order_request.symbol and p.magic_number == order_request.magic_number
                ]
                if not positions_to_close:
                    logger.warning(
                        "No se encontraron posiciones abiertas para cerrar: %s (Magic: %s)",
                        order_request.symbol, order_request.magic_number
                    )
            else:
                # Fallback: cerrar todas las posiciones del símbolo
                positions_to_close = [p for p in self.open_positions if p.symbol == order_request.symbol]
                logger.debug("Cerrando todas las posiciones de %s (sin Magic Number especificado)", order_request.symbol)
            
            # Cerrar posiciones y crear registros de trades cerrados
            for pos in positions_to_close:
                self.open_positions.remove(pos)
                
                # Crear registro de trade cerrado
                trade_record = TradeRecord(
                    symbol=pos.symbol,
                    strategy_name=pos.strategy_name,
                    entry_time=pos.open_time,
                    exit_time=datetime.now(timezone.utc),
                    entry_price=pos.entry_price,
                    exit_price=1.0,  # Precio de cierre simulado
                    size=pos.volume,
                    pnl=0.0,  # PnL simulado
                    stop_loss=pos.stop_loss,
                    take_profit=pos.take_profit
                )
                self.closed_trades.append(trade_record)
                
                logger.info("Posición simulada cerrada: %s (Magic: %s, Strategy: %s)", 
                           pos.symbol, pos.magic_number, pos.strategy_name)

        return OrderResult(success=True, order_id=order_id)

    def get_open_positions(self):
        """Devuelve las posiciones abiertas simuladas."""
        return self.open_positions.copy()

    def get_closed_trades(self):
        """Devuelve los trades cerrados simulados."""
        return self.closed_trades.copy()


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

    bot.run_once(now=datetime.now(timezone.utc))
    logger.info("Órdenes enviadas en ejemplo: %d", len(broker.orders_sent))


if __name__ == "__main__":
    main()
