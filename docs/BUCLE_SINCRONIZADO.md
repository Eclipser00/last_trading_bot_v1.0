# Bucle Sincronizado con Cierre de Velas

## Descripción

El bot ahora incluye un método `run_synchronized()` que ejecuta el bot en bucle infinito, sincronizado con el cierre de velas del timeframe especificado.

## Características

- ✅ **Sincronización precisa**: Espera hasta el cierre exacto de la vela
- ✅ **Delay configurable**: Espera N segundos después del cierre antes de ejecutar
- ✅ **Múltiples timeframes**: Soporta M1, M5, M15, M30, H1, H4, etc.
- ✅ **Manejo de errores**: Reintenta automáticamente si hay errores
- ✅ **Interrupción segura**: Ctrl+C detiene el bot limpiamente

## Uso

### Configuración Actual (main.py)

```python
# Ejecutar bot sincronizado con velas M1
# Espera 5 segundos después del cierre de cada vela
bot.run_synchronized(timeframe_minutes=1, wait_after_close=5)
```

### Parámetros

- **`timeframe_minutes`**: Duración de la vela en minutos
  - `1` = M1 (1 minuto)
  - `5` = M5 (5 minutos)
  - `15` = M15 (15 minutos)
  - `30` = M30 (30 minutos)
  - `60` = H1 (1 hora)
  - `240` = H4 (4 horas)

- **`wait_after_close`**: Segundos a esperar después del cierre de la vela
  - Recomendado: `5` segundos para asegurar que MT5 haya procesado la vela
  - Mínimo: `1` segundo
  - Máximo: `59` segundos (para M1)

## Ejemplo de Funcionamiento

### Para M1 (1 minuto)

```
Hora actual: 17:21:30
Próxima vela cierra: 17:22:00
Espera hasta: 17:22:05 (cierre + 5 seg)
Ejecuta ciclo...
Espera hasta: 17:23:05 (siguiente vela + 5 seg)
Ejecuta ciclo...
```

### Para M5 (5 minutos)

```
Hora actual: 17:23:10
Próxima vela cierra: 17:25:00
Espera hasta: 17:25:05 (cierre + 5 seg)
Ejecuta ciclo...
Espera hasta: 17:30:05 (siguiente vela + 5 seg)
Ejecuta ciclo...
```

## Ventajas para Múltiples Timeframes

Cuando operas con múltiples timeframes (ej: M1 y M5), el bucle sincronizado:

1. **Descarga datos una vez** al cierre de la vela base (M1)
2. **Resamplea** a los timeframes necesarios (M1, M5, etc.)
3. **Evalúa todas las estrategias** con los datos actualizados
4. **Espera** hasta el próximo cierre de vela

Esto es más eficiente que ejecutar cada estrategia por separado.

## Logs Generados

El bot mostrará logs como:

```
================================================================================
Iniciando bucle sincronizado con velas de 1 minutos
Esperando 5 segundos después del cierre de cada vela
Presiona Ctrl+C para detener el bot
================================================================================
Esperando 35.2 segundos hasta 17:22:05 (cierre de vela + 5 seg)
--------------------------------------------------------------------------------
Ejecutando ciclo de trading en 2025-11-21 17:22:05
--------------------------------------------------------------------------------
```

## Detener el Bot

Para detener el bot de forma segura:

1. Presiona **Ctrl+C**
2. El bot mostrará: `⚠️ Bucle interrumpido por el usuario`
3. Mostrará estadísticas finales
4. Cerrará la conexión con MT5 correctamente

## Comparación con `run_forever()`

| Característica | `run_forever()` | `run_synchronized()` |
|----------------|-----------------|----------------------|
| Sincronización | ❌ No | ✅ Sí |
| Precisión | ⚠️ Aproximada | ✅ Exacta |
| Múltiples TFs | ⚠️ Menos eficiente | ✅ Eficiente |
| Delay configurable | ❌ No | ✅ Sí |

## Recomendaciones

### Para Trading en Tiempo Real

- **Timeframe base**: M1 (1 minuto)
- **Delay**: 5 segundos
- **Uso**: Ideal para scalping y trading intradía

```python
bot.run_synchronized(timeframe_minutes=1, wait_after_close=5)
```

### Para Trading Swing

- **Timeframe base**: H1 o H4
- **Delay**: 10-30 segundos
- **Uso**: Estrategias de mayor plazo

```python
bot.run_synchronized(timeframe_minutes=60, wait_after_close=10)
```

### Para Backtesting/Desarrollo

- Usar `run_once()` para ejecutar un solo ciclo
- Útil para pruebas rápidas sin esperar

## Troubleshooting

### El bot no espera correctamente

Verifica que:
- El sistema tenga la hora correcta (sincronizado con NTP)
- No haya problemas de red que afecten el tiempo

### El bot ejecuta demasiado rápido

Aumenta `wait_after_close`:
```python
bot.run_synchronized(timeframe_minutes=1, wait_after_close=10)
```

### El bot ejecuta demasiado lento

Disminuye `wait_after_close` (mínimo 1 segundo):
```python
bot.run_synchronized(timeframe_minutes=1, wait_after_close=1)
```

## Notas Técnicas

- El cálculo del próximo cierre de vela usa `datetime.now(timezone.utc)` para precisión
- El bot maneja automáticamente cambios de hora (DST)
- Si hay un error, espera 10 segundos antes de reintentar
- Las estadísticas se muestran solo al finalizar (Ctrl+C)


