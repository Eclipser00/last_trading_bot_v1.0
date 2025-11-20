"""Tests del cliente MetaTrader5 (mockeado)."""
import pytest

from bot_trading.infrastructure.mt5_client import MetaTrader5Client


def test_meta_trader5_client_metodos_no_implementados() -> None:
    """Debe dejar claro que aún no se implementa la integración real."""
    client = MetaTrader5Client()

    with pytest.raises(NotImplementedError):
        client.connect()
    with pytest.raises(NotImplementedError):
        client.get_ohlcv("EURUSD", "M1", None, None)  # type: ignore[arg-type]
    with pytest.raises(NotImplementedError):
        client.send_market_order(order_request=None)  # type: ignore[arg-type]
    with pytest.raises(NotImplementedError):
        client.get_open_positions()
    with pytest.raises(NotImplementedError):
        client.get_closed_trades()
