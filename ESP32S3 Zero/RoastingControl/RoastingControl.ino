#include <max6675.h>
#include <math.h>
//#include "PIDController.h"

int thermoDO = 11;
int thermoCS = 12;
int thermoCLK = 13;

// FreeRTOS Task Handle
TaskHandle_t TempTaskHandle;
MAX6675 thermocouple(thermoCLK, thermoCS, thermoDO);

volatile float temp = NAN;
volatile int errorReadings = 0;
volatile bool abortSignal = false;
volatile bool failsafeEventPending = false;
volatile uint8_t healthyReadings = 0;
portMUX_TYPE stateMux = portMUX_INITIALIZER_UNLOCKED;

int fanPin = 2;
int relayPin = 1;
float relayValue = 0;
float appliedRelayValue = 0;
float fanTargetValue = 0;
float fanValue = 0;

double fanMaxAcceleration = 2.0; //max acceleration per cycle

const float PWM_MIN = 0.0f;
const float PWM_MAX = 255.0f;
const float MIN_SAFE_FAN = 128.0f;  // 50 % Mindestluftstrom bei aktiver Heizung
const float FAILSAFE_FAN = PWM_MAX;
const char* FIRMWARE_VERSION = "1.3.2";
const uint8_t PROTOCOL_VERSION = 3;
const char* HARDWARE_ID = "CoffeeRoast-Waveshare-ESP32-S3-Zero";

int delayValue = 50;


bool autoRunMode = true;
unsigned long StartTime = millis(); 
//double profile[800];

float readTemperature() {
    return thermocouple.readCelsius();
}

float clampPwm(float value) {
  if (value < PWM_MIN) {
    return PWM_MIN;
  }

  if (value > PWM_MAX) {
    return PWM_MAX;
  }

  return value;
}

void printStatus() {
  float snapshotTemp;
  int snapshotErrors;
  bool snapshotAbort;
  uint8_t snapshotHealthyReadings;

  portENTER_CRITICAL(&stateMux);
  snapshotTemp = temp;
  snapshotErrors = errorReadings;
  snapshotAbort = abortSignal;
  snapshotHealthyReadings = healthyReadings;
  portEXIT_CRITICAL(&stateMux);

  Serial.print("state=");
  Serial.print(snapshotAbort ? "failsafe" : "ok");
  Serial.print(",temp=");
  Serial.print(snapshotTemp);
  Serial.print(",heater=");
  Serial.print(appliedRelayValue);
  Serial.print(",fan=");
  Serial.print(fanValue);
  Serial.print(",fanTarget=");
  Serial.print(fanTargetValue);
  Serial.print(",errors=");
  Serial.print(snapshotErrors);
  Serial.print(",healthyReadings=");
  Serial.print(snapshotHealthyReadings);
  Serial.print(",failsafeLatched=");
  Serial.print(snapshotAbort ? 1 : 0);
  Serial.print(",version=");
  Serial.print(FIRMWARE_VERSION);
  Serial.print(",protocol=");
  Serial.print(PROTOCOL_VERSION);
  Serial.print(",hardware=");
  Serial.println(HARDWARE_ID);
}

void printInfo() {
  Serial.print("product=CoffeeRoast,firmware=");
  Serial.print(FIRMWARE_VERSION);
  Serial.print(",protocol=");
  Serial.print(PROTOCOL_VERSION);
  Serial.print(",hardware=");
  Serial.println(HARDWARE_ID);
}

bool resetFailsafeIfSafe() {
  const bool outputsSafe = relayValue <= PWM_MIN && appliedRelayValue <= PWM_MIN && fanValue >= MIN_SAFE_FAN;
  bool resetAllowed = false;

  portENTER_CRITICAL(&stateMux);
  resetAllowed = abortSignal && outputsSafe && errorReadings == 0 && healthyReadings >= 3 && isfinite(temp) && temp > 0.0f && temp < 450.0f;
  if (resetAllowed) {
    abortSignal = false;
    failsafeEventPending = false;
  }
  portEXIT_CRITICAL(&stateMux);

  return resetAllowed;
}

// FreeRTOS Task: Reads temperature every 500ms
void TemperatureTask(void *parameter) {
    float candidateTemp = NAN;
    uint8_t candidateReadings = 0;

    while (1) {
        const float sample = readTemperature();
        const bool plausible = isfinite(sample) && sample > 0.0f && sample < 450.0f;
        float currentTemp;
        int currentErrors;
        uint8_t currentHealthyReadings;
        bool currentlyAborted;

        portENTER_CRITICAL(&stateMux);
        currentTemp = temp;
        currentErrors = errorReadings;
        currentHealthyReadings = healthyReadings;
        currentlyAborted = abortSignal;
        portEXIT_CRITICAL(&stateMux);

        bool acceptTemperature = false;
        float acceptedTemperature = currentTemp;

        if (plausible) {
            if (!isfinite(currentTemp) || fabsf(sample - currentTemp) <= 20.0f) {
                acceptTemperature = true;
                acceptedTemperature = sample;
                candidateTemp = NAN;
                candidateReadings = 0;
            } else {
                currentErrors++;
                currentHealthyReadings = 0;

                // Do not remain stuck forever after a bad first value. Only
                // resynchronise after three mutually consistent samples.
                if (isfinite(candidateTemp) && fabsf(sample - candidateTemp) <= 5.0f) {
                    candidateTemp = (candidateTemp * candidateReadings + sample) / (candidateReadings + 1);
                    candidateReadings++;
                } else {
                    candidateTemp = sample;
                    candidateReadings = 1;
                }

                if (candidateReadings >= 3) {
                    acceptTemperature = true;
                    acceptedTemperature = candidateTemp;
                    currentHealthyReadings = 2;
                    candidateTemp = NAN;
                    candidateReadings = 0;
                }
            }
        } else {
            currentErrors++;
            currentHealthyReadings = 0;
            candidateTemp = NAN;
            candidateReadings = 0;
        }

        if (acceptTemperature) {
            currentErrors = 0;
            if (currentHealthyReadings < 255) {
                currentHealthyReadings++;
            }
        }

        const bool triggerFailsafe = currentErrors > 20 && !currentlyAborted;
        portENTER_CRITICAL(&stateMux);
        if (acceptTemperature) {
            temp = acceptedTemperature;
        }
        errorReadings = currentErrors;
        healthyReadings = currentHealthyReadings;
        if (triggerFailsafe) {
            abortSignal = true;
            failsafeEventPending = true;
        }
        portEXIT_CRITICAL(&stateMux);

        vTaskDelay(pdMS_TO_TICKS(500));
    }
}


void setup() {

  Serial.begin(115200);
  
  // put your setup code here, to run once:
     Serial.setTimeout(100);

     // Create FreeRTOS Task for temperature reading
    xTaskCreatePinnedToCore(
        TemperatureTask,   // Function
        "TemperatureTask", // Task Name
        2048,              // Stack Size
        NULL,              // Task Parameters
        1,                 // Priority (higher number = higher priority)
        &TempTaskHandle,   // Task Handle
        1                  // Core to run on (0 or 1)
    );


}

void loop() {
  bool reportFailsafe = false;
  portENTER_CRITICAL(&stateMux);
  if (failsafeEventPending) {
    reportFailsafe = true;
    failsafeEventPending = false;
  }
  portEXIT_CRITICAL(&stateMux);
  if (reportFailsafe) {
    Serial.println("Failsafe!");
  }

  if (Serial.available()) {  
    String command = Serial.readStringUntil('\n'); // Read incoming command
    command.trim();  // Remove trailing spaces/newlines

  if (command == "get temp") {
    Serial.println(temp); // Send temp value back
  } 
  else if (command.startsWith("set setpoint ")) {
    String valueStr = command.substring(12);  // Extract number
    relayValue = clampPwm(valueStr.toFloat());  // Convert to float
    
  }
  else if (command.startsWith("get setpoint")) {
    Serial.println(relayValue);
  }
  else if (command.startsWith("set fan ")){
    String valueStr = command.substring(7);  // Extract number
    fanTargetValue = clampPwm(valueStr.toFloat());  // Convert to float

  }else if (command == "get fan"){
    Serial.println(fanValue); // Send temp value back

  }
  else if (command == "hello"){
    Serial.println("popcorn roaster");
  }
  else if (command == "get status"){
    printStatus();
  }
  else if (command == "get info"){
    printInfo();
  }
  else if (command == "reset failsafe"){
    Serial.println(resetFailsafeIfSafe() ? "failsafe reset" : "failsafe reset denied");
  }
}  


  //Safety regulations section:
  float safetyTemp;
  bool safetyAbort;
  portENTER_CRITICAL(&stateMux);
  safetyTemp = temp;
  safetyAbort = abortSignal;
  portEXIT_CRITICAL(&stateMux);

  //Keep fan running until temperature is below 60°C
  if (safetyTemp > 60){
    fanTargetValue = max(fanTargetValue, MIN_SAFE_FAN); //if warmer than 60°C min fanspeed of about 20% = 50
  }

  //while heating minium fan speed is 50/255
  if (relayValue > 0) {
    fanTargetValue = max(fanTargetValue, MIN_SAFE_FAN); //if relay is on fan atleast at 50
  } 

  relayValue = clampPwm(relayValue);
  fanTargetValue = clampPwm(fanTargetValue);

  //This is the failsafe abort signal handling. Do not add fan code code after this
  if (safetyAbort){
    relayValue = PWM_MIN;
    fanTargetValue = FAILSAFE_FAN;
  }

  //Limit Acceleration and Deceleration of Fan to prevent self-destruction
  //Do not place any non-critical fan control code after this
  if (abs(fanValue - fanTargetValue) <= fanMaxAcceleration){
    fanValue = fanTargetValue;
  }

  if (fanValue < fanTargetValue){
    fanValue = fanValue + fanMaxAcceleration;
  }else if (fanValue > fanTargetValue){
    fanValue = fanValue - fanMaxAcceleration;
  }

  // Re-read the latch immediately before touching the hardware so a sensor
  // task transition cannot leave the SSR enabled for another control cycle.
  bool outputAbort;
  portENTER_CRITICAL(&stateMux);
  outputAbort = abortSignal;
  portEXIT_CRITICAL(&stateMux);
  if (outputAbort) {
    relayValue = PWM_MIN;
    fanTargetValue = FAILSAFE_FAN;
  }

  // Hardware-level airflow interlock: never energise the SSR until the
  // measured/ramped fan output has reached the safe threshold.
  appliedRelayValue = (!outputAbort && fanValue >= MIN_SAFE_FAN) ? relayValue : PWM_MIN;
  analogWrite(relayPin, appliedRelayValue);
  analogWrite(fanPin, fanValue);

  delay(delayValue);  //allow the cpu to switch to other tasks
}
