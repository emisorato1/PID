# Explicación de las Fórmulas de Estabilidad

## Modelo del Sistema

### Controlador PID
```
Gc(s) = KP + KI/s + KD·s
```

### Planta (FOPDT)
```
Gp(s) = (K / (T·s + 1)) · e^(-L·s)
```

**Parámetros:**
- **K = 0.35**: Ganancia estática (°C / % PWM)
- **T = 1.0s**: Constante de tiempo
- **L = 0.1s**: Tiempo muerto/retardo

**Aproximación de Padé** (para el retardo):
```
e^(-L·s) ≈ (1 - L·s/2) / (1 + L·s/2)
```

### Función de Lazo Abierto
```
L(s) = Gc(s) × Gp(s)
```

## Margen de Ganancia (GM)

### ¿Qué es?

Mide cuánta ganancia adicional puede tolerar el sistema antes de volverse inestable.

### Cálculo

1. Encontrar frecuencia donde fase = -180° (ωcg)
2. Evaluar magnitud en esa frecuencia: `|L(jωcg)|`
3. Calcular:
   ```
   GM (lineal) = 1 / |L(jωcg)|
   GM (dB) = 20·log₁₀(GM_lineal) = -20·log₁₀(|L(jωcg)|)
   ```

### Interpretación

| GM (dB) | Interpretación |
|---------|----------------|
| ∞ | Fase nunca cruza -180°. Sistema muy estable |
| > 6 dB | Sistema muy robusto |
| 3-6 dB | Sistema estable con margen moderado |
| 0-3 dB | Sistema estable pero cercano a inestabilidad |
| < 0 dB | Sistema inestable |

## Margen de Fase (PM)

### ¿Qué es?

Mide cuánto retardo de fase adicional puede tolerar el sistema antes de volverse inestable.

### Cálculo

1. Encontrar frecuencia donde magnitud = 0 dB (ωcp)
2. Evaluar fase en esa frecuencia: `∠L(jωcp)`
3. Calcular:
   ```
   PM = 180° + ∠L(jωcp)
   ```

### Interpretación

| PM | Interpretación |
|----|----------------|
| > 60° | Sistema muy robusto pero puede ser lento |
| 30° - 60° | **Rango óptimo**. Buena respuesta transitoria |
| 0° - 30° | Sistema estable pero puede oscilar |
| < 0° | Sistema inestable |

## Origen Teórico

Las fórmulas provienen del **Criterio de Nyquist**:

- Un sistema en lazo cerrado es estable si el diagrama de Nyquist de la función de lazo abierto no encierra el punto (-1, 0).
- El punto (-1, 0) corresponde a magnitud 1 (0 dB) y fase -180°.
- Los márgenes miden qué tan cerca está el sistema de este punto crítico.

## Conversión a Decibeles

**Fórmula estándar:**
```
dB = 20·log₁₀(valor_lineal)
```

**Por qué 20 y no 10?**
- Para magnitudes (ganancias): se usa 20 porque la potencia es proporcional al cuadrado de la amplitud.
- Para potencias: se usaría 10·log₁₀(valor).

## Ejemplo Real

Para el sistema con KP=1.8, KI=5.4, KD=0.31, K=0.35, T=1.0s, L=0.1s:

```
Margen de Ganancia (GM): ∞ (infinito) @ N/A
Margen de Fase   (PM): 56.44° @ 1.21 rad/s
```

**Interpretación:**
- **GM = ∞**: Sistema muy estable, nunca cruza -180°
- **PM = 56.44°**: Excelente margen, dentro del rango óptimo (30°-60°)

## Criterios de Estabilidad

**✅ Sistema Robusto:**
- `GM > 3 dB` (o GM = ∞) **Y**
- `30° < PM < 60°`

**⚠️ Sistema con Problemas:**
- `GM < 3 dB` O `PM < 30°` O `PM > 60°`
