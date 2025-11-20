"""Tests de la capa de gestión de riesgo."""
from datetime import datetime, timedelta

from bot_trading.application.risk_management import RiskManager
from bot_trading.domain.entities import RiskLimits, TradeRecord


def _build_trade(symbol: str, strategy: str, pnl: float) -> TradeRecord:
    now = datetime.utcnow()
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
    """El bot debe bloquearse cuando el drawdown global supera el límite."""
    trades = [_build_trade("EURUSD", "strat", -120.0)]
    manager = RiskManager(RiskLimits(dd_global=100.0))

    assert manager.check_bot_risk_limits(trades) is False


def test_risk_manager_bloquea_activo_cuando_dd_por_activo_superado() -> None:
    """Un símbolo debe bloquearse si supera su drawdown permitido."""
    trades = [
        _build_trade("EURUSD", "strat", -20.0),
        _build_trade("EURUSD", "strat", -40.0),
    ]
    manager = RiskManager(RiskLimits(dd_por_activo={"EURUSD": 50.0}))

    assert manager.check_symbol_risk_limits("EURUSD", trades) is False


def test_risk_manager_bloquea_estrategia_cuando_dd_por_estrategia_superado() -> None:
    """Una estrategia debe bloquearse si supera su drawdown permitido."""
    trades = [
        _build_trade("EURUSD", "trend", -30.0),
        _build_trade("GBPUSD", "trend", -40.0),
    ]
    manager = RiskManager(RiskLimits(dd_por_estrategia={"trend": 60.0}))

    assert manager.check_strategy_risk_limits("trend", trades) is False
