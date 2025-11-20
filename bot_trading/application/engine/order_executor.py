"""Ejecución de órdenes a través del broker."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from bot_trading.domain.entities import OrderRequest, OrderResult, TradeRecord
from bot_trading.infrastructure.mt5_client import BrokerClient

logger = logging.getLogger(__name__)


@dataclass
class OrderExecutor:
    """Encapsula la lógica de envío y verificación de órdenes."""

    broker_client: BrokerClient

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
        return result

    def build_trade_record(self, order_result: OrderResult) -> TradeRecord:
        """Construye un TradeRecord a partir del resultado de la orden.

        Se deja como placeholder para cuando se conecte con datos reales de entrada
        y salida de posiciones.
        """
        raise NotImplementedError(
            "Debería mapear la respuesta del broker a un TradeRecord completo."
        )
