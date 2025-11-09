from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Pendiente de implementación")
def test_broker_adapter_conexion() -> None:
    """Gestiona la conexión y desconexión del broker."""
    raise NotImplementedError()


@pytest.mark.skip(reason="Pendiente de implementación")
def test_broker_adapter_ordenes() -> None:
    """Opera el ciclo de vida completo de órdenes con callbacks."""
    raise NotImplementedError()
