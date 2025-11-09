from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass(slots=True)
class DataStore:
    """Repositorio en memoria de información de mercado."""

    frames: dict[tuple[str, str], pd.DataFrame] = field(default_factory=dict)
    features: dict[tuple[str, str], dict[str, pd.Series]] = field(default_factory=dict)
    window_bars: int | None = None

    def update_bar(self, symbol: str, timeframe: str, bar: dict[str, Any]) -> None:
        """Incorpora una nueva barra de precios a la serie correspondiente."""
        raise NotImplementedError()

    def get_frame(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Obtiene el DataFrame asociado al símbolo y timeframe."""
        raise NotImplementedError()

    def compute_features(self, symbol: str, timeframe: str, feature_set: str) -> None:
        """Calcula indicadores derivados y los almacena en caché."""
        raise NotImplementedError()

    def snapshot(self) -> dict[tuple[str, str], pd.DataFrame]:
        """Genera una copia inmutable de los datos disponibles."""
        raise NotImplementedError()
