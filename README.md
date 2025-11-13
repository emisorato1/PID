# Control PID de Temperatura - Invernadero

Controlador PID para mantener temperatura en 28°C (±0.5°C) en un microinvernadero.

## Estructura del Proyecto

```
arduino/
├── temperature_pid/          # Código Arduino
│   └── temperature_pid.ino   # Firmware del controlador PID
├── Analisis/                 # Análisis y visualización
│   ├── analisis.py           # Script de análisis en tiempo real
│   └── README.md             # Documentación del análisis
├── TEORIA_PID.md             # Teoría y explicación del sistema
└── README.md                 # Este archivo
```

## Especificaciones

- **Setpoint**: 28°C
- **Tolerancia**: ±0.5°C
- **Plataforma**: Arduino Nano/UNO
- **Parámetros PID**: KP=1.8, KI=5.4, KD=0.31
- **Período de muestreo**: 100ms (10 Hz)

## Hardware

- **A0**: Sensor de temperatura (ADC)
- **Pin 3**: Salida PWM (calefactor)

## Uso Rápido

### 1. Compilar y Cargar Firmware

1. Abre `temperature_pid/temperature_pid.ino` en Arduino IDE
2. Ajusta `leer_temperatura()` según tu sensor (LM35, TMP36, etc.)
3. Compila y carga al Arduino
4. Exporta el binario para SimulIDE

### 2. Configurar SimulIDE

- Pin 3 (PWM) → **Plant-Input**
- **Plant-SlowOut** → Pin A0 (sensor)
- Puerto serie virtual: COM0 (o el que corresponda)

**Importante**: Usa **Plant-SlowOut** (τ=1.0s) para simular invernadero real.

### 3. Análisis en Tiempo Real

```powershell
cd Analisis
.venv\Scripts\python.exe analisis.py
```

El script mostrará:
- Análisis de estabilidad (márgenes de ganancia/fase)
- Diagrama de Bode
- Gráfica en tiempo real: temperatura, setpoint y salida PWM

## Ajuste de Parámetros PID

| Problema | Solución |
|----------|----------|
| Respuesta muy lenta | Aumenta KP (2.0-2.5) y KI ligeramente (6.0) |
| Oscila mucho | Reduce KP (1.5) y KI (4.0), aumenta KD (0.4-0.5) |
| No llega al setpoint | Aumenta KI (6.0-7.0) |
| Sobreimpulso | Reduce KP o aumenta KD |

**⚠️ Límites recomendados**: KP < 5, KI < 8, KD < 0.5

## Documentación

- **`TEORIA_PID.md`**: Teoría del controlador PID y análisis del sistema
- **`Analisis/README.md`**: Guía completa del script de análisis
- **`Analisis/EXPLICACION_FORMULAS.md`**: Explicación detallada de las fórmulas de estabilidad

## Características del Código

- Filtro de promedio móvil (3 muestras)
- Anti-windup mejorado
- Zona muerta (<0.15°C)
- Derivativo sobre temperatura (evita "derivative kick")
- Límites: Integral ≤ 15.0, Derivativo ≤ ±50

## Formato de Datos Serial

```
>> temperatura,setpoint,error,out_p,out_i,out_d,out_total,salida
```

- **temperatura**: Temperatura medida (°C)
- **setpoint**: 28.00°C
- **error**: Diferencia setpoint-temperatura (°C)
- **out_p, out_i, out_d**: Componentes PID
- **out_total**: Salida PID antes de limitar
- **salida**: Salida PWM aplicada (0-255)

## Solución de Problemas

**Temperatura no alcanza setpoint:**
- Verifica calibración del sensor
- Usa Plant-SlowOut (no FastOut)
- Aumenta KI gradualmente

**Oscilaciones grandes:**
- Reduce KP y KI inmediatamente
- Aumenta KD ligeramente

**Valores conservadores (si todo falla):**
```cpp
KP = 1.5, KI = 3.0, KD = 0.2
```
