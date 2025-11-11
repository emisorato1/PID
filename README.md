# PID Control de Temperatura - Invernadero de Vainilla

Controlador PID simple para mantener temperatura en 28°C (±0.5°C) en un microinvernadero.

## Archivos

- `invernadero_pid.ino` - Código del controlador PID
- `TEORIA_PID.md` - Documentación teórica y análisis

## Especificaciones

- **Setpoint**: 28°C
- **Tolerancia**: ±0.5°C
- **Plataforma**: Arduino Nano/UNO
- **Parámetros PID**: KP=1.8, KI=5.4, KD=0.31

## Hardware

### Pines
- **A0**: Sensor de temperatura (ADC)
- **3**: Salida PWM (calefactor)

### Sensor de Temperatura

Ajusta `leer_temperatura()` según tu sensor:

**LM35 (10mV/°C):**
```cpp
float temp = (adc * 5.0 / 1024.0) * 100.0;
```

**TMP36 (10mV/°C, offset 0.5V):**
```cpp
float temp = ((adc * 5.0 / 1024.0) - 0.5) * 100.0;
```

## Compilación y Uso

1. Abre `invernadero_pid.ino` en Arduino IDE
2. Ajusta la función `leer_temperatura()` según tu sensor
3. Compila y carga al Arduino
4. Exporta el binario para SimulIDE

## Configuración en SimulIDE

### Conexiones
1. Pin 3 (PWM) → **Plant-Input**
2. **Plant-SlowOut** → Pin A0 (sensor)
3. Configura puerto serie virtual (COM0)

### La Planta

- **Plant-SlowOut**: τ=1.0s (respuesta lenta, usar esta)
- **Plant-FastOut**: τ=0.1s (respuesta rápida, solo pruebas)

**Recomendación**: Usa **Plant-SlowOut** para simular invernadero real.

## Configuración de SerialPlot

### Configuración Básica
1. **Puerto**: COM0 (o el de SimulIDE)
2. **Baudrate**: 9600
3. **Formato**: ASCII
4. **Delimitador**: `,` (coma)
5. **Filtro**: Prefix `>> `, Mode `Include`

### Canales (8 valores)

```
>> temperatura,setpoint,error,out_p,out_i,out_d,out_total,salida
```

- **temperatura**: Temperatura medida (°C)
- **setpoint**: 28.00°C (constante)
- **error**: Diferencia setpoint-temperatura (°C)
- **out_p**: Componente proporcional
- **out_i**: Componente integral
- **out_d**: Componente derivativo
- **out_total**: Salida PID antes de limitar
- **salida**: Salida PWM aplicada (0-255)

## Ajuste de Parámetros PID

### Parámetros Actuales
- **KP = 1.8**: Proporcional
- **KI = 5.4**: Integral
- **KD = 0.31**: Derivativo

### Cómo Ajustar

**Si la respuesta es muy lenta:**
- Aumenta KP (ej: 2.0, 2.5)
- Aumenta KI ligeramente (ej: 6.0)

**Si oscila mucho:**
- Reduce KP (ej: 1.5, 1.2)
- Reduce KI (ej: 4.0, 3.0)
- Aumenta KD (ej: 0.4, 0.5)

**Si no llega al setpoint:**
- Aumenta KI (ej: 6.0, 7.0)

**Si hay sobreimpulso:**
- Reduce KP o aumenta KD

### ⚠️ Advertencia

**NO aumentes demasiado los parámetros:**
- KP > 5 → Oscilaciones
- KI > 8 → Inestabilidad
- KD > 0.5 → Sobre-reacción

## Solución de Problemas

### La temperatura no alcanza el setpoint

1. Verifica calibración del sensor
2. Usa **Plant-SlowOut** (no FastOut)
3. Aumenta KI gradualmente
4. Verifica conexiones en SimulIDE

### Oscilaciones grandes

1. **REDUCE KP y KI** inmediatamente
2. Aumenta KD ligeramente
3. Verifica que uses Plant-SlowOut

### El término I se satura

- Normal si hay error grande persistente
- Verifica que el sensor esté bien calibrado
- Ajusta `MAX_INTEGRAL` en el código si es necesario

### Valores Conservadores (si todo falla)

```cpp
const float KP = 1.5;
const float KI = 3.0;
const float KD = 0.2;
```

## Análisis Rápido de Datos

### Qué Observar en SerialPlot

**Temperatura vs Setpoint:**
- Debe subir suavemente hacia 28°C
- Debe estabilizarse alrededor de 28°C
- No debe oscilar mucho

**Error:**
- Debe disminuir de 28°C a ~0°C
- En estabilización debe ser < 0.5°C

**Componentes PID:**
- **P**: Alto al inicio, pequeño al final
- **I**: Crece y se estabiliza (~81)
- **D**: Negativo al inicio, ~0 al final

**Salida:**
- Alta al inicio (65-101)
- Disminuye al acercarse (101→81)
- Estable al final (79-81)

### Métricas Objetivo

- **Tiempo de establecimiento**: < 30 segundos
- **Sobreimpulso**: < 1.4°C sobre setpoint
- **Error estacionario**: < 0.5°C
- **Oscilaciones**: < ±0.2°C

## Características del Código

- Filtro de promedio móvil (3 muestras)
- Anti-windup mejorado
- Zona muerta (<0.15°C)
- Derivativo sobre temperatura
- Límites: Integral ≤ 15.0, Derivativo ≤ ±50

## Notas

- Período de muestreo: 100ms (10 Hz)
- Salida PWM: 0-255
- Integral limitada: 15.0 (i_term máximo ≈ 81)
- Derivativo limitado: ±50
