"""Test para verificar el correcto funcionamiento de Magic Numbers."""
import logging
from datetime import datetime, timezone

from bot_trading.main import FakeBroker
from bot_trading.application.engine.bot_engine import TradingBot
from bot_trading.application.engine.order_executor import OrderExecutor
from bot_trading.application.risk_management import RiskManager
from bot_trading.application.strategies.simple_example_strategy import SimpleExampleStrategy
from bot_trading.domain.entities import RiskLimits, SymbolConfig
from bot_trading.infrastructure.data_fetcher import MarketDataService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_no_duplicate_positions():
    """Verifica que no se abran múltiples posiciones con el mismo Magic Number."""
    broker = FakeBroker()
    market_data_service = MarketDataService(broker)
    risk_manager = RiskManager(RiskLimits(dd_global=1000))
    order_executor = OrderExecutor(broker)
    strategy = SimpleExampleStrategy(name="test_strategy", timeframes=["M1"])
    symbols = [SymbolConfig(name="EURUSD", min_timeframe="M1", lot_size=0.01)]

    bot = TradingBot(
        broker_client=broker,
        market_data_service=market_data_service,
        risk_manager=risk_manager,
        order_executor=order_executor,
        strategies=[strategy],
        symbols=symbols,
    )

    # Primera ejecución - debería abrir una posición
    bot.run_once(now=datetime.now(timezone.utc))
    first_orders = len(broker.orders_sent)
    first_positions = len(broker.open_positions)
    
    logger.info("Primera ejecución: %d órdenes, %d posiciones abiertas", first_orders, first_positions)
    
    # Segunda ejecución - NO debería abrir otra posición (ya existe una con el mismo Magic Number)
    bot.run_once(now=datetime.now(timezone.utc))
    second_orders = len(broker.orders_sent)
    second_positions = len(broker.open_positions)
    
    logger.info("Segunda ejecución: %d órdenes totales, %d posiciones abiertas", second_orders, second_positions)
    
    # Verificar que no se abrieron órdenes duplicadas
    assert second_orders == first_orders, f"Se abrió una orden duplicada (esperado {first_orders}, obtenido {second_orders})"
    logger.info("✓ TEST PASADO: No se abrieron órdenes duplicadas")

def test_multiple_strategies_same_symbol():
    """Verifica que múltiples estrategias puedan operar el mismo símbolo sin interferencias."""
    broker = FakeBroker()
    market_data_service = MarketDataService(broker)
    risk_manager = RiskManager(RiskLimits(dd_global=1000))
    order_executor = OrderExecutor(broker)
    
    # Dos estrategias diferentes
    strategy1 = SimpleExampleStrategy(name="strategy_1", timeframes=["M1"])
    strategy2 = SimpleExampleStrategy(name="strategy_2", timeframes=["M1"])
    symbols = [SymbolConfig(name="EURUSD", min_timeframe="M1", lot_size=0.01)]

    bot = TradingBot(
        broker_client=broker,
        market_data_service=market_data_service,
        risk_manager=risk_manager,
        order_executor=order_executor,
        strategies=[strategy1, strategy2],
        symbols=symbols,
    )

    # Ejecutar - deberían abrirse 2 posiciones (una por cada estrategia)
    bot.run_once(now=datetime.now(timezone.utc))
    
    orders = len(broker.orders_sent)
    positions = len(broker.open_positions)
    
    logger.info("Test múltiples estrategias: %d órdenes, %d posiciones", orders, positions)
    
    # Verificar que cada estrategia abrió su propia posición
    assert positions == 2, f"Se esperaban 2 posiciones, se obtuvieron {positions}"
    logger.info("✓ TEST PASADO: Cada estrategia abrió su propia posición")
    
    # Verificar que los Magic Numbers son diferentes
    magic_numbers = [p.magic_number for p in broker.open_positions]
    assert len(set(magic_numbers)) == 2, f"Magic Numbers duplicados: {magic_numbers}"
    logger.info("✓ Magic Numbers únicos: %s", magic_numbers)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("TEST 1: Prevención de posiciones duplicadas")
    logger.info("=" * 60)
    try:
        test_no_duplicate_positions()
        result1 = True
    except AssertionError as e:
        logger.error("✗ TEST 1 FALLIDO: %s", e)
        result1 = False
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Múltiples estrategias en el mismo símbolo")
    logger.info("=" * 60)
    try:
        test_multiple_strategies_same_symbol()
        result2 = True
    except AssertionError as e:
        logger.error("✗ TEST 2 FALLIDO: %s", e)
        result2 = False
    
    logger.info("\n" + "=" * 60)
    if result1 and result2:
        logger.info("✓ TODOS LOS TESTS PASARON")
    else:
        logger.error("✗ ALGUNOS TESTS FALLARON")
    logger.info("=" * 60)

