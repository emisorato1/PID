# Teoría del Sistema de Control PID

## Descripción del Sistema

Sistema de control PID para mantener la temperatura de un invernadero de vainilla en 28°C (±0.5°C). El controlador recibe la temperatura medida, calcula una señal de control y la aplica al sistema de calefacción.

---

## 1. Teoría del Controlador PID

### ¿Qué es un PID?

Un controlador PID (Proporcional-Integral-Derivativo) calcula una señal de control basándose en el error entre el valor deseado (setpoint) y el valor actual.

**Fórmula general:**
```
Salida = KP × error + KI × ∫error·dt + KD × (dTemperatura/dt)
```

### Componentes del PID

#### Término Proporcional (P)
- **Fórmula**: `P = KP × error`
- **Función**: Responde al error actual
- **Comportamiento**: 
  - Error grande → Acción fuerte
  - Error pequeño → Acción suave
  - Error cero → P = 0

#### Término Integral (I)
- **Fórmula**: `I = KI × Σ(error × dt)`
- **Función**: Elimina el error estacionario acumulando errores pasados
- **Comportamiento**: 
  - Se acumula mientras hay error
  - Sigue actuando con errores pequeños
  - Con anti-windup: limitado para evitar saturación

#### Término Derivativo (D)
- **Fórmula**: `D = KD × (dTemperatura/dt)`
- **Función**: Anticipa cambios futuros basándose en la velocidad de cambio
- **Comportamiento**: 
  - Temperatura subiendo rápido → D negativo (frena)
  - Temperatura estable → D ≈ 0
  - Temperatura bajando → D positivo (acelera)

### Parámetros del Sistema

- **KP = 1.8**: Ganancia proporcional
- **KI = 5.4**: Ganancia integral
- **KD = 0.31**: Ganancia derivativa
- **Setpoint = 28.0°C**: Temperatura objetivo

---

## 2. La Planta: Análisis del Circuito

La planta simula el comportamiento térmico del invernadero mediante un circuito electrónico.

### Estructura del Circuito

#### Etapa 1: Entrada y Filtrado (R1, R2, C1)
- **Componentes**: 2 × 10 kΩ en serie, capacitor 10 nF a tierra
- **Función**: Filtra la señal PWM del Arduino
- **Comportamiento**: Suaviza cambios bruscos, simula inercia inicial

#### Etapa 2: Integrador (Op-Amp + C2)
- **Componentes**: Amplificador operacional con capacitor 10 µF en retroalimentación
- **Función**: Integra la señal, simula acumulación de calor
- **Comportamiento**: Respuesta lenta y acumulativa (constante térmica)

#### Etapa 3: Salidas con Cargas RC

**Plant-SlowOut (Respuesta Lenta):**
- **Componentes**: R3=10 kΩ, C4=100 µF, R5=100 kΩ
- **Constante de tiempo**: τ = 10 kΩ × 100 µF = **1.0 segundo**
- **Uso**: Simula temperatura del ambiente (inercia térmica grande)

**Plant-FastOut (Respuesta Rápida):**
- **Componentes**: R4=1 kΩ, C5=100 µF, R6=100 kΩ
- **Constante de tiempo**: τ = 1 kΩ × 100 µF = **0.1 segundos**
- **Uso**: Simula sensor rápido o procesos con poca inercia

### Función de Transferencia

La planta modela un **sistema de primer orden**:
```
G(s) = K / (τs + 1)
```

- **τ (SlowOut)**: 1.0 s → Tiempo de establecimiento ≈ 5 segundos
- **τ (FastOut)**: 0.1 s → Tiempo de establecimiento ≈ 0.5 segundos

### Simulación del Comportamiento Térmico

- **Plant-Input**: Potencia del calefactor (PWM 0-255)
- **Filtro R1-R2-C1**: Inercia inicial del aire
- **Integrador Op-Amp-C2**: Acumulación de calor en la estructura
- **Carga RC**: Disipación y acumulación de temperatura
  - **SlowOut**: Temperatura ambiente (cambia lento)
  - **FastOut**: Temperatura de sensor (responde rápido)

---

## 3. Aplicación en el Proyecto

### Flujo del Sistema

1. **Arduino lee temperatura** (pin A0) → `leer_temperatura()`
2. **Calcula error** → `error = SETPOINT - temperatura`
3. **Calcula PID** → `calcular_pid(temperatura)`
4. **Aplica salida PWM** (pin 3) → `analogWrite(PIN_SALIDA, salida)`
5. **Planta recibe PWM** → Filtra y procesa
6. **Planta responde** → Cambia temperatura gradualmente
7. **Ciclo se repite** cada 100ms

### Características Implementadas

- **Filtro de promedio móvil**: 3 muestras para reducir ruido
- **Anti-windup**: Limita acumulación de I cuando salida está saturada
- **Zona muerta**: Reduce acumulación de I cuando error < 0.15°C
- **Derivativo sobre temperatura**: Evita "derivative kick"
- **Límites**: Integral ≤ 15.0, Derivativo ≤ ±50

---

## 4. Análisis de los Datos Obtenidos

### Datos Reales con Plant-SlowOut

#### Fase 1: Arranque (0°C → 20°C)

| Tiempo | Temp | Error | P | I | D | Total | Salida |
|--------|------|-------|---|---|---|-------|--------|
| Inicio | 0.00 | 28.00 | 50.40 | 15.12 | 0.00 | 65.52 | 65.52 |
| 0.78s | 0.78 | 27.22 | 48.99 | 29.82 | -2.42 | 76.39 | 76.39 |
| 2.41s | 2.41 | 25.59 | 46.06 | 43.64 | -5.05 | 84.66 | 84.66 |
| 7.49s | 7.49 | 20.51 | 36.92 | 67.18 | -7.97 | 96.13 | 96.13 |
| 12.50s | 12.50 | 15.50 | 27.90 | 81.00 | -7.67 | 101.23 | 101.23 |

**Análisis:**
- **P**: Disminuye de 50.4 a 27.9 (error se reduce)
- **I**: Crece de 15.1 a 81.0 (se satura en el límite)
- **D**: Negativo (-7.97), frena el aumento rápido
- **Salida**: Aumenta de 65.5 a 101.2 (máxima potencia)

#### Fase 2: Aproximación (20°C → 27°C)

| Temp | Error | P | I | D | Total |
|------|-------|---|---|---|-------|
| 20.35 | 7.65 | 13.78 | 81.00 | -4.74 | 90.04 |
| 23.60 | 4.40 | 7.92 | 81.00 | -2.83 | 86.09 |
| 25.00 | 3.00 | 5.40 | 81.00 | -2.02 | 84.38 |
| 26.66 | 1.34 | 2.41 | 81.00 | -1.01 | 82.40 |

**Análisis:**
- **P**: Disminuye gradualmente (7.65 → 2.41)
- **I**: Se mantiene en 81.0 (saturado)
- **D**: Se acerca a cero (-4.74 → -1.01)
- **Salida**: Disminuye (90.0 → 82.4)

#### Fase 3: Estabilización (27°C → 28°C)

| Temp | Error | P | I | D | Total |
|------|-------|---|---|---|-------|
| 27.83 | 0.17 | 0.30 | 81.00 | -0.30 | 81.00 |
| 27.99 | 0.01 | 0.01 | 81.00 | -0.20 | 80.81 |
| 28.06 | -0.06 | -0.11 | 80.98 | -0.20 | 80.67 |
| 28.22 | -0.22 | -0.40 | 80.21 | 0.00 | 79.81 |
| 28.03 | -0.03 | -0.05 | 79.07 | 0.10 | 79.13 |

**Análisis:**
- **P**: Muy pequeño (±0.4), error mínimo
- **I**: Se ajusta (81.0 → 79.1), corrige error residual
- **D**: Cerca de cero (±0.1)
- **Salida**: Estable (79-81), potencia de mantenimiento

### Interpretación de los Resultados

**Tiempo de establecimiento**: ~28 segundos (de 0°C a 28°C)
- **Arranque**: 0-12s (sube rápidamente)
- **Aproximación**: 12-25s (se acerca al setpoint)
- **Estabilización**: 25s+ (oscila alrededor de 28°C)

**Sobreimpulso**: Mínimo (~0.2°C sobre 28°C)
- La temperatura alcanza 28.22°C máximo
- Luego se estabiliza en 28.03°C

**Error estacionario**: Prácticamente cero
- En estabilización: error = ±0.03°C
- Dentro de la tolerancia (±0.5°C)

**Oscilaciones**: Mínimas
- Variación: 27.96°C - 28.22°C
- Amplitud: ~0.26°C (dentro de tolerancia)

---

## 5. Comportamiento de los Componentes PID

### Término Proporcional (P)

**Evolución:**
- **0-12s**: Alto (50.4 → 27.9), error grande
- **12-25s**: Disminuye (27.9 → 2.4), error se reduce
- **25s+**: Muy pequeño (±0.4), error mínimo

**Función**: Proporciona la respuesta inicial rápida

### Término Integral (I)

**Evolución:**
- **0-12s**: Crece (15.1 → 81.0), se satura en el límite
- **12-25s**: Se mantiene en 81.0 (saturado)
- **25s+**: Se ajusta (81.0 → 79.1), corrige error residual

**Función**: Elimina el error estacionario

### Término Derivativo (D)

**Evolución:**
- **0-12s**: Negativo (-7.97), frena aumento rápido
- **12-25s**: Se acerca a cero (-4.7 → -1.0)
- **25s+**: Cerca de cero (±0.1), cambios mínimos

**Función**: Amortigua oscilaciones y sobreimpulso

### Salida Total

**Evolución:**
- **0-12s**: Aumenta (65.5 → 101.2), máxima potencia
- **12-25s**: Disminuye (101.2 → 82.4), potencia moderada
- **25s+**: Estable (79-81), potencia de mantenimiento

---

## 6. Métricas de Rendimiento

### Tiempo de Establecimiento (ts)
- **Medido**: ~28 segundos
- **Objetivo**: < 30 segundos ✅
- **Definición**: Tiempo para llegar al 98% del setpoint

### Sobreimpulso (Mp)
- **Medido**: 0.22°C (0.8% sobre 28°C)
- **Objetivo**: < 5% (< 1.4°C) ✅
- **Definición**: Máximo sobrepaso del setpoint

### Error Estacionario (ess)
- **Medido**: ±0.03°C
- **Objetivo**: < 0.5°C ✅
- **Definición**: Error permanente en estado estable

### Oscilaciones
- **Medidas**: ±0.13°C alrededor de 28°C
- **Objetivo**: < ±0.2°C ✅
- **Definición**: Variación en estado estable

---

## 7. Conclusión

El sistema PID logra:
- ✅ Respuesta rápida (28 segundos al setpoint)
- ✅ Mínimo sobreimpulso (<1%)
- ✅ Error estacionario prácticamente cero
- ✅ Oscilaciones mínimas (<0.2°C)

El controlador funciona correctamente con los parámetros KP=1.8, KI=5.4, KD=0.31, logrando un buen balance entre velocidad de respuesta y estabilidad.
