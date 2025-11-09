from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class SecretsStorage(Protocol):
    """Protocolo para almacenamiento seguro de secretos."""

    def read(self, key: str) -> str:
        """Recupera un secreto identificado por la clave proporcionada."""
        raise NotImplementedError()

    def write(self, key: str, value: str) -> None:
        """Guarda un secreto bajo la clave especificada."""
        raise NotImplementedError()

    def rotate(self, key: str) -> None:
        """Realiza la rotación segura del secreto indicado."""
        raise NotImplementedError()


@dataclass(slots=True)
class SecretsManager:
    """Gestiona las credenciales y claves de acceso."""

    store_path: str
    encryption_key_ref: str
    storage_backend: SecretsStorage

    def get(self, key: str) -> str:
        """Obtiene un secreto del backend seguro."""
        raise NotImplementedError()

    def set(self, key: str, value: str) -> None:
        """Guarda o actualiza un secreto en el backend."""
        raise NotImplementedError()

    def rotate(self, key: str) -> None:
        """Ejecuta la rotación del secreto para reforzar la seguridad."""
        raise NotImplementedError()
