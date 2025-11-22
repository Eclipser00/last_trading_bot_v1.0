"""Configuración centralizada del bot de trading.

Este módulo contiene toda la configuración del bot en un solo lugar,
facilitando el cambio entre modos de ejecución y parámetros.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class BrokerConfig:
    """Configuración del broker."""
    use_real_broker: bool = True  # True = MT5 real, False = simulado
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class LoggingConfig:
    """Configuración de logging."""
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_to_file: bool = False
    log_file_path: Optional[str] = "bot_trading.log"


@dataclass
class RiskConfig:
    """Configuración de gestión de riesgo."""
    dd_global: float = 30.0  # Drawdown máximo global (%)
    dd_por_activo: dict = None  # Drawdown por activo
    dd_por_estrategia: dict = None  # Drawdown por estrategia
    initial_balance: float = 10000.0  # Balance inicial para cálculos


@dataclass
class SymbolsConfig:
    """Configuración de símbolos a operar."""
    # Símbolos estándar en MT5 demo (pares Forex mayores)
    symbols: list = None
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = [
                {
                    "name": "EURUSD",
                    "min_timeframe": "M1",
                    "lot_size": 0.01
                },
                {
                    "name": "GBPUSD",
                    "min_timeframe": "M1",
                    "lot_size": 0.01
                },
                {
                    "name": "USDJPY",
                    "min_timeframe": "M1",
                    "lot_size": 0.01
                },
                {
                    "name": "AUDUSD",
                    "min_timeframe": "M1",
                    "lot_size": 0.01
                },
            ]


@dataclass
class StrategiesConfig:
    """Configuración de estrategias de trading."""
    strategies: list = None
    
    def __post_init__(self):
        if self.strategies is None:
            self.strategies = [
                {
                    "name": "momentum_h1",
                    "timeframes": ["H1"],
                    "allowed_symbols": ["EURUSD", "GBPUSD"]
                },
                {
                    "name": "trend_following_h4",
                    "timeframes": ["H4"],
                    "allowed_symbols": ["USDJPY", "AUDUSD"]
                },
            ]


@dataclass
class BotConfig:
    """Configuración completa del bot."""
    broker: BrokerConfig = None
    logging: LoggingConfig = None
    risk: RiskConfig = None
    symbols: SymbolsConfig = None
    strategies: StrategiesConfig = None
    
    def __post_init__(self):
        if self.broker is None:
            self.broker = BrokerConfig()
        if self.logging is None:
            self.logging = LoggingConfig()
        if self.risk is None:
            self.risk = RiskConfig()
        if self.symbols is None:
            self.symbols = SymbolsConfig()
        if self.strategies is None:
            self.strategies = StrategiesConfig()


# =============================================================================
# CONFIGURACIONES PREDEFINIDAS
# =============================================================================

# Configuración para PRODUCCIÓN (MT5 real)
PRODUCTION_CONFIG = BotConfig(
    broker=BrokerConfig(
        use_real_broker=True,
        max_retries=3,
        retry_delay=1.0
    ),
    logging=LoggingConfig(
        level="INFO",
        log_to_file=True,
        log_file_path="logs/production.log"
    ),
    risk=RiskConfig(
        dd_global=30.0,
        dd_por_activo={
            "EURUSD": 30.0,
            "GBPUSD": 30.0,
            "USDJPY": 30.0,
            "AUDUSD": 30.0,
        },
        dd_por_estrategia={
            "momentum_h1": 30.0,
            "trend_following_h4": 30.0,
        }
    )
)

# Configuración para DESARROLLO (broker simulado)
DEVELOPMENT_CONFIG = BotConfig(
    broker=BrokerConfig(
        use_real_broker=False,  # Usar FakeBroker
        max_retries=1,
        retry_delay=0.1
    ),
    logging=LoggingConfig(
        level="DEBUG",
        log_to_file=True,
        log_file_path="logs/development.log"
    ),
    risk=RiskConfig(
        dd_global=50.0,  # Más permisivo en desarrollo
        dd_por_activo={
            "EURUSD": 50.0,
            "GBPUSD": 50.0,
            "USDJPY": 50.0,
            "AUDUSD": 50.0,
        },
        dd_por_estrategia={
            "momentum_h1": 50.0,
            "trend_following_h4": 50.0,
        }
    )
)

# Configuración para TESTING (broker simulado, menos restricciones)
TESTING_CONFIG = BotConfig(
    broker=BrokerConfig(
        use_real_broker=False,
        max_retries=1,
        retry_delay=0.0
    ),
    logging=LoggingConfig(
        level="DEBUG",
        log_to_file=False
    ),
    risk=RiskConfig(
        dd_global=100.0,  # Sin restricciones para tests
        dd_por_activo={},
        dd_por_estrategia={}
    )
)


# =============================================================================
# CONFIGURACIÓN ACTIVA
# =============================================================================

# Cambiar esta variable para seleccionar el entorno
ACTIVE_CONFIG = PRODUCTION_CONFIG  # Opciones: PRODUCTION_CONFIG, DEVELOPMENT_CONFIG, TESTING_CONFIG


def get_config() -> BotConfig:
    """Retorna la configuración activa del bot.
    
    Returns:
        Configuración activa según la variable ACTIVE_CONFIG.
    """
    return ACTIVE_CONFIG

