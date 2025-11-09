from __future__ import annotations

from dataclasses import dataclass

from src.portfolio.portfolio import Portfolio


@dataclass(slots=True)
class KillSwitch:
    """Permite detener la operativa de forma segura ante eventos críticos."""

    portfolio: Portfolio
    armed_state: bool = False
    cooldown_policy: dict[str, int] | None = None

    def trigger(self, reason: str) -> None:
        """Activa el mecanismo de parada forzosa con la razón indicada."""
        raise NotImplementedError()

    def disarm(self) -> None:
        """Desactiva el kill switch tras un periodo de seguridad."""
        raise NotImplementedError()
