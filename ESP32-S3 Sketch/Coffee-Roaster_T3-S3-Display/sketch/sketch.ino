
#include "TFT_eSPI.h"
#include <max6675.h>
#include <ModbusRtu.h>
unsigned colour = 0xFFFF;
TFT_eSPI tft = TFT_eSPI();
#define topbutton 0
#define lowerbutton 14
#define PIN_POWER_ON 15  // LCD and battery Power Enable
#define PIN_LCD_BL 38    // BackLight enable pin (see Dimming.txt)

uint16_t au16data[16] = {
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, -1 };

Modbus slave(1,0,0); // this is slave @1 and RS-232 or USB-FTDI

int thermoDO = 11;
int thermoCS = 12;
int thermoCLK = 13;

MAX6675 thermocouple(thermoCLK, thermoCS, thermoDO);

int relay = 1;  

uint16_t currentTemp = -1;
int relayValue;

void setup() {

  pinMode(relay, OUTPUT);
  pinMode(PIN_POWER_ON, OUTPUT);  //triggers the LCD backlight
  pinMode(PIN_LCD_BL, OUTPUT);    // BackLight enable pin
  pinMode(lowerbutton, INPUT);    //Right button pulled up, push = 0
  pinMode(topbutton, INPUT);      //Left button  pulled up, push = 0
  delay(100);
  digitalWrite(PIN_POWER_ON, HIGH);
  digitalWrite(PIN_LCD_BL, HIGH);
  Serial.begin(115200);  // be sure to set USB CDC On Boot: "Enabled"
  //(Serial print slows progres bar Demo)
  delay(100);
  tft.init();
  //tft.setRotation(3);
  tft.setRotation(1);
  tft.setSwapBytes(true);
  tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);

  draw_static_text();
  
}

void draw_static_text(){
  tft.fillScreen(TFT_BLACK);  //horiz / vert<> position/dimension

  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  
  tft.drawString("RelayValue:", 10,10, 4);
  tft.drawString("CurrentTemp:", 10, 40, 4);

}

void loop() {

  if (!digitalRead(topbutton)){
   
  }

  if (!digitalRead(lowerbutton)){
  
  }


  //write current thermocouple value
   currentTemp = (uint16_t)thermocouple.readCelsius();


    if (Serial.available()) {
        if (Serial.available()) {
          String command = Serial.readStringUntil('\n'); // Read incoming command
          command.trim();  // Remove trailing spaces/newlines

          if (command == "get temp") {
              Serial.println(currentTemp); // Send temp value back
          } 
          else if (command.startsWith("set setpoint ")) {
              String valueStr = command.substring(12);  // Extract number
              relayValue = valueStr.toFloat();  // Convert to float
            
          }
      }
  }
  
   analogWrite(relay, relayValue);

   
   
   
   //tft.fillScreen(TFT_BLACK);  //horiz / vert<> position/dimension
   tft.fillRect(180, 10, 80, 60, TFT_BLACK);

   tft.drawString(String(relayValue), 180, 10, 4);
   tft.drawString(String(currentTemp) + " C", 180, 40, 4);
  


   delay(100);

  
}
