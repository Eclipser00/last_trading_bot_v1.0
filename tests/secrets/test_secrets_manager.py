from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Pendiente de implementación")
def test_secrets_manager_get() -> None:
    """Recupera secretos existentes desde el backend seguro."""
    raise NotImplementedError()


@pytest.mark.skip(reason="Pendiente de implementación")
def test_secrets_manager_rotate() -> None:
    """Ejecuta la rotación de secretos asegurando auditoría."""
    raise NotImplementedError()
