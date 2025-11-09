from __future__ import annotations

from typing import Protocol
from datetime import datetime


class Clock(Protocol):
    """Provee utilidades de tiempo y sincronización."""

    def now(self) -> datetime:
        """Devuelve el instante temporal actual."""
        raise NotImplementedError()

    def sleep_until_next_beat(self) -> None:
        """Bloquea la ejecución hasta el siguiente pulso del scheduler."""
        raise NotImplementedError()
