from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.config.models import Config
from src.secrets.manager import SecretsManager
from src.broker.protocols import BrokerAdapter
from src.data.feed import DataFeed
from src.data.store import DataStore
from src.portfolio.portfolio import Portfolio
from src.risk.manager import RiskManager
from src.orders.manager import OrderManager
from src.strategy.registry import StrategyRegistry
from src.scheduling.scheduler import Scheduler
from src.scheduling.market_hours import MarketHours
from src.observability.logger.logger import Logger
from src.observability.audit.trail import AuditTrail
from src.observability.metrics.metrics import Metrics
from src.health.health_monitor import HealthMonitor
from src.health.kill_switch import KillSwitch


class AppLifecycleObserver(Protocol):
    """Protocolo para recibir eventos del ciclo de vida de la aplicación."""

    def on_boot(self) -> None:
        """Se invoca cuando la aplicación inicia la secuencia de arranque."""
        raise NotImplementedError()

    def on_run(self) -> None:
        """Se invoca al entrar en el bucle principal."""
        raise NotImplementedError()

    def on_shutdown(self) -> None:
        """Se invoca durante el proceso de apagado controlado."""
        raise NotImplementedError()


@dataclass
class App:
    """Orquestador principal del bot de trading."""

    config: Config
    secrets: SecretsManager
    broker: BrokerAdapter
    data_feed: DataFeed
    data_store: DataStore
    portfolio: Portfolio
    risk: RiskManager
    order_mgr: OrderManager
    strategy_registry: StrategyRegistry
    scheduler: Scheduler
    market_hours: MarketHours
    logger: Logger
    audit: AuditTrail
    metrics: Metrics
    health: HealthMonitor
    kill_switch: KillSwitch
    lifecycle_observer: AppLifecycleObserver | None = None

    def boot(self) -> None:
        """Prepara todos los componentes antes de operar."""
        raise NotImplementedError()

    def run(self) -> None:
        """Ejecuta el ciclo de vida principal del bot."""
        raise NotImplementedError()

    def shutdown(self) -> None:
        """Detiene la aplicación liberando recursos de forma segura."""
        raise NotImplementedError()

    def reload_config(self) -> None:
        """Recarga parámetros en caliente cuando sea soportado."""
        raise NotImplementedError()
