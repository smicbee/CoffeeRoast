#include <max6675.h>
#include <math.h>
//#include "PIDController.h"

int thermoDO = 11;
int thermoCS = 12;
int thermoCLK = 13;

// FreeRTOS Task Handle
TaskHandle_t TempTaskHandle;
MAX6675 thermocouple(thermoCLK, thermoCS, thermoDO);

int temp = 0;

int fanPin = 2;
int relayPin = 1;
float relayValue = 0;
float fanTargetValue = 0;
float fanValue = 0;

double fanMaxAcceleration = 2.0; //max acceleration per cycle

const float PWM_MIN = 0.0f;
const float PWM_MAX = 255.0f;
const float MIN_SAFE_FAN = 50.0f;
const float FAILSAFE_FAN = PWM_MAX;

int errorReadings = 0;
int delayValue = 50;


bool autoRunMode = true;
unsigned long StartTime = millis(); 
//double profile[800];
bool abortSignal = false;
bool disableFailsafe = false;

uint16_t readTemperature() {
    return (uint16_t)thermocouple.readCelsius();
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
  Serial.print(relayValue);
  Serial.print(",fan=");
  Serial.print(fanValue);
  Serial.print(",fanTarget=");
  Serial.print(fanTargetValue);
  Serial.print(",errors=");
  Serial.println(errorReadings);
}

// FreeRTOS Task: Reads temperature every 500ms
void TemperatureTask(void *parameter) { 
    uint16_t tempTemp = 1;
    temp = tempTemp;
    while (1) {
        
        tempTemp = readTemperature();
        
        //Serial.println(temp);
        //Serial.println(tempTemp);


        if (temp == 1){
          temp = tempTemp;
        }

        if (tempTemp > 0){
          if (abs(tempTemp - temp) > 20){
           errorReadings = errorReadings + 1;
          }else{
          temp = tempTemp;
          errorReadings = 0;
          abortSignal = false;
          }

        }else{
          errorReadings = errorReadings + 1;
        }

        if (errorReadings > 20 && !disableFailsafe){
          abortSignal = true;
          Serial.println("Failsafe!");
        }else{
          abortSignal = false;
        }

        vTaskDelay(pdMS_TO_TICKS(500)); // Wait for 500ms
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
    fanValue = FAILSAFE_FAN;
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

  analogWrite(relayPin, relayValue);
  analogWrite(fanPin, fanValue);

  delay(delayValue);  //allow the cpu to switch to other tasks
}
