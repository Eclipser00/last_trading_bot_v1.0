"""Ejecución de órdenes a través del broker."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from bot_trading.domain.entities import OrderRequest, OrderResult, Position
from bot_trading.infrastructure.mt5_client import BrokerClient

logger = logging.getLogger(__name__)


@dataclass
class OrderExecutor:
    """Encapsula la lógica de envío y verificación de órdenes."""

    broker_client: BrokerClient
    open_positions: dict[str, Position] = None

    def __post_init__(self):
        """Inicializa el diccionario de posiciones abiertas."""
        if self.open_positions is None:
            self.open_positions = {}

    def execute_order(self, order_request: OrderRequest) -> OrderResult:
        """Envía una orden al broker y devuelve el resultado."""
        logger.info(
            "Enviando orden %s de volumen %s para %s",
            order_request.order_type,
            order_request.volume,
            order_request.symbol,
        )
        result = self.broker_client.send_market_order(order_request)
        if not result.success:
            logger.error("Orden rechazada: %s", result.error_message)
        else:
            logger.debug("Orden aceptada con id %s", result.order_id)
            # Registrar posición abierta si es BUY o SELL
            if order_request.order_type in {"BUY", "SELL"}:
                self._register_position(order_request, result)
        return result

    def _register_position(self, order_request: OrderRequest, result: OrderResult) -> None:
        """Registra una posición abierta."""
        position = Position(
            symbol=order_request.symbol,
            volume=order_request.volume,
            entry_price=0.0,  # Se actualizará con datos reales del broker
            stop_loss=order_request.stop_loss,
            take_profit=order_request.take_profit,
            strategy_name=order_request.comment or "unknown",
            open_time=datetime.now(timezone.utc)
        )
        # Usar order_id como clave
        position_key = f"{order_request.symbol}_{result.order_id}"
        self.open_positions[position_key] = position
        logger.debug("Posición registrada: %s", position_key)

    def has_open_position(self, symbol: str, strategy_name: str = None) -> bool:
        """Verifica si existe una posición abierta para el símbolo dado.
        
        Args:
            symbol: Símbolo a verificar.
            strategy_name: Opcional, filtrar por nombre de estrategia.
            
        Returns:
            True si existe al menos una posición abierta.
        """
        for pos in self.open_positions.values():
            if pos.symbol == symbol:
                if strategy_name is None or pos.strategy_name.startswith(strategy_name):
                    return True
        return False
