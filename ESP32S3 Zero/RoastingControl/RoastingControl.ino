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

int fanPin = 2;
int relayPin = 1;
float relayValue = 0;
float appliedRelayValue = 0;
float fanTargetValue = 0;
float fanValue = 0;

double fanMaxAcceleration = 2.0; //max acceleration per cycle

const float PWM_MIN = 0.0f;
const float PWM_MAX = 255.0f;
const float MIN_SAFE_FAN = 50.0f;
const float FAILSAFE_FAN = PWM_MAX;
const char* FIRMWARE_VERSION = "1.2.0";
const uint8_t PROTOCOL_VERSION = 2;
const char* HARDWARE_ID = "CoffeeRoast-RevA-ESP32S3-WROOM-1-N8R8";

int errorReadings = 0;
int delayValue = 50;


bool autoRunMode = true;
unsigned long StartTime = millis(); 
//double profile[800];
bool abortSignal = false;
bool disableFailsafe = false;

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
  Serial.print("state=");
  Serial.print(abortSignal ? "failsafe" : "ok");
  Serial.print(",temp=");
  Serial.print(temp);
  Serial.print(",heater=");
  Serial.print(appliedRelayValue);
  Serial.print(",fan=");
  Serial.print(fanValue);
  Serial.print(",fanTarget=");
  Serial.print(fanTargetValue);
  Serial.print(",errors=");
  Serial.print(errorReadings);
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

// FreeRTOS Task: Reads temperature every 500ms
void TemperatureTask(void *parameter) {
    float candidateTemp = NAN;
    uint8_t candidateReadings = 0;

    while (1) {
        const float sample = readTemperature();
        const bool plausible = isfinite(sample) && sample > 0.0f && sample < 450.0f;

        if (plausible) {
            if (!isfinite(temp) || fabsf(sample - temp) <= 20.0f) {
                temp = sample;
                candidateTemp = NAN;
                candidateReadings = 0;
                errorReadings = 0;
            } else {
                errorReadings++;

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
                    temp = candidateTemp;
                    candidateTemp = NAN;
                    candidateReadings = 0;
                    errorReadings = 0;
                }
            }
        } else {
            errorReadings++;
            candidateTemp = NAN;
            candidateReadings = 0;
        }

        if (errorReadings > 20 && !disableFailsafe) {
            abortSignal = true;
            Serial.println("Failsafe!");
        } else {
            abortSignal = false;
        }

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
  else if (command == "disable failsafe"){
    disableFailsafe = true;
  }
}  


  //Safety regulations section:

  //Keep fan running until temperature is below 60°C
  if (temp > 60){
    fanTargetValue = max(fanTargetValue, MIN_SAFE_FAN); //if warmer than 60°C min fanspeed of about 20% = 50
  }

  //while heating minium fan speed is 50/255
  if (relayValue > 0) {
    fanTargetValue = max(fanTargetValue, MIN_SAFE_FAN); //if relay is on fan atleast at 50
  } 

  relayValue = clampPwm(relayValue);
  fanTargetValue = clampPwm(fanTargetValue);

  //This is the failsafe abort signal handling. Do not add fan code code after this
  if (abortSignal == true){
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

  // Hardware-level airflow interlock: never energise the SSR until the
  // measured/ramped fan output has reached the safe threshold.
  appliedRelayValue = (!abortSignal && fanValue >= MIN_SAFE_FAN) ? relayValue : PWM_MIN;
  analogWrite(relayPin, appliedRelayValue);
  analogWrite(fanPin, fanValue);

  delay(delayValue);  //allow the cpu to switch to other tasks
}
