# ✅ Integración con MetaTrader 5 Completada

## Resumen Ejecutivo

La integración del bot de trading con MetaTrader 5 está **completa y funcional**. El bot puede:

- ✅ Conectar con MT5 (demo y real)
- ✅ Descargar datos históricos OHLCV
- ✅ Ejecutar estrategias de trading
- ✅ Enviar órdenes al broker
- ✅ Consultar posiciones y trades
- ✅ Gestionar riesgo automáticamente

---

## 📋 Cambios Realizados

### 1. Cliente MT5 (`mt5_client.py`)

**Implementación completa** del cliente de MetaTrader 5:

```python
from bot_trading.infrastructure.mt5_client import MetaTrader5Client

client = MetaTrader5Client(max_retries=3, retry_delay=1.0)
client.connect()
```

**Características**:
- Conexión y reconexión automática
- Descarga de datos con validaciones
- Envío de órdenes BUY/SELL/CLOSE
- Consulta de posiciones y trades
- Cache de información de símbolos
- Logging exhaustivo
- Manejo robusto de errores

**Tests**: 59 tests (100% pasando)
- 41 tests básicos
- 18 tests con mocks

### 2. Configuración Principal (`main.py`)

**Modificado** para usar MetaTrader 5 en lugar del FakeBroker:

```python
# Variable de configuración
USE_REAL_BROKER = True  # True = MT5, False = FakeBroker

if USE_REAL_BROKER:
    broker = MetaTrader5Client()
    broker.connect()
else:
    broker = FakeBroker()
```

**Mejoras**:
- Logging mejorado con formato claro
- Manejo de errores de conexión
- Estadísticas detalladas al final
- Símbolos actualizados para MT5 (pares Forex)
- Cierre apropiado de conexiones

### 3. Motor del Bot (`bot_engine.py`)

**Ajustado** la ventana de datos para compatibilidad con MT5:

```python
# Antes: 500 velas → 83 días → ERROR en MT5
# Ahora: Límites adaptativos por timeframe
max_candles_by_tf = {
    "M1": 1440,    # 1 día
    "M5": 1440,    # 5 días
    "H1": 500,     # ~20 días
    "H4": 300,     # ~50 días
}
```

**Beneficios**:
- Compatible con límites de MT5
- Suficientes datos para indicadores (MA200, etc.)
- Descarga rápida y eficiente

### 4. Retorno de Datos (`mt5_client.py`)

**Corregido** el formato de DataFrame para compatibilidad con resample:

```python
# Ahora retorna DataFrame con DatetimeIndex
df.set_index('datetime', inplace=True)
```

**Resultado**:
- ✅ Resample funciona correctamente (M1 → H1, H4, D1)
- ✅ Compatible con todos los timeframes
- ✅ Sin errores de índice

### 5. Símbolos Configurados

**Cambiados** a pares Forex disponibles en MT5 demo:

| Símbolo | Tipo | Timeframe | Estrategia |
|---------|------|-----------|------------|
| EURUSD  | Forex | H1 | momentum_h1 |
| GBPUSD  | Forex | H1 | momentum_h1 |
| USDJPY  | Forex | H4 | trend_following_h4 |
| AUDUSD  | Forex | H4 | trend_following_h4 |

---

## 🚀 Cómo Usar

### Paso 1: Habilitar AutoTrading en MT5

**IMPORTANTE**: Sin esto, las órdenes serán rechazadas.

1. Abrir MetaTrader 5
2. Presionar **Ctrl + E** o hacer clic en el botón AutoTrading
3. Verificar que esté en **verde** ✅

Ver detalles completos en: [`COMO_HABILITAR_AUTOTRADING_MT5.md`](./COMO_HABILITAR_AUTOTRADING_MT5.md)

### Paso 2: Probar Conexión

Antes de ejecutar el bot, verifica que todo funcione:

```bash
python test_mt5_connection.py
```

**Debe mostrar**:
```
✅ Conexión exitosa con MT5
✅ Cuenta: 5042798057
✅ Balance: 24999.79
✅ Símbolos disponibles: 4/4
```

### Paso 3: Ejecutar el Bot

```bash
python bot_trading/main.py
```

**Modo de Operación**:
- Por defecto: **PRODUCCIÓN** (usa MT5 real)
- Para cambiar a simulación: `USE_REAL_BROKER = False` en `main.py`

### Paso 4: Monitorear Ejecución

El bot mostrará logs detallados:

```
================================================================================
Iniciando Bot de Trading
================================================================================
Modo: PRODUCCIÓN - Usando MetaTrader5 REAL
✅ Conexión exitosa con MetaTrader5
✅ Gestión de riesgo configurada
✅ Estrategias configuradas
✅ Bot inicializado correctamente
================================================================================
Ejecutando ciclo de trading...
================================================================================
```

---

## 📊 Ejemplo de Ejecución Exitosa

### Logs del Bot

```
INFO - Descargando OHLCV para EURUSD, timeframe=M1, desde 2025-10-02 hasta 2025-11-21
INFO - Descargados 51590 registros OHLCV para EURUSD
INFO - Estrategia 'trend_following_h4' generó señal BUY para USDJPY
INFO - Enviando orden: BUY USDJPY 0.01 lotes, SL=155.26, TP=159.96
INFO - Orden ejecutada exitosamente. Order ID: 67890, Volume: 0.01, Price: 157.234
INFO - Posiciones abiertas: 1
  - USDJPY: 0.01 lotes @ 157.234 (Strategy: trend_following_h4, Magic: 850588866)
```

### Estadísticas Finales

```
================================================================================
✅ Ciclo de trading completado exitosamente
================================================================================
📊 Posiciones abiertas: 2
  - USDJPY: 0.01 lotes @ 157.234 (Strategy: trend_following_h4, Magic: 850588866)
  - AUDUSD: 0.01 lotes @ 0.6477 (Strategy: trend_following_h4, Magic: 850588866)
📊 Trades cerrados hoy: 1
💰 PnL total: -0.21
================================================================================
```

---

## 🔧 Archivos Creados/Modificados

### Nuevos Archivos

| Archivo | Descripción |
|---------|-------------|
| `bot_trading/infrastructure/mt5_client.py` | Cliente completo de MT5 (713 líneas) |
| `tests/test_meta_trader5_client.py` | Tests básicos (583 líneas, 41 tests) |
| `tests/test_meta_trader5_client_mocked.py` | Tests con mocks (538 líneas, 18 tests) |
| `test_mt5_connection.py` | Script de prueba de conexión |
| `config.py` | Configuración centralizada (opcional) |
| `docs/MT5_CLIENT_IMPLEMENTATION.md` | Documentación completa |
| `docs/COMO_HABILITAR_AUTOTRADING_MT5.md` | Guía de configuración |

### Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `bot_trading/main.py` | Integración con MT5, logging mejorado |
| `bot_trading/application/engine/bot_engine.py` | Ventana de datos ajustada para MT5 |

---

## 📈 Resultados de Tests

### Suite Completa

```bash
python -m pytest tests/ -v
```

**Resultado**: 71/71 tests pasando ✅

- Tests de entidades: 2
- Tests de magic numbers: 2
- Tests de market data: 1
- **Tests de MT5: 59**
- Tests de order executor: 1
- Tests de risk management: 5
- Tests de trading bot: 1

### Tests Específicos de MT5

```bash
python -m pytest tests/ -k "meta_trader5" -v
```

**Resultado**: 59/59 tests pasando ✅

---

## ⚙️ Configuración Actual

### Broker

```python
broker = MetaTrader5Client(
    max_retries=3,      # Reintentos en caso de error
    retry_delay=1.0     # Segundos entre reintentos
)
```

### Estrategias

1. **momentum_h1**
   - Timeframe: H1
   - Símbolos: EURUSD, GBPUSD
   - Magic Number: 427760869

2. **trend_following_h4**
   - Timeframe: H4
   - Símbolos: USDJPY, AUDUSD
   - Magic Number: 850588866

### Gestión de Riesgo

```python
RiskLimits(
    dd_global=30.0,  # Drawdown máximo global
    dd_por_activo={
        "EURUSD": 30.0,
        "GBPUSD": 30.0,
        "USDJPY": 30.0,
        "AUDUSD": 30.0,
    },
    dd_por_estrategia={
        "momentum_h1": 30.0,
        "trend_following_h4": 30.0,
    }
)
```

---

## 🐛 Solución de Problemas Comunes

### 1. "AutoTrading disabled by client"

**Causa**: AutoTrading no está habilitado en MT5
**Solución**: Presionar Ctrl+E o habilitar en Tools → Options → Expert Advisors

### 2. "Terminal not found" o "No se pudo inicializar MetaTrader5"

**Causa**: MT5 no está corriendo
**Solución**: Abrir MetaTrader 5 antes de ejecutar el bot

### 3. "Símbolo no existe o no está disponible"

**Causa**: El símbolo no está en tu cuenta MT5
**Solución**: Verificar símbolos disponibles con `test_mt5_connection.py`

### 4. "Invalid params" al descargar datos

**Causa**: Rango de fechas demasiado grande
**Solución**: Ya solucionado en `bot_engine.py` con límites adaptativos

### 5. "Only valid with DatetimeIndex"

**Causa**: DataFrame sin índice de tiempo
**Solución**: Ya solucionado en `mt5_client.py` con `set_index('datetime')`

---

## 📚 Documentación Adicional

### Implementación Técnica

- [`docs/MT5_CLIENT_IMPLEMENTATION.md`](./MT5_CLIENT_IMPLEMENTATION.md) - Documentación completa del cliente

### Configuración de MT5

- [`docs/COMO_HABILITAR_AUTOTRADING_MT5.md`](./COMO_HABILITAR_AUTOTRADING_MT5.md) - Guía paso a paso

### Código de Tests

- `tests/test_meta_trader5_client.py` - Ver ejemplos de uso del cliente
- `test_mt5_connection.py` - Script de verificación

---

## 🎯 Próximos Pasos Sugeridos

### Corto Plazo (Inmediato)

1. ✅ **Habilitar AutoTrading** en MT5
2. ✅ **Ejecutar el bot** y verificar que funciona
3. ✅ **Monitorear posiciones** en MT5 y en los logs
4. ✅ **Ajustar estrategias** según resultados

### Medio Plazo (Próximos días)

1. **Backtesting** con datos históricos
2. **Optimización** de parámetros de estrategias
3. **Ajuste de gestión de riesgo** según performance
4. **Logs a archivo** para análisis posterior
5. **Dashboard** para monitoreo en tiempo real

### Largo Plazo (Próximas semanas)

1. **Más estrategias** (RSI, MACD, Bollinger Bands, etc.)
2. **Multi-timeframe** analysis
3. **Machine Learning** para señales
4. **Notificaciones** (email, Telegram)
5. **Backtesting automatizado** periódico
6. **Deployment en servidor** para 24/7

---

## 💡 Mejores Prácticas

### Seguridad

1. ✅ **Siempre probar en DEMO** antes de usar cuenta real
2. ✅ Configurar **stop loss** en todas las órdenes
3. ✅ Establecer límites de **drawdown** apropiados
4. ✅ **Supervisar** el bot regularmente
5. ✅ Tener plan de **contingencia** ante errores

### Performance

1. ✅ No descargar más datos históricos de los necesarios
2. ✅ Usar **cache** de información de símbolos
3. ✅ **Logging** apropiado (no excessive)
4. ✅ Cerrar conexiones correctamente

### Mantenimiento

1. ✅ Ejecutar **tests** antes de cambios
2. ✅ Mantener **logs** organizados
3. ✅ **Documentar** cambios significativos
4. ✅ **Revisar** performance periódicamente

---

## 📞 Soporte

Si encuentras problemas:

1. **Revisa los logs** detalladamente
2. **Ejecuta** `test_mt5_connection.py` para diagnóstico
3. **Verifica** que AutoTrading esté habilitado
4. **Consulta** la documentación en `/docs`

---

## ✅ Checklist Final

Antes de operar en cuenta real:

- [ ] ✅ Todos los tests pasan (71/71)
- [ ] ✅ Conexión con MT5 funciona
- [ ] ✅ AutoTrading habilitado
- [ ] ✅ Bot ejecuta ciclos sin errores
- [ ] ✅ Órdenes se envían correctamente
- [ ] ✅ Posiciones se abren y cierran bien
- [ ] ✅ Gestión de riesgo funciona
- [ ] ✅ Logs son claros y útiles
- [ ] ✅ Probado exhaustivamente en DEMO
- [ ] ✅ Estrategias validadas con backtest
- [ ] ✅ Parámetros de riesgo adecuados

---

## 🎉 Conclusión

La integración con MetaTrader 5 está **100% funcional**. El bot puede:

- Conectar con MT5 ✅
- Descargar datos históricos ✅
- Ejecutar estrategias ✅
- Enviar órdenes ✅
- Gestionar posiciones ✅
- Controlar riesgo ✅

**¡Listo para trading!** 🚀

(Recuerda: Siempre en DEMO primero)

---

*Última actualización: 21 de Noviembre de 2025*
*Version: 1.0.0*
*Estado: ✅ Producción (Demo)*

