# Bot de trading orientado a objetos

Proyecto generado con enfoque TDD para un bot multi-activo/multi-estrategia que opera mediante MetaTrader 5. El objetivo es mantener una arquitectura limpia y extensible basada en protocolos para desacoplar la logica de negocio de la integracion con el broker.

## Estructura
- `bot_trading/domain`: Entidades y dataclasses de configuracion y registros.
- `bot_trading/infrastructure`: Adaptadores de datos (broker, exportadores, etc.).
- `bot_trading/application`: Gestion de riesgo, estrategias y motor de ejecucion.
- `tests`: Cobertura unitaria con pytest.

## Requisitos
- Python 3.11
- pandas
- pytest

## Ejecucion de ejemplo
```bash
python -m bot_trading.main
```

## Ejecucion en local
1. Clonar el repositorio:
   ```bash
   git clone https://github.com/Eclipser00/last_trading_bot_v1.0.git
   cd last_trading_bot_v1.0
   ```
2. Crear y activar un entorno virtual:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate      # PowerShell/cmd en Windows
   # source .venv/bin/activate   # Bash/Zsh en Linux/macOS
   ```
3. Instalar dependencias de desarrollo:
   ```bash
   pip install --upgrade pip
   pip install pandas pytest
   ```
4. Ejecutar las pruebas unitarias:
   ```bash
   pytest
   ```
5. Probar el ejemplo principal:
   ```bash
   python -m bot_trading.main
   ```

## Licencia
Este proyecto se distribuye bajo licencia **CC BY-NC 4.0** (Atribucion-No Comercial). Consulte el archivo `LICENSE` para mas detalles.
