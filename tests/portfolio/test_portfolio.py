from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Pendiente de implementación")
def test_portfolio_update_from_broker() -> None:
    """Sincroniza el portafolio con el estado del broker."""
    raise NotImplementedError()


@pytest.mark.skip(reason="Pendiente de implementación")
def test_portfolio_apply_fill() -> None:
    """Actualiza posiciones y órdenes tras una ejecución."""
    raise NotImplementedError()
