"""Tests del ejecutor de órdenes."""
from bot_trading.application.engine.order_executor import OrderExecutor
from bot_trading.domain.entities import OrderRequest, OrderResult


class FakeBroker:
    """Broker simulado que almacena la última orden enviada."""

    def __init__(self) -> None:
        self.last_order: OrderRequest | None = None

    def send_market_order(self, order_request: OrderRequest) -> OrderResult:
        self.last_order = order_request
        return OrderResult(success=True, order_id=1)

    def get_open_positions(self):
        return []


def test_order_executor_envia_orden_y_interpreta_respuesta() -> None:
    """El ejecutor debe enviar la orden y retornar el resultado del broker."""
    broker = FakeBroker()
    executor = OrderExecutor(broker)
    request = OrderRequest(symbol="EURUSD", volume=0.01, order_type="BUY")

    result = executor.execute_order(request)

    assert broker.last_order == request
    assert result.success is True
    assert result.order_id == 1
