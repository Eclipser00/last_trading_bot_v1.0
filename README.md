# Bot de trading orientado a objetos

Proyecto generado con enfoque TDD para un bot multi-activo/multi-estrategia que
opera mediante MetaTrader 5. El objetivo es mantener una arquitectura limpia y
extensible basada en protocolos para desacoplar la lógica de negocio de la
integración con el broker.

## Estructura
- `bot_trading/domain`: Entidades y dataclasses de configuración y registros.
- `bot_trading/infrastructure`: Adaptadores de datos (broker, exportadores, etc.).
- `bot_trading/application`: Gestión de riesgo, estrategias y motor de ejecución.
- `tests`: Cobertura unitaria con pytest.

## Requisitos
- Python 3.11
- pandas
- pytest

## Ejecución de ejemplo
```bash
python -m bot_trading.main
```

## Licencia
Este proyecto se distribuye bajo licencia **CC BY-NC 4.0** (Atribución-No
Comercial). Consulte el archivo `LICENSE` para más detalles.
