"""Gestión de riesgo del bot de trading."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from bot_trading.domain.entities import RiskLimits, TradeRecord

logger = logging.getLogger(__name__)


class RiskLimitExceeded(Exception):
    """Excepción para indicar que un límite de riesgo ha sido violado."""


@dataclass
class RiskManager:
    """Evalúa límites de riesgo globales, por símbolo y por estrategia."""

    risk_limits: RiskLimits

    def _calculate_drawdown(self, trades: list[TradeRecord]) -> float:
        """Calcula el drawdown real como porcentaje desde el máximo histórico.
        
        Usa el balance inicial configurado para calcular correctamente el drawdown
        incluso cuando la estrategia comienza con pérdidas.
        
        Args:
            trades: Lista de trades cerrados ordenados cronológicamente.
            
        Returns:
            Drawdown actual en porcentaje (0-100).
        """
        if not trades:
            return 0.0
        
        # Usar balance inicial de la configuración
        initial_balance = self.risk_limits.initial_balance
        equity = initial_balance
        max_equity = initial_balance
        max_drawdown = 0.0
        
        for trade in trades:
            equity += trade.pnl
            if equity > max_equity:
                max_equity = equity
            
            # Calcular drawdown actual (max_equity siempre > 0 con balance inicial)
            current_dd = ((max_equity - equity) / max_equity) * 100
            if current_dd > max_drawdown:
                max_drawdown = current_dd
        
        logger.debug("Drawdown calculado: %.2f%% (Equity: %.2f, Max: %.2f)", 
                     max_drawdown, equity, max_equity)
        return max_drawdown

    def check_bot_risk_limits(self, trades: list[TradeRecord]) -> bool:
        """Valida si el bot puede operar según el drawdown global."""
        if self.risk_limits.dd_global is None:
            return True
        drawdown = self._calculate_drawdown(trades)
        allowed = drawdown <= self.risk_limits.dd_global
        if not allowed:
            logger.warning(
                "Límite de drawdown global superado: %.2f%% > %.2f%%",
                drawdown,
                self.risk_limits.dd_global,
            )
        return allowed

    def check_symbol_risk_limits(
        self, symbol: str, trades: list[TradeRecord]
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
                "Límite de drawdown por símbolo %s superado: %.2f%% > %.2f%%",
                symbol,
                drawdown,
                limit,
            )
        return allowed

    def check_strategy_risk_limits(
        self, strategy_name: str, trades: list[TradeRecord]
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
                "Límite de drawdown por estrategia %s superado: %.2f%% > %.2f%%",
                strategy_name,
                drawdown,
                limit,
            )
        return allowed
