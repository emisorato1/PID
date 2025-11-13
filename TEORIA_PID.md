# Teoría del Sistema de Control PID

Sistema de control PID para mantener la temperatura de un invernadero de vainilla en 28°C (±0.5°C).

## Controlador PID

### Fórmula General

```
Salida = KP × error + KI × ∫error·dt + KD × (dTemperatura/dt)
```

### Componentes

**Término Proporcional (P)**: `P = KP × error`
- Responde al error actual
- Error grande → Acción fuerte
- Error cero → P = 0

**Término Integral (I)**: `I = KI × Σ(error × dt)`
- Elimina el error estacionario
- Se acumula mientras hay error
- Con anti-windup: limitado para evitar saturación

**Término Derivativo (D)**: `D = KD × (dTemperatura/dt)`
- Anticipa cambios futuros
- Temperatura subiendo rápido → D negativo (frena)
- Temperatura estable → D ≈ 0

### Parámetros del Sistema

- **KP = 1.8**: Ganancia proporcional
- **KI = 5.4**: Ganancia integral
- **KD = 0.31**: Ganancia derivativa
- **Setpoint = 28.0°C**: Temperatura objetivo

## La Planta

La planta simula el comportamiento térmico del invernadero mediante un circuito electrónico.

### Estructura

1. **Filtrado (R1, R2, C1)**: Filtra la señal PWM, simula inercia inicial
2. **Integrador (Op-Amp + C2)**: Integra la señal, simula acumulación de calor
3. **Salidas RC**:
   - **Plant-SlowOut**: τ=1.0s (temperatura ambiente, usar esta)
   - **Plant-FastOut**: τ=0.1s (sensor rápido, solo pruebas)

### Función de Transferencia

Sistema de primer orden: `G(s) = K / (τs + 1)`

- **τ (SlowOut)**: 1.0s → Tiempo de establecimiento ≈ 5 segundos
- **τ (FastOut)**: 0.1s → Tiempo de establecimiento ≈ 0.5 segundos

## Flujo del Sistema

1. Arduino lee temperatura (pin A0)
2. Calcula error: `error = SETPOINT - temperatura`
3. Calcula PID: `calcular_pid(temperatura)`
4. Aplica salida PWM (pin 3)
5. Planta recibe PWM y responde gradualmente
6. Ciclo se repite cada 100ms

## Características Implementadas

- Filtro de promedio móvil (3 muestras)
- Anti-windup mejorado
- Zona muerta (<0.15°C)
- Derivativo sobre temperatura (evita "derivative kick")
- Límites: Integral ≤ 15.0, Derivativo ≤ ±50

## Métricas de Rendimiento

| Métrica | Objetivo | Resultado |
|---------|----------|-----------|
| Tiempo de establecimiento | < 30s | ~28s ✅ |
| Sobreimpulso | < 5% (< 1.4°C) | 0.8% (0.22°C) ✅ |
| Error estacionario | < 0.5°C | ±0.03°C ✅ |
| Oscilaciones | < ±0.2°C | ±0.13°C ✅ |

## Comportamiento de los Componentes PID

### Evolución Temporal

**Término P:**
- 0-12s: Alto (50.4 → 27.9), error grande
- 12-25s: Disminuye (27.9 → 2.4), error se reduce
- 25s+: Muy pequeño (±0.4), error mínimo

**Término I:**
- 0-12s: Crece (15.1 → 81.0), se satura
- 12-25s: Se mantiene en 81.0 (saturado)
- 25s+: Se ajusta (81.0 → 79.1), corrige error residual

**Término D:**
- 0-12s: Negativo (-7.97), frena aumento rápido
- 12-25s: Se acerca a cero (-4.7 → -1.0)
- 25s+: Cerca de cero (±0.1), cambios mínimos

**Salida Total:**
- 0-12s: Aumenta (65.5 → 101.2), máxima potencia
- 12-25s: Disminuye (101.2 → 82.4), potencia moderada
- 25s+: Estable (79-81), potencia de mantenimiento

## Conclusión

El sistema PID logra:
- ✅ Respuesta rápida (28 segundos al setpoint)
- ✅ Mínimo sobreimpulso (<1%)
- ✅ Error estacionario prácticamente cero
- ✅ Oscilaciones mínimas (<0.2°C)

El controlador funciona correctamente con KP=1.8, KI=5.4, KD=0.31, logrando un buen balance entre velocidad de respuesta y estabilidad.
