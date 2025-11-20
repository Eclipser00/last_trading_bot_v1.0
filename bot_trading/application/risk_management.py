"""Gestión de riesgo del bot de trading."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

from bot_trading.domain.entities import RiskLimits, TradeRecord

logger = logging.getLogger(__name__)


class RiskLimitExceeded(Exception):
    """Excepción para indicar que un límite de riesgo ha sido violado."""


@dataclass
class RiskManager:
    """Evalúa límites de riesgo globales, por símbolo y por estrategia."""

    risk_limits: RiskLimits

    def _calculate_drawdown(self, trades: Iterable[TradeRecord]) -> float:
        """Calcula un drawdown simplificado basado en pérdidas acumuladas."""
        total_loss = -sum(min(trade.pnl, 0.0) for trade in trades)
        logger.debug("Drawdown calculado: %s", total_loss)
        return total_loss

    def check_bot_risk_limits(self, trades: Iterable[TradeRecord]) -> bool:
        """Valida si el bot puede operar según el drawdown global."""
        if self.risk_limits.dd_global is None:
            return True
        drawdown = self._calculate_drawdown(trades)
        allowed = drawdown <= self.risk_limits.dd_global
        if not allowed:
            logger.warning(
                "Límite de drawdown global superado: %.2f > %.2f",
                drawdown,
                self.risk_limits.dd_global,
            )
        return allowed

    def check_symbol_risk_limits(
        self, symbol: str, trades: Iterable[TradeRecord]
    ) -> bool:
        """Valida límites de riesgo por símbolo."""
        limit = self.risk_limits.dd_por_activo.get(symbol)
        if limit is None:
            return True
        filtered = [t for t in trades if t.symbol == symbol]
        drawdown = self._calculate_drawdown(filtered)
        allowed = drawdown <= limit
        if not allowed:
            logger.warning(
                "Límite de drawdown por símbolo %s superado: %.2f > %.2f",
                symbol,
                drawdown,
                limit,
            )
        return allowed

    def check_strategy_risk_limits(
        self, strategy_name: str, trades: Iterable[TradeRecord]
    ) -> bool:
        """Valida límites de riesgo por estrategia."""
        limit = self.risk_limits.dd_por_estrategia.get(strategy_name)
        if limit is None:
            return True
        filtered = [t for t in trades if t.strategy_name == strategy_name]
        drawdown = self._calculate_drawdown(filtered)
        allowed = drawdown <= limit
        if not allowed:
            logger.warning(
                "Límite de drawdown por estrategia %s superado: %.2f > %.2f",
                strategy_name,
                drawdown,
                limit,
            )
        return allowed
