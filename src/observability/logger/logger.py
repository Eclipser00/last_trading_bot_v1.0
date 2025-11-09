from __future__ import annotations

from typing import Protocol, Any


class Logger(Protocol):
    """Interfaz para registro estructurado de eventos."""

    def info(self, message: str, **context: Any) -> None:
        """Registra información relevante para operaciones normales."""
        raise NotImplementedError()

    def debug(self, message: str, **context: Any) -> None:
        """Registra detalles útiles para depuración."""
        raise NotImplementedError()

    def warning(self, message: str, **context: Any) -> None:
        """Registra situaciones inesperadas pero no críticas."""
        raise NotImplementedError()

    def error(self, message: str, **context: Any) -> None:
        """Registra errores o condiciones críticas."""
        raise NotImplementedError()
