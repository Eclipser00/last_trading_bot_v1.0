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
from bot_trading.infrastructure.mt5_client import MetaTrader5Client, MT5ConnectionError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURACIÓN: Cambiar a False para usar el broker simulado
# =============================================================================
USE_REAL_BROKER = True  # True = MetaTrader5, False = FakeBroker


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
    """Ejecuta el bot de trading.

    Puede usar MetaTrader5 real o un broker simulado según la configuración.
    """
    logger.info("="*80)
    logger.info("Iniciando Bot de Trading")
    logger.info("="*80)
    
    # Seleccionar broker según configuración
    if USE_REAL_BROKER:
        logger.info("Modo: PRODUCCIÓN - Usando MetaTrader5 REAL")
        logger.info("IMPORTANTE: Las órdenes se ejecutarán en la cuenta demo de MT5")
        
        try:
            # Crear cliente de MetaTrader5
            broker = MetaTrader5Client(max_retries=3, retry_delay=1.0)
            
            # Conectar con MT5
            logger.info("Conectando con MetaTrader5...")
            broker.connect()
            logger.info(" Conexión exitosa con MetaTrader5")
            
        except MT5ConnectionError as e:
            logger.error(" Error al conectar con MetaTrader5: %s", e)
            logger.error("Verifica que:")
            logger.error("  1. MetaTrader5 esté instalado y corriendo")
            logger.error("  2. Estés logueado en tu cuenta demo")
            logger.error("  3. El terminal no esté bloqueado")
            sys.exit(1)
        except Exception as e:
            logger.error(" Error inesperado: %s", e)
            sys.exit(1)
    else:
        logger.info("Modo: SIMULACIÓN - Usando FakeBroker")
        logger.info("Las órdenes NO se ejecutarán en broker real")
        broker = FakeBroker()
        broker.connect()
    
    logger.info("-"*80)
    
    # Crear servicio de datos de mercado
    market_data_service = MarketDataService(broker)
    ############################################################################
    #
    #               RIESGO GLOBAL Y POR ACTIVO
    #
    ############################################################################
    logger.info("Configurando gestión de riesgo...")
    risk_manager = RiskManager(
        RiskLimits(
            dd_global=30.0,  # Drawdown máximo global del bot (30%)
            dd_por_activo={
                "EURUSD": 30.0,
                "GBPUSD": 30.0,
                "USDJPY": 30.0,
            },  # Drawdown máximo por activo (30%)
            dd_por_estrategia={
                "momentum_M1": 30.0,  # Límite para estrategia momentum
                "trend_following_M5": 30.0,  # Límite para estrategia trend
            }
        )
    )
    logger.info(" Gestión de riesgo configurada")
    
    order_executor = OrderExecutor(broker)
    logger.info(" Ejecutor de órdenes configurado")

    # TIMEFRAME_MAP: "M1": "1min", "M5": "5min", "M15": "15min", "H1": "1H", "H4": "4H", "D1": "1D"

    ############################################################################
    #
    #            ESTRATEGIAS CON SÍMBOLOS ESPECÍFICOS
    #
    ############################################################################
    logger.info("Configurando estrategias de trading...")
    
    # Estrategia Momentum: opera pares EUR y GBP
    strategy_momentum = SimpleExampleStrategy(
        name="momentum_M1",
        timeframes=["M1"],
        allowed_symbols=["EURUSD", "GBPUSD"]  # Pares mayores Forex
    )
    logger.info("  - Estrategia 'momentum_M1' creada (EURUSD, GBPUSD)")
    
    # Estrategia Trend: opera pares USD y AUD
    strategy_trend = SimpleExampleStrategy(
        name="trend_following_M5",
        timeframes=["M5"],
        allowed_symbols=["USDJPY"]  # Pares mayores Forex
    )
    logger.info("  - Estrategia 'trend_following_M1' creada (USDJPY)")
    logger.info(" Estrategias configuradas")

    ############################################################################
    #
    #             ACTIVOS, TIMEFRAME MINIMO Y LOT SIZE
    #
    ############################################################################
    # Timeframe minimo para empezar a resamplear los datos
    # Incluir todos los símbolos que las estrategias necesitan
    # NOTA: En MT5 demo, estos símbolos son estándar y deberían estar disponibles
    logger.info("Configurando símbolos a operar...")
    symbols = [
        SymbolConfig(name="EURUSD", min_timeframe="M1", lot_size=0.01),
        SymbolConfig(name="GBPUSD", min_timeframe="M1", lot_size=0.01),
        SymbolConfig(name="USDJPY", min_timeframe="M5", lot_size=0.01),
    ]
    logger.info("  - EURUSD: Timeframe mínimo M1, Lot size 0.01")
    logger.info("  - GBPUSD: Timeframe mínimo M1, Lot size 0.01")
    logger.info("  - USDJPY: Timeframe mínimo M5, Lot size 0.01")
    logger.info(" Símbolos configurados")

    ############################################################################
    #
    #                      INICIALIZACIÓN DEL BOT
    #
    ############################################################################
    logger.info("-"*80)
    logger.info("Inicializando bot de trading...")
    
    bot = TradingBot(
        broker_client=broker,
        market_data_service=market_data_service,
        risk_manager=risk_manager,
        order_executor=order_executor,
        ######################################################################
        #           ESTRATEGIAS A EJECUTAR
        ######################################################################
        strategies=[
            strategy_momentum, 
            strategy_trend
        ],
        symbols=symbols,
    )
    logger.info("✅ Bot inicializado correctamente")
    
    ############################################################################
    #
    #                      EJECUCIÓN DEL BOT
    #
    ############################################################################
    logger.info("="*80)
    logger.info("Modo de ejecución: BUCLE SINCRONIZADO")
    logger.info("="*80)
    logger.info("El bot ejecutará un ciclo cada vez que cierre una vela M1")
    logger.info("Esperará 5 segundos después del cierre antes de ejecutar")
    logger.info("Presiona Ctrl+C para detener el bot")
    logger.info("="*80)
    
    try:
        # Ejecutar bot en bucle sincronizado con cierre de velas M1
        # timeframe_minutes=1: Sincroniza con velas de 1 minuto (M1)
        # wait_after_close=5: Espera 5 segundos después del cierre de la vela
        bot.run_synchronized(timeframe_minutes=1, wait_after_close=5)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Ejecución interrumpida por el usuario")
    except Exception as e:
        logger.error("❌ Error durante la ejecución del bot: %s", e, exc_info=True)
        raise
    finally:
        # Mostrar estadísticas finales al cerrar
        logger.info("="*80)
        logger.info("ESTADÍSTICAS FINALES")
        logger.info("="*80)
        
        if USE_REAL_BROKER:
            # Obtener posiciones abiertas reales
            try:
                positions = broker.get_open_positions()
                logger.info("📊 Posiciones abiertas: %d", len(positions))
                for pos in positions:
                    logger.info("  - %s: %.2f lotes @ %.5f (Strategy: %s, Magic: %s)",
                               pos.symbol, pos.volume, pos.entry_price,
                               pos.strategy_name, pos.magic_number)
                
                # Obtener trades cerrados
                trades = broker.get_closed_trades()
                logger.info("📊 Trades cerrados hoy: %d", len(trades))
                if trades:
                    total_pnl = sum(t.pnl for t in trades)
                    logger.info("💰 PnL total: %.2f", total_pnl)
                    # Mostrar últimos 5 trades
                    logger.info("Últimos trades:")
                    for trade in trades[:5]:
                        logger.info("  - %s: %.2f lotes, PnL=%.2f, Entrada=%.5f, Salida=%.5f",
                                   trade.symbol, trade.size, trade.pnl,
                                   trade.entry_price, trade.exit_price)
                
            except Exception as e:
                logger.error("Error al obtener estadísticas: %s", e)
        else:
            # Estadísticas del broker simulado
            logger.info("📊 Órdenes simuladas enviadas: %d", len(broker.orders_sent))
            logger.info("📊 Posiciones simuladas abiertas: %d", len(broker.open_positions))
            logger.info("📊 Trades simulados cerrados: %d", len(broker.closed_trades))
        
        # Cerrar conexión con MT5 si es necesario
        if USE_REAL_BROKER:
            logger.info("Cerrando conexión con MetaTrader5...")
            # El destructor del cliente se encarga del cierre
            logger.info("✅ Conexión cerrada")
        
        logger.info("="*80)
        logger.info("Bot finalizado")
        logger.info("="*80)


if __name__ == "__main__":
    main()
