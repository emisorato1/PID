/*
 * Control PID de temperatura para invernadero de vainilla
 * Setpoint: 28°C
 */

// Configuración
const float SETPOINT = 28.0;
const int PIN_SENSOR = A0;
const int PIN_SALIDA = 3;

// Parámetros PID
const float KP = 1.8;
const float KI = 5.4;
const float KD = 0.31;

const unsigned long PERIODO_MS = 100;

// Variables del PID
float integral = 0.0;
float temp_anterior = 0.0;
unsigned long tiempo_anterior = 0;

// Filtro simple (promedio de 3 muestras)
float filtro[3] = {0, 0, 0};
int filtro_idx = 0;

float leer_temperatura() {
    int adc = analogRead(PIN_SENSOR);
    float voltaje = (adc * 5.0) / 1024.0;
    float temp = voltaje * 20.0;  // Ajusta según tu sensor
    
    // Filtro simple
    filtro[filtro_idx] = temp;
    filtro_idx = (filtro_idx + 1) % 3;
    return (filtro[0] + filtro[1] + filtro[2]) / 3.0;
}

// Variables globales para los componentes del PID (para poder mostrarlos)
float pid_error = 0.0;
float pid_p = 0.0;
float pid_i = 0.0;
float pid_d = 0.0;
float pid_total = 0.0;

float calcular_pid(float temp_actual) {
    unsigned long tiempo = millis();
    
    // Calculo el tiempo transcurrido en segundos
    float dt = (tiempo - tiempo_anterior) / 1000.0;
    
    // Si es la primera vez o el tiempo es inválido, uso el período normal
    if (tiempo_anterior == 0 || dt <= 0 || dt > 1.0) {
        dt = PERIODO_MS / 1000.0;
    }
    
    // Calculo el error
    pid_error = SETPOINT - temp_actual;
    float error_abs = (pid_error < 0) ? -pid_error : pid_error;
    
    // Término P: proporcional al error
    pid_p = KP * pid_error;
    
    // Término D: calculo sobre la temperatura (no el error) para evitar "derivative kick"
    float cambio_temp = temp_anterior - temp_actual;
    pid_d = KD * (cambio_temp / dt);
    
    // Limito el derivativo para evitar valores extremos
    if (pid_d > 50.0) pid_d = 50.0;
    if (pid_d < -50.0) pid_d = -50.0;
    
    // Calculo salida temporal para verificar saturación (anti-windup)
    float salida_temp = pid_p + (KI * integral) + pid_d;
    
    // Zona muerta: reduzco acumulación cuando estoy muy cerca del setpoint
    float factor = 1.0;
    if (error_abs < 0.15) {
        factor = error_abs / 0.15;  // Más cerca = menos acumulación
    }
    
    // Si estoy por encima del setpoint y la salida es alta, reduzco más rápido
    if (pid_error < 0 && salida_temp > 70.0) {
        factor *= 1.5;
    }
    
    // Anti-windup: solo acumulo la integral si ayuda o no está saturado
    if (salida_temp < 255.0 && salida_temp > 0.0) {
        // No saturado: acumulo normalmente con factor de zona muerta
        integral += pid_error * dt * factor;
    } else if (salida_temp >= 255.0 && pid_error < 0) {
        // Saturado pero error negativo: reduzco más rápido
        integral += pid_error * dt * 1.2;
    } else if (salida_temp <= 0.0 && pid_error > 0) {
        // Saturado pero error positivo: aumento
        integral += pid_error * dt;
    }
    // Si está saturado y el error tiene el mismo signo, no acumulo (anti-windup)
    
    // Limito la integral para evitar que crezca infinitamente
    if (integral > 15.0) integral = 15.0;
    if (integral < -15.0) integral = -15.0;
    
    // Término I: multiplico la integral acumulada por KI
    pid_i = KI * integral;
    
    // Salida total: sumo los tres términos
    pid_total = pid_p + pid_i + pid_d;
    
    // Limito la salida entre 0 y 255 (valores válidos para PWM)
    float salida = pid_total;
    if (salida > 255.0) salida = 255.0;
    if (salida < 0.0) salida = 0.0;
    
    // Guardo valores para la próxima iteración
    temp_anterior = temp_actual;
    tiempo_anterior = tiempo;
    
    return salida;
}

void setup() {
    Serial.begin(9600);
    pinMode(PIN_SENSOR, INPUT);
    pinMode(PIN_SALIDA, OUTPUT);
    
    tiempo_anterior = millis();
    temp_anterior = leer_temperatura();
    
    Serial.println(F("=== PID Control Temperatura ==="));
    Serial.print(F("Setpoint: "));
    Serial.print(SETPOINT);
    Serial.println(F("°C"));
    Serial.println(F("Formato: >> temperatura,setpoint,error,out_p,out_i,out_d,out_total,salida"));
    Serial.println();
    
    delay(1000);
}

void loop() {
    unsigned long ahora = millis();
    
    if (ahora - tiempo_anterior >= PERIODO_MS) {
        float temp = leer_temperatura();
        float salida = calcular_pid(temp);
        
        // Aplico la salida al pin PWM
        analogWrite(PIN_SALIDA, (int)salida);
        
        // Envío todos los datos para análisis completo
        Serial.print(F(">> "));
        Serial.print(temp, 2);
        Serial.print(F(","));
        Serial.print(SETPOINT, 2);
        Serial.print(F(","));
        Serial.print(pid_error, 2);
        Serial.print(F(","));
        Serial.print(pid_p, 2);
        Serial.print(F(","));
        Serial.print(pid_i, 2);
        Serial.print(F(","));
        Serial.print(pid_d, 2);
        Serial.print(F(","));
        Serial.print(pid_total, 2);
        Serial.print(F(","));
        Serial.println(salida, 2);
    }
}