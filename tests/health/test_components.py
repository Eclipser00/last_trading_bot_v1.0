from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Pendiente de implementación")
def test_health_monitor_watchdogs() -> None:
    """Supervisa conectividad y frescura de datos."""
    raise NotImplementedError()


@pytest.mark.skip(reason="Pendiente de implementación")
def test_kill_switch_trigger() -> None:
    """Activa el mecanismo de parada ante condiciones críticas."""
    raise NotImplementedError()
