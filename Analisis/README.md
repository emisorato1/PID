# Análisis en Vivo del Controlador PID

Script para analizar en tiempo real el comportamiento del controlador PID mientras SimulIDE está ejecutándose.

## Instalación

El proyecto incluye un entorno virtual (`.venv`) con todas las dependencias instaladas.

**Windows:**
```powershell
cd Analisis
.venv\Scripts\python.exe analisis.py
```

**Linux/Mac:**
```bash
cd Analisis
.venv/bin/python analisis.py
```

## Configuración

Edita `analisis.py`:
```python
PUERTO_SERIAL = 'COM1'  # Verifica en SimulIDE cuál es el correcto
MOSTRAR_ANALISIS_ESTABILIDAD = True  # Mostrar análisis de Bode al inicio
```

## Uso

1. **Ejecuta** `analisis.py` (esperará datos del puerto serial)
2. **Inicia SimulIDE** y carga tu circuito
3. El script detectará automáticamente los datos y comenzará a graficar

El script muestra:
1. Análisis de estabilidad (márgenes de ganancia/fase) y diagrama de Bode
2. Gráfica en tiempo real: temperatura, setpoint y salida PWM

## Gráficas

**Gráfica en Tiempo Real:**
- Temperatura medida (rojo)
- Setpoint (azul, línea punteada)
- Salida PWM en % (verde, eje derecho)

## Análisis de Estabilidad

### Margen de Ganancia (GM)

Mide cuánta ganancia adicional puede tolerar el sistema antes de volverse inestable.

- Se calcula en la frecuencia donde la fase es -180°
- **Fórmula**: `GM (dB) = -20·log₁₀(|L(jωcg)|)`
- **GM > 0 dB**: Sistema estable
- **GM = ∞**: Sistema muy estable (nunca cruza -180°)

### Margen de Fase (PM)

Mide cuánto retardo de fase adicional puede tolerar el sistema antes de volverse inestable.

- Se calcula en la frecuencia donde la magnitud es 0 dB
- **Fórmula**: `PM = 180° + ∠L(jωcp)`
- **PM > 0°**: Sistema estable
- **Rango óptimo**: 30° < PM < 60°

### Interpretación

**✅ Sistema Robusto:**
- `GM > 3 dB` Y `30° < PM < 60°`

**⚠️ Sistema Propenso a Oscilaciones:**
- `GM < 3 dB` O `PM < 30°` O `PM > 60°`

## Solución de Problemas

**Error: "No se puede abrir el puerto COM1"**
- Verifica que SimulIDE esté corriendo
- Cambia `PUERTO_SERIAL` en `analisis.py` al puerto correcto

**No aparecen datos en las gráficas**
- Verifica que el firmware envíe datos con formato: `>> temperatura,setpoint,error,out_p,out_i,out_d,out_total,salida`
- Verifica que el baud rate sea 9600

**El análisis de estabilidad no se muestra**
- Cambia `MOSTRAR_ANALISIS_ESTABILIDAD = True` en `analisis.py`

## Parámetros del Sistema

Los parámetros están en `analisis.py`:
```python
KP = 1.8, KI = 5.4, KD = 0.31  # PID
K = 0.35, T = 1.0s, L = 0.1s   # Planta
```

Si cambias los parámetros del PID en el firmware, actualiza también estos valores.

## Documentación Adicional

- **`EXPLICACION_FORMULAS.md`**: Explicación detallada de las fórmulas y su origen teórico
