from __future__ import annotations

from typing import Protocol, Iterable, Sequence

from src.domain.entities.order import Order
from src.domain.entities.position import Position


class BrokerEventHandler(Protocol):
    """Protocolo para callbacks de eventos del broker."""

    def __call__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        """Procesa un evento asincrónico del broker."""
        raise NotImplementedError()


class BrokerAdapter(Protocol):
    """Interfaz genérica hacia proveedores de ejecución."""

    def connect(self) -> None:
        """Establece la conexión con el broker remoto."""
        raise NotImplementedError()

    def disconnect(self) -> None:
        """Cierra la conexión activa con el broker."""
        raise NotImplementedError()

    def is_connected(self) -> bool:
        """Indica si la sesión con el broker está activa."""
        raise NotImplementedError()

    def get_quote(self, symbol: str) -> float:
        """Obtiene la última cotización disponible para el símbolo."""
        raise NotImplementedError()

    def get_ohlc(self, symbol: str, timeframe: str, bars: int) -> Sequence[dict[str, float]]:
        """Recupera velas históricas del símbolo en el marco temporal indicado."""
        raise NotImplementedError()

    def subscribe(self, symbols: Iterable[str]) -> None:
        """Solicita el flujo de datos en tiempo real para los símbolos."""
        raise NotImplementedError()

    def get_balance(self) -> float:
        """Obtiene el balance actual de la cuenta."""
        raise NotImplementedError()

    def get_equity(self) -> float:
        """Obtiene la equity de la cuenta."""
        raise NotImplementedError()

    def get_margin_used(self) -> float:
        """Devuelve el margen utilizado en la cuenta."""
        raise NotImplementedError()

    def get_open_positions(self) -> Sequence[Position]:
        """Recupera las posiciones abiertas."""
        raise NotImplementedError()

    def get_open_orders(self) -> Sequence[Order]:
        """Recupera las órdenes abiertas."""
        raise NotImplementedError()

    def place_order(self, order: Order) -> str:
        """Envía una orden y retorna su identificador asignado."""
        raise NotImplementedError()

    def modify_order(self, order_id: str, **params) -> None:  # type: ignore[no-untyped-def]
        """Modifica atributos de una orden existente."""
        raise NotImplementedError()

    def cancel_order(self, order_id: str) -> None:
        """Cancela la orden identificada por el parámetro."""
        raise NotImplementedError()

    def close_position(self, position_id: str, **params) -> None:  # type: ignore[no-untyped-def]
        """Cierra una posición abierta aplicando los parámetros dados."""
        raise NotImplementedError()

    def on_fill(self, callback: BrokerEventHandler) -> None:
        """Registra un callback para eventos de ejecución."""
        raise NotImplementedError()

    def on_order_update(self, callback: BrokerEventHandler) -> None:
        """Registra un callback para actualizaciones de órdenes."""
        raise NotImplementedError()

    def on_disconnect(self, callback: BrokerEventHandler) -> None:
        """Registra un callback para desconexiones inesperadas."""
        raise NotImplementedError()
