from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Pendiente de implementación")
def test_order_manager_signal_to_order() -> None:
    """Transforma señales aprobadas en órdenes listas para enviar."""
    raise NotImplementedError()


@pytest.mark.skip(reason="Pendiente de implementación")
def test_order_manager_on_fill() -> None:
    """Propaga fills al portafolio y gestor de riesgo."""
    raise NotImplementedError()
