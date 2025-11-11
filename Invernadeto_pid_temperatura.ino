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
    float dt = (tiempo - tiempo_anterior) / 1000.0;
    if (dt <= 0 || dt > 1.0) dt = PERIODO_MS / 1000.0;
    
    pid_error = SETPOINT - temp_actual;
    float error_abs = (pid_error < 0) ? -pid_error : pid_error;
    
    // Término P
    pid_p = KP * pid_error;
    
    // Término D
    float cambio = temp_anterior - temp_actual;
    pid_d = KD * (cambio / dt);
    if (pid_d > 50.0) pid_d = 50.0;
    if (pid_d < -50.0) pid_d = -50.0;
    
    // Término I con anti-windup simplificado
    float salida_temp = pid_p + (KI * integral) + pid_d;
    
    // Zona muerta simple
    float factor = 1.0;
    if (error_abs < 0.15) factor = error_abs / 0.15;
    if (pid_error < 0 && salida_temp > 70.0) factor *= 1.5;
    
    // Anti-windup: solo acumulo si no está saturado o ayuda
    if (salida_temp < 255.0 && salida_temp > 0.0) {
        integral += pid_error * dt * factor;
    } else if (salida_temp >= 255.0 && pid_error < 0) {
        integral += pid_error * dt * 1.2;
    } else if (salida_temp <= 0.0 && pid_error > 0) {
        integral += pid_error * dt;
    }
    
    // Limito la integral
    if (integral > 15.0) integral = 15.0;
    if (integral < -15.0) integral = -15.0;
    
    pid_i = KI * integral;
    pid_total = pid_p + pid_i + pid_d;
    
    // Limito la salida PWM
    float salida = pid_total;
    if (salida > 255.0) salida = 255.0;
    if (salida < 0.0) salida = 0.0;
    
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
