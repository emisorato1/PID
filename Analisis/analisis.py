import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import control as ct
from collections import deque
import time
import datetime

# --- CONFIGURACIÓN DEL USUARIO ---
PUERTO_SERIAL = 'COM1'  # Puerto virtual de SimulIDE (cambiar si es necesario)
BAUD_RATE = 9600
MAX_PUNTOS = 300  # Número de puntos a mostrar en la gráfica
MOSTRAR_ANALISIS_ESTABILIDAD = True  # Si True, muestra análisis al inicio (bloquea hasta cerrar)

# --- MODELO DEL SISTEMA PARA ANÁLISIS DE ESTABILIDAD ---
# Parámetros del Controlador PID (de los archivos .ino y .md)
KP = 1.8
KI = 5.4
KD = 0.31

# Parámetros estimados de la Planta (Invernadero)
K = 0.35   # Ganancia (°C / % PWM)
T = 1.0    # Constante de Tiempo (segundos)
L = 0.1    # Tiempo muerto / Retardo (segundos)

# --- ANÁLISIS DE FRECUENCIA (MÁRGENES DE GANANCIA Y FASE) ---
def analizar_estabilidad():
    """
    Calcula y muestra los márgenes de ganancia/fase y el diagrama de Bode.
    
    EXPLICACIÓN DE LOS MÁRGENES:
    
    MARGEN DE GANANCIA (GM):
    - Es la cantidad de ganancia adicional que puede tolerar el sistema antes de volverse inestable.
    - Se calcula en la frecuencia donde la fase es -180° (frecuencia de cruce de fase, ωcg).
    - Fórmula: GM (lineal) = 1 / |L(jωcg)|, donde L(jωcg) es la función de transferencia en lazo abierto
    - En decibeles: GM (dB) = 20 * log10(GM_lineal) = -20 * log10(|L(jωcg)|)
    - Si GM > 1 (o GM > 0 dB): el sistema es estable
    - Si GM = infinito: significa que la fase nunca cruza -180°, el sistema es muy estable
    
    MARGEN DE FASE (PM):
    - Es la cantidad de retardo de fase adicional que puede tolerar el sistema antes de volverse inestable.
    - Se calcula en la frecuencia donde la magnitud es 0 dB (frecuencia de cruce de ganancia, ωcp).
    - Fórmula: PM = 180° + ∠L(jωcp), donde ∠L(jωcp) es el ángulo de fase en grados
    - Si PM > 0°: el sistema es estable
    - Rango óptimo: 30° < PM < 60°
    """
    print("=" * 70)
    print("ANÁLISIS DE ESTABILIDAD DEL SISTEMA")
    print("=" * 70)
    
    # ========================================================================
    # CONSTRUCCIÓN DEL MODELO DEL SISTEMA
    # ========================================================================
    
    # Variable de Laplace
    s = ct.TransferFunction.s
    
    # Función de transferencia del controlador PID
    # Gc(s) = KP + KI/s + KD*s
    # - KP: término proporcional (respuesta inmediata al error)
    # - KI/s: término integral (elimina error estacionario)
    # - KD*s: término derivativo (anticipa cambios, reduce oscilaciones)
    G_c = KP + KI/s + KD*s
    G_c.name = 'Controlador PID'
    
    # Función de transferencia de la Planta (FOPDT: First Order Plus Dead Time)
    # Modelo: Gp(s) = (K / (T*s + 1)) * e^(-L*s)
    # - K: ganancia estática (°C / % PWM) - cuánto cambia la temperatura por unidad de PWM
    # - T: constante de tiempo (segundos) - qué tan rápido responde el sistema
    # - L: tiempo muerto/retardo (segundos) - retardo puro en la respuesta
    # - e^(-L*s): retardo puro (no es una función racional, necesita aproximación)
    
    # Aproximación de Padé para el retardo de tiempo
    # Padé aproxima e^(-L*s) como una función racional (cociente de polinomios)
    # Orden 1: e^(-L*s) ≈ (1 - L*s/2) / (1 + L*s/2)
    n_pade, d_pade = ct.pade(L, 1)  # Aproximación de 1er orden
    retardo = ct.TransferFunction(n_pade, d_pade)
    
    # Planta completa: sistema de primer orden con retardo
    G_p = (K / (T*s + 1)) * retardo
    G_p.name = 'Planta (Invernadero)'

    # Función de transferencia de lazo abierto L(s) = Gc(s) * Gp(s)
    # Esta es la función que se analiza para determinar la estabilidad
    L_s = G_c * G_p
    
    print("\n[1/4] Modelo del Sistema")
    print("-" * 70)
    print(f"Controlador PID Gc(s):\n{G_c}\n")
    print(f"Planta Gp(s):\n{G_p}\n")
    print(f"Función de Lazo Abierto L(s) = Gc(s) × Gp(s):\n{L_s}\n")
    
    # ========================================================================
    # CÁLCULO DE MÁRGENES DE GANANCIA Y FASE
    # ========================================================================
    
    print("[2/4] Calculando Márgenes de Estabilidad...")
    print("-" * 70)
    
    # ct.margin() calcula automáticamente:
    # - gm: margen de ganancia (valor lineal, no en dB)
    # - pm: margen de fase (en grados)
    # - wcg: frecuencia de cruce de fase (rad/s) - donde fase = -180°
    # - wcp: frecuencia de cruce de ganancia (rad/s) - donde magnitud = 0 dB
    gm, pm, wcg, wcp = ct.margin(L_s)
    
    # ========================================================================
    # CONVERSIÓN Y MANEJO DE RESULTADOS
    # ========================================================================
    
    # Convertir margen de ganancia a decibeles
    # Fórmula: dB = 20 * log10(valor_lineal)
    # Esta es la fórmula estándar para convertir ganancia a decibeles
    # Ejemplo: ganancia de 2 → 20*log10(2) ≈ 6.02 dB (duplica la señal)
    #          ganancia de 0.5 → 20*log10(0.5) ≈ -6.02 dB (reduce a la mitad)
    
    # Manejar casos especiales:
    # - Si gm es infinito: el sistema nunca cruza -180°, es muy estable
    # - Si gm es NaN: no se encontró cruce de fase
    if np.isinf(gm) or np.isnan(gm):
        gm_db = np.inf
        gm_str = "∞ (infinito)"
        wcg_str = "N/A (no hay cruce de fase)"
        interpretacion_gm = "El sistema NUNCA cruza la línea de -180° de fase. " \
                           "Esto significa que es MUY ESTABLE en términos de ganancia. " \
                           "No hay frecuencia donde el sistema se vuelva inestable por aumento de ganancia."
    else:
        gm_db = 20 * np.log10(gm)
        gm_str = f"{gm_db:.2f} dB"
        if not np.isnan(wcg) and wcg > 0:
            wcg_str = f"{wcg:.2f} rad/s ({wcg/(2*np.pi):.3f} Hz)"
        else:
            wcg_str = "N/A"
        interpretacion_gm = f"El sistema puede tolerar un aumento de ganancia de {gm:.2f}x " \
                          f"({gm_db:.2f} dB) antes de volverse inestable."
    
    # Manejar margen de fase
    if not np.isnan(pm) and not np.isnan(wcp) and wcp > 0:
        pm_str = f"{pm:.2f}°"
        wcp_str = f"{wcp:.2f} rad/s ({wcp/(2*np.pi):.3f} Hz)"
        
        # Interpretación del margen de fase
        if pm > 60:
            interpretacion_pm = f"Margen muy alto ({pm:.1f}°). Sistema muy robusto pero puede ser " \
                               "demasiado lento (sobre-amortiguado)."
        elif 30 < pm <= 60:
            interpretacion_pm = f"Margen óptimo ({pm:.1f}°). Sistema estable con buena respuesta transitoria."
        elif 0 < pm <= 30:
            interpretacion_pm = f"Margen bajo ({pm:.1f}°). Sistema estable pero puede tener " \
                              "oscilaciones en la respuesta transitoria."
        else:
            interpretacion_pm = f"Margen negativo ({pm:.1f}°). Sistema INESTABLE."
    else:
        pm_str = "N/A"
        wcp_str = "N/A"
        interpretacion_pm = "No se pudo calcular el margen de fase."
    
    # ========================================================================
    # MOSTRAR RESULTADOS
    # ========================================================================
    
    print("\n[3/4] Resultados del Análisis")
    print("=" * 70)
    print(f"\n📊 MARGEN DE GANANCIA (Gain Margin, GM):")
    print(f"   Valor: {gm_str}")
    print(f"   Frecuencia de cruce de fase (ωcg): {wcg_str}")
    print(f"   Interpretación: {interpretacion_gm}")
    
    print(f"\n📊 MARGEN DE FASE (Phase Margin, PM):")
    print(f"   Valor: {pm_str}")
    print(f"   Frecuencia de cruce de ganancia (ωcp): {wcp_str}")
    print(f"   Interpretación: {interpretacion_pm}")
    
    # Evaluación general del sistema
    print(f"\n[4/4] Evaluación General del Sistema")
    print("=" * 70)
    
    # Criterios de estabilidad mejorados
    sistema_estable = True
    problemas = []
    
    if np.isinf(gm_db) or (not np.isnan(gm_db) and gm_db > 3):
        print("✅ Margen de Ganancia: ADECUADO")
    elif not np.isnan(gm_db) and gm_db > 0:
        print("⚠️  Margen de Ganancia: BAJO (GM < 3 dB)")
        problemas.append("Margen de ganancia bajo")
        sistema_estable = False
    else:
        print("❌ Margen de Ganancia: INESTABLE (GM < 0 dB)")
        problemas.append("Margen de ganancia negativo")
        sistema_estable = False
    
    if not np.isnan(pm):
        if 30 < pm <= 60:
            print("✅ Margen de Fase: ÓPTIMO")
        elif pm > 60:
            print("⚠️  Margen de Fase: ALTO (PM > 60°) - puede ser demasiado lento")
            problemas.append("Margen de fase muy alto")
        elif 0 < pm <= 30:
            print("⚠️  Margen de Fase: BAJO (PM < 30°) - puede oscilar")
            problemas.append("Margen de fase bajo")
        else:
            print("❌ Margen de Fase: INESTABLE (PM < 0°)")
            problemas.append("Margen de fase negativo")
            sistema_estable = False
    
    print()
    if sistema_estable and len(problemas) == 0:
        print("✅ CONCLUSIÓN: El sistema es ROBUSTO y ESTABLE.")
        print("   - Tiene buenos márgenes de seguridad")
        print("   - Respuesta transitoria bien amortiguada")
        print("   - Puede tolerar variaciones en los parámetros")
    elif sistema_estable:
        print("⚠️  CONCLUSIÓN: El sistema es ESTABLE pero puede tener problemas:")
        for p in problemas:
            print(f"   - {p}")
    else:
        print("❌ CONCLUSIÓN: El sistema puede ser INESTABLE o propenso a oscilaciones.")
        for p in problemas:
            print(f"   - {p}")
        print("   RECOMENDACIÓN: Ajustar parámetros PID (reducir KP y/o KI)")
    
    print("\n" + "=" * 70)

    # ========================================================================
    # GRÁFICA DE BODE
    # ========================================================================
    
    # Graficar Diagrama de Bode (solo mostrar si está habilitado)
    if MOSTRAR_ANALISIS_ESTABILIDAD:
        try:
            print("\n📈 Generando Diagrama de Bode...")
            
            # Crear figura con dos subplots
            fig = plt.figure(figsize=(12, 8))
            
            # Generar el diagrama de Bode usando la librería control
            # display_margins=True muestra automáticamente las líneas de referencia
            # dB=True muestra la magnitud en decibeles
            # Hz=False usa rad/s en lugar de Hz para la frecuencia
            mag, phase, omega = ct.bode(L_s, dB=True, Hz=False, omega_limits=(0.01, 100))
            
            # Obtener los ejes actuales de matplotlib
            axes = plt.gcf().get_axes()
            
            # Mejorar la visualización del gráfico de magnitud
            if len(axes) >= 1:
                axes[0].set_title('Magnitud (Diagrama de Bode)', fontsize=12, fontweight='bold')
                axes[0].set_ylabel('Magnitud [dB]', fontsize=11)
                axes[0].grid(True, alpha=0.3, which='both')
                # Línea de referencia en 0 dB (ganancia unitaria)
                axes[0].axhline(y=0, color='g', linestyle='--', alpha=0.5, 
                               label='0 dB (ganancia unitaria)')
                axes[0].legend(loc='best')
            
            # Mejorar la visualización del gráfico de fase
            if len(axes) >= 2:
                axes[1].set_title('Fase (Diagrama de Bode)', fontsize=12, fontweight='bold')
                axes[1].set_ylabel('Fase [grados]', fontsize=11)
                axes[1].set_xlabel('Frecuencia [rad/s]', fontsize=11)
                axes[1].grid(True, alpha=0.3, which='both')
                # Línea de referencia en -180° (límite de estabilidad)
                axes[1].axhline(y=-180, color='r', linestyle='--', alpha=0.5, 
                               label='-180° (límite de estabilidad)')
                axes[1].legend(loc='best')
            
            # Título general con información de los márgenes
            fig.suptitle("Diagrama de Bode del Sistema en Lazo Abierto\n" +
                        f"GM = {gm_str} @ {wcg_str}  |  PM = {pm_str} @ {wcp_str}", 
                        fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.show(block=False)  # No bloquea, permite continuar
            plt.pause(0.1)  # Pequeña pausa para que se renderice
            print("✅ Diagrama de Bode generado correctamente")
        except Exception as e:
            print(f"⚠️  Error al mostrar diagrama de Bode: {e}")
            # Intentar método alternativo si el anterior falla
            try:
                print("   Intentando método alternativo...")
                plt.figure(figsize=(12, 8))
                ct.bode_plot(L_s, display_margins=True, dB=True)
                plt.suptitle("Diagrama de Bode del Sistema en Lazo Abierto", 
                            fontsize=14, fontweight='bold')
                plt.tight_layout()
                plt.show(block=False)
                plt.pause(0.1)
                print("✅ Diagrama de Bode generado con método alternativo")
            except Exception as e2:
                print(f"⚠️  Error también con método alternativo: {e2}")
                import traceback
                traceback.print_exc()

# --- GRAFICACIÓN EN TIEMPO REAL ---

# Inicializar la conexión serial (se hará después del análisis si es necesario)
ser = None
intentos_serial = 0
MAX_INTENTOS_SERIAL = 10  # Intentar conectar solo 10 veces antes de dar por perdido

# Contenedores para los datos
tiempo = deque(maxlen=MAX_PUNTOS)
temperatura = deque(maxlen=MAX_PUNTOS)
setpoint = deque(maxlen=MAX_PUNTOS)
salida_pwm = deque(maxlen=MAX_PUNTOS)
pid_p = deque(maxlen=MAX_PUNTOS)
pid_i = deque(maxlen=MAX_PUNTOS)
pid_d = deque(maxlen=MAX_PUNTOS)

# Configuración de la figura para graficar
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
fig.suptitle('Análisis en Vivo del Controlador PID', fontsize=16)

# Gráfica 1: Temperatura
ax1.set_ylabel('Temperatura [°C]')
ax1.grid(True)
line_temp, = ax1.plot([], [], 'r-', label='Temperatura Medida')
line_setpoint, = ax1.plot([], [], 'b--', label='Setpoint')
ax1.legend()
ax1_twin = ax1.twinx()
ax1_twin.set_ylabel('Salida PID [%]')
line_pwm, = ax1_twin.plot([], [], 'g-', alpha=0.5, label='Salida PWM')
ax1_twin.legend(loc='lower right')

# Gráfica 2: Componentes PID
ax2.set_ylabel('Contribución PID')
ax2.set_xlabel('Tiempo [s]')
ax2.grid(True)
line_p, = ax2.plot([], [], label='Componente P')
line_i, = ax2.plot([], [], label='Componente I')
line_d, = ax2.plot([], [], label='Componente D')
ax2.legend()

start_time = None

def init():
    """Función de inicialización para la animación."""
    ax1.set_ylim(20, 35)
    ax1_twin.set_ylim(0, 100)  # PWM en porcentaje (0-100%)
    ax2.set_ylim(-100, 100)
    ax1.set_xlim(0, 30)  # Inicializar con 30 segundos
    ax2.set_xlim(0, 30)
    return line_temp, line_setpoint, line_pwm, line_p, line_i, line_d

def update(frame):
    """Función que se llama en cada frame para actualizar la gráfica."""
    global start_time, ser, intentos_serial
    
    # Inicializar serial si no está abierto
    if ser is None or (hasattr(ser, 'is_open') and not ser.is_open):
        if intentos_serial < MAX_INTENTOS_SERIAL:
            try:
                ser = serial.Serial(PUERTO_SERIAL, BAUD_RATE, timeout=0.1)
                print(f"✅ Conectado al puerto {PUERTO_SERIAL}")
                intentos_serial = MAX_INTENTOS_SERIAL  # Ya conectó, no intentar más
            except serial.SerialException as e:
                intentos_serial += 1
                if intentos_serial == 1:  # Solo mostrar el error la primera vez
                    print(f"⚠️ Error al abrir el puerto {PUERTO_SERIAL}: {e}")
                    print("   Asegúrate de que SimulIDE esté corriendo y el puerto sea correcto.")
                    print("   Reintentando...")
            except Exception as e:
                intentos_serial += 1
                if intentos_serial == 1:
                    print(f"⚠️ Error inesperado: {e}")
        else:
            # Ya intentamos muchas veces, solo retornar sin hacer nada
            return line_temp, line_setpoint, line_pwm, line_p, line_i, line_d
    
    # Leer datos del serial
    if ser and ser.is_open:
        try:
            # Leer todas las líneas disponibles
            while ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                # Ignorar líneas vacías
                if not line:
                    continue
                
                # Buscamos el prefijo ">> " para asegurarnos que es una línea de datos
                if line.startswith(">> "):
                    # Extraemos los datos
                    parts = line.replace(">> ", "").split(',')
                    if len(parts) == 8:
                        # Convertimos los datos a números
                        try:
                            data = [float(p) for p in parts]
                            
                            if start_time is None:
                                start_time = time.time()
                                print(f"📊 Recibiendo datos... (T={data[0]:.2f}°C, Setpoint={data[1]:.2f}°C)")

                            current_time = time.time() - start_time

                            # Añadimos los datos a las listas
                            tiempo.append(current_time)
                            temperatura.append(data[0])
                            setpoint.append(data[1])
                            pid_p.append(data[3])
                            pid_i.append(data[4])
                            pid_d.append(data[5])
                            salida_pwm.append(data[7] * 100.0 / 255.0)  # Convertir PWM a %
                        except (ValueError, IndexError) as e:
                            # Debug: mostrar línea que no se pudo parsear
                            if len(tiempo) == 0:  # Solo mostrar errores al inicio
                                print(f"⚠️ Error parseando línea: {line[:50]}...")
        except serial.SerialException as e:
            print(f"⚠️ Error de comunicación serial: {e}")
        except Exception as e:
            if len(tiempo) == 0:  # Solo mostrar errores al inicio
                print(f"⚠️ Error inesperado: {e}")
    
    # Actualizar gráficas si hay datos
    if len(tiempo) > 0:
        # Convertir deques a listas para matplotlib
        t_list = list(tiempo)
        temp_list = list(temperatura)
        setpoint_list = list(setpoint)
        pwm_list = list(salida_pwm)
        p_list = list(pid_p)
        i_list = list(pid_i)
        d_list = list(pid_d)
        
        # Actualizar las líneas
        line_temp.set_data(t_list, temp_list)
        line_setpoint.set_data(t_list, setpoint_list)
        line_pwm.set_data(t_list, pwm_list)
        line_p.set_data(t_list, p_list)
        line_i.set_data(t_list, i_list)
        line_d.set_data(t_list, d_list)

        # Ajustar límites del eje X dinámicamente
        if len(t_list) > 1:
            t_min = max(0, t_list[0])
            t_max = t_list[-1]
            ax1.set_xlim(t_min, max(t_max, t_min + 30))
            ax2.set_xlim(t_min, max(t_max, t_min + 30))
        elif len(t_list) == 1:
            # Si solo hay un punto, mostrar un rango inicial
            ax1.set_xlim(0, 30)
            ax2.set_xlim(0, 30)
        
        # Ajustar límites Y dinámicamente para temperatura
        if len(temp_list) > 0:
            temp_min = min(min(temp_list), 20)
            temp_max = max(max(temp_list), 35)
            ax1.set_ylim(temp_min - 2, temp_max + 2)
        
        # Ajustar límites Y para componentes PID
        if len(p_list) > 0 or len(i_list) > 0 or len(d_list) > 0:
            all_pid = p_list + i_list + d_list
            if all_pid:
                pid_min = min(min(all_pid), -100)
                pid_max = max(max(all_pid), 100)
                ax2.set_ylim(pid_min - 10, pid_max + 10)

    return line_temp, line_setpoint, line_pwm, line_p, line_i, line_d

# --- EJECUCIÓN PRINCIPAL ---
if __name__ == '__main__':
    print("=" * 60)
    print("ANÁLISIS EN VIVO DEL CONTROLADOR PID")
    print("=" * 60)
    
    # 1. Realizar el análisis de estabilidad (opcional, puede bloquear)
    if MOSTRAR_ANALISIS_ESTABILIDAD:
        print("\n[1/2] Realizando análisis de estabilidad...")
        analizar_estabilidad()
        print("\n[2/2] Iniciando graficación en tiempo real...")
    else:
        print("\n[1/1] Iniciando graficación en tiempo real...")
    
    # 2. Iniciar la animación para la graficación en tiempo real
    print(f"   Esperando datos del puerto {PUERTO_SERIAL}...")
    print("   (Asegúrate de que SimulIDE esté corriendo)")
    print("   Presiona Ctrl+C o cierra la ventana para terminar\n")
    
    try:
        ani = animation.FuncAnimation(fig, update, init_func=init, blit=False, 
                                     interval=50, cache_frame_data=False, save_count=MAX_PUNTOS)
        plt.show()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupción del usuario")
    finally:
        # Cerrar el puerto serial al terminar
        if ser is not None and hasattr(ser, 'is_open') and ser.is_open:
            ser.close()
            print("✅ Puerto serial cerrado. Programa finalizado.")
