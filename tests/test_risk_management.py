"""Tests de la capa de gestión de riesgo."""
from datetime import datetime, timedelta, timezone

from bot_trading.application.risk_management import RiskManager
from bot_trading.domain.entities import RiskLimits, TradeRecord


def _build_trade(symbol: str, strategy: str, pnl: float) -> TradeRecord:
    now = datetime.now(timezone.utc)
    return TradeRecord(
        symbol=symbol,
        strategy_name=strategy,
        entry_time=now - timedelta(minutes=5),
        exit_time=now,
        entry_price=1.0,
        exit_price=1.0,
        size=1.0,
        pnl=pnl,
        stop_loss=None,
        take_profit=None,
    )


def test_risk_manager_bloquea_bot_cuando_dd_global_superado() -> None:
    """El bot debe bloquearse cuando el drawdown global supera el límite.
    
    Escenario: 
    - Trade 1: +1000 (equity = 1000, max_equity = 1000, dd = 0%)
    - Trade 2: -600 (equity = 400, max_equity = 1000, dd = 60%)
    - Límite: 50%
    - Resultado esperado: BLOQUEADO
    """
    trades = [
        _build_trade("EURUSD", "strat", 1000.0),  # Ganancia inicial
        _build_trade("EURUSD", "strat", -600.0),  # Pérdida que genera 60% DD
    ]
    manager = RiskManager(RiskLimits(dd_global=50.0))

    assert manager.check_bot_risk_limits(trades) is False


def test_risk_manager_bloquea_activo_cuando_dd_por_activo_superado() -> None:
    """Un símbolo debe bloquearse si supera su drawdown permitido.
    
    Escenario:
    - Trade 1: +500 (equity = 500, max_equity = 500, dd = 0%)
    - Trade 2: -350 (equity = 150, max_equity = 500, dd = 70%)
    - Límite: 60%
    - Resultado esperado: BLOQUEADO
    """
    trades = [
        _build_trade("EURUSD", "strat", 500.0),   # Ganancia inicial
        _build_trade("EURUSD", "strat", -350.0),  # Pérdida que genera 70% DD
    ]
    manager = RiskManager(RiskLimits(dd_por_activo={"EURUSD": 60.0}))

    assert manager.check_symbol_risk_limits("EURUSD", trades) is False


def test_risk_manager_bloquea_estrategia_cuando_dd_por_estrategia_superado() -> None:
    """Una estrategia debe bloquearse si supera su drawdown permitido.
    
    Escenario:
    - Trade 1: +1000 (equity = 1000, max_equity = 1000, dd = 0%)
    - Trade 2: +200 (equity = 1200, max_equity = 1200, dd = 0%)
    - Trade 3: -900 (equity = 300, max_equity = 1200, dd = 75%)
    - Límite: 70%
    - Resultado esperado: BLOQUEADO
    """
    trades = [
        _build_trade("EURUSD", "trend", 1000.0),  # Ganancia
        _build_trade("GBPUSD", "trend", 200.0),   # Más ganancia (nuevo máximo)
        _build_trade("EURUSD", "trend", -900.0),  # Gran pérdida = 75% DD
    ]
    manager = RiskManager(RiskLimits(dd_por_estrategia={"trend": 70.0}))

    assert manager.check_strategy_risk_limits("trend", trades) is False


def test_risk_manager_permite_operar_dentro_de_limites() -> None:
    """El bot debe permitir operar si el drawdown está dentro del límite."""
    trades = [
        _build_trade("EURUSD", "strat", 1000.0),  # +1000
        _build_trade("EURUSD", "strat", -300.0),  # -300 = 30% DD
    ]
    manager = RiskManager(RiskLimits(dd_global=50.0))

    assert manager.check_bot_risk_limits(trades) is True


def test_risk_manager_drawdown_sin_trades() -> None:
    """Con lista vacía de trades, el drawdown debe ser 0 y permitir operar."""
    trades = []
    manager = RiskManager(RiskLimits(dd_global=10.0))

    assert manager.check_bot_risk_limits(trades) is True
