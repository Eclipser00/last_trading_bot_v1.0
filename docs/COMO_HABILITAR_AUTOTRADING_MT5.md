# Cómo Habilitar AutoTrading en MetaTrader 5

## Problema

Cuando el bot intenta enviar órdenes, MT5 las rechaza con el mensaje:

```
AutoTrading disabled by client (código 10027)
```

Esto significa que MT5 tiene desactivada la capacidad de ejecutar órdenes automáticas desde programas externos.

## Solución

Para permitir que el bot ejecute órdenes, debes **habilitar el AutoTrading** en MT5:

### Paso 1: Abrir MT5

Asegúrate de que MetaTrader 5 esté corriendo y logueado en tu cuenta demo.

### Paso 2: Habilitar AutoTrading

Hay **3 maneras** de habilitar el AutoTrading:

#### Opción 1: Botón en la Barra de Herramientas
1. Busca el botón **"AutoTrading"** en la barra de herramientas superior
2. Es un botón con el icono de un semáforo o señal de tráfico
3. Haz clic para que se ponga en **VERDE** ✅
4. Cuando está verde, el AutoTrading está habilitado

#### Opción 2: Menú Tools
1. Ve al menú **Tools** (Herramientas)
2. Selecciona **Options** (Opciones)
3. Ve a la pestaña **Expert Advisors** (Asesores Expertos)
4. Marca la casilla **"Allow algorithmic trading"** (Permitir trading algorítmico)
5. Haz clic en **OK**

#### Opción 3: Tecla Rápida
1. Presiona **Ctrl + E** (atajo de teclado)
2. Esto activa/desactiva el AutoTrading rápidamente

### Paso 3: Verificar Configuración

Para asegurarte de que está correctamente configurado:

1. Ve a **Tools → Options → Expert Advisors**
2. Verifica que estén marcadas estas opciones:
   - ✅ **Allow algorithmic trading**
   - ✅ **Allow DLL imports** (opcional, no necesario para este bot)
   - ✅ **Disable algorithmic trading when account is changed** (recomendado por seguridad)

### Paso 4: Ejecutar el Bot

Ahora puedes ejecutar el bot y debería poder enviar órdenes:

```bash
python bot_trading/main.py
```

## Verificación

Si todo está configurado correctamente, verás mensajes como:

```
Orden ejecutada exitosamente. Order ID: 12345, Volume: 0.10, Price: 1.10000
```

En lugar de:

```
Orden rechazada: AutoTrading disabled by client
```

## Notas Importantes

### Seguridad

⚠️ **IMPORTANTE**: El AutoTrading permite que programas externos ejecuten órdenes en tu cuenta.

**Recomendaciones de seguridad**:
1. **Usa SIEMPRE una cuenta DEMO** para probar
2. Nunca habilites AutoTrading en una cuenta real sin haber probado exhaustivamente el bot
3. Mantén el bot bajo supervisión cuando esté corriendo
4. Establece límites de riesgo apropiados en la configuración

### Permisos de MT5

En la configuración de **Expert Advisors**, puedes configurar:

- **Maximum number of positions** (Número máximo de posiciones): Limita cuántas posiciones puede abrir el bot
- **Maximum risk per trade** (Riesgo máximo por trade): Limita el tamaño de las órdenes
- **Allowed actions**: Qué acciones puede realizar (trading, modificación de órdenes, etc.)

### Estado del Botón AutoTrading

El botón de AutoTrading en la barra de herramientas tiene 3 estados:

| Color | Estado | Significado |
|-------|--------|-------------|
| 🟢 Verde | Activo | AutoTrading habilitado, el bot puede operar |
| 🔴 Rojo | Deshabilitado | AutoTrading desactivado, órdenes serán rechazadas |
| ⚪ Gris | No disponible | No hay EAs corriendo o terminal no está conectado |

## Solución de Problemas

### "AutoTrading disabled by server"

Si ves este mensaje en lugar de "disabled by client", significa que el **servidor (broker)** no permite AutoTrading:

- Algunas cuentas demo tienen restricciones
- Verifica con tu broker si permiten trading algorítmico
- Considera abrir una cuenta demo diferente que lo permita

### "Trade is disabled"

Significa que el símbolo específico no permite trading:

- Puede estar fuera del horario de mercado
- El símbolo puede estar deshabilitado temporalmente
- Verifica el estado del símbolo en el **Market Watch**

### El botón AutoTrading se desactiva solo

Revisa la configuración:

1. **Tools → Options → Expert Advisors**
2. Desmarca **"Disable algorithmic trading when account is changed"**
3. Esto evita que se desactive al cambiar de cuenta

## Probar la Configuración

Usa el script de prueba para verificar que todo funciona:

```bash
python test_mt5_connection.py
```

Este script verifica la conexión pero NO intenta enviar órdenes.

Para probar con órdenes reales (en DEMO):

```bash
python bot_trading/main.py
```

El bot intentará ejecutar las estrategias configuradas y verás si las órdenes se aceptan o rechazan.

## Resumen

1. Habilitar AutoTrading en MT5 (botón verde o Ctrl+E)
2. Configurar Options → Expert Advisors → "Allow algorithmic trading"
3. Verificar que el botón esté VERDE
4. Ejecutar el bot
5. Supervisar que las órdenes se ejecuten correctamente

---

**¿Necesitas ayuda?** Revisa los logs del bot para ver mensajes de error específicos.

