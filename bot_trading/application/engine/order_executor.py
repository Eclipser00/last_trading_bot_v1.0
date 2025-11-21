"""Ejecución de órdenes a través del broker."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from bot_trading.domain.entities import OrderRequest, OrderResult, Position
from bot_trading.infrastructure.mt5_client import BrokerClient

logger = logging.getLogger(__name__)


@dataclass
class OrderExecutor:
    """Encapsula la lógica de envío y verificación de órdenes."""

    broker_client: BrokerClient
    open_positions: dict[str, Position] = field(default_factory=dict)

    def _generate_position_key(self, symbol: str, magic_number: int | None) -> str:
        """Genera una clave única para identificar posiciones.
        
        Args:
            symbol: Símbolo de la posición.
            magic_number: Magic Number de la estrategia.
            
        Returns:
            Clave única basada en símbolo y magic_number.
        """
        if magic_number is not None:
            return f"{symbol}_{magic_number}"
        return symbol

    def sync_state(self) -> None:
        """Sincroniza el estado interno con las posiciones reales del broker."""
        try:
            real_positions = self.broker_client.get_open_positions()
            # Reconstruimos el mapa local usando símbolo + magic_number como clave
            # Esto permite múltiples posiciones del mismo símbolo con diferentes estrategias
            self.open_positions.clear()
            for pos in real_positions:
                position_key = self._generate_position_key(pos.symbol, pos.magic_number)
                self.open_positions[position_key] = pos
            logger.debug("Estado sincronizado con broker. %d posiciones abiertas.", len(self.open_positions))
        except Exception as e:
            logger.error("Error sincronizando posiciones con broker: %s", e)

    def execute_order(self, order_request: OrderRequest) -> OrderResult:
        """Envía una orden al broker y devuelve el resultado."""
        logger.info(
            "Enviando orden %s de volumen %s para %s (Magic: %s)",
            order_request.order_type,
            order_request.volume,
            order_request.symbol,
            order_request.magic_number,
        )
        result = self.broker_client.send_market_order(order_request)
        if not result.success:
            logger.error("Orden rechazada: %s", result.error_message)
        else:
            logger.debug("Orden aceptada con id %s", result.order_id)
            
            if order_request.order_type in {"BUY", "SELL"}:
                self._register_position(order_request, result)
            elif order_request.order_type == "CLOSE":
                self._remove_position(order_request.symbol, order_request.magic_number)
                
        return result

    def _remove_position(self, symbol: str, magic_number: int | None = None) -> None:
        """Elimina posiciones internas asociadas a un símbolo y opcionalmente a una estrategia.
        
        Args:
            symbol: Símbolo de la posición a eliminar.
            magic_number: Si se proporciona, solo elimina posiciones con este Magic Number.
                         Si es None, elimina todas las posiciones del símbolo.
        """
        if magic_number is not None:
            # Eliminar posición específica de la estrategia
            position_key = self._generate_position_key(symbol, magic_number)
            if position_key in self.open_positions:
                del self.open_positions[position_key]
                logger.debug("Posición eliminada: %s con Magic Number: %s", symbol, magic_number)
            else:
                logger.warning("No se encontró posición para eliminar: %s (Magic: %s)", symbol, magic_number)
        else:
            # Fallback: eliminar todas las posiciones del símbolo
            keys_to_remove = [k for k, v in self.open_positions.items() if v.symbol == symbol]
            for k in keys_to_remove:
                del self.open_positions[k]
            logger.debug("Posiciones eliminadas del registro local para %s", symbol)

    def _register_position(self, order_request: OrderRequest, result: OrderResult) -> None:
        """Registra una posición abierta.
        
        Args:
            order_request: Solicitud de orden que generó la posición.
            result: Resultado de la orden ejecutada.
        """
        position = Position(
            symbol=order_request.symbol,
            volume=order_request.volume,
            entry_price=0.0,  # Se actualizará con datos reales del broker
            stop_loss=order_request.stop_loss,
            take_profit=order_request.take_profit,
            strategy_name=order_request.comment or "unknown",
            open_time=datetime.now(timezone.utc),
            magic_number=order_request.magic_number
        )
        # Usar símbolo + magic_number como clave para consistencia
        position_key = self._generate_position_key(order_request.symbol, order_request.magic_number)
        self.open_positions[position_key] = position
        logger.debug("Posición registrada: %s con Magic Number: %s", position_key, order_request.magic_number)

    def has_open_position(
        self, 
        symbol: str, 
        strategy_name: str = None,
        magic_number: int = None
    ) -> bool:
        """Verifica si existe una posición abierta para el símbolo dado.
        
        Args:
            symbol: Símbolo a verificar.
            strategy_name: Opcional, filtrar por nombre de estrategia (fallback legacy).
            magic_number: Opcional, filtrar por Magic Number (método preferido y robusto).
            
        Returns:
            True si existe al menos una posición abierta que coincida con los criterios.
        """
        # Método preferido: búsqueda directa usando clave
        if magic_number is not None:
            position_key = self._generate_position_key(symbol, magic_number)
            return position_key in self.open_positions
        
        # Fallback: búsqueda iterativa (menos eficiente, para compatibilidad)
        for pos in self.open_positions.values():
            if pos.symbol == symbol:
                if strategy_name is None or pos.strategy_name.startswith(strategy_name):
                    return True
        return False
