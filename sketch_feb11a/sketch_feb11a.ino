// #include<LiquidCrystal.h>
#include "DHT.h"
# 

#define DHTPIN 4     // what pin we're connected to
#define DHTTYPE DHT11   // DHT 11 
DHT dht(DHTPIN, DHTTYPE);

// #define echo 9
// #define trigger 10
// #define tank_pump 4
#define watering_pump 13
#define moisture_sensor A0
// #define tempPin A1


// long duration;
// int distance;
int moisture_value;
// int distance_percent;
int moist_percent;
float temp;
float min_threshold;
float max_threshold;
int irrigating;
int rain;
// LiquidCrystal lcd(12,11,8,7,6,5);


float vol = 0.0;
float l_minute = 0.0;
unsigned char flowsensor = 2; // Sensor Input
unsigned long currentTime;
unsigned long cloopTime;
unsigned long flow_frequency;

void flow () // Interrupt function to increment flow
{
  if (irrigating == 1){
   flow_frequency++;
  }
}



//LCD DISPLAY
void setup () {
  dht.begin();
  // lcd.begin(20,4);
  Serial.begin(9600);
  // pinMode(echo,INPUT);
  pinMode(moisture_sensor,INPUT);
  // pinMode(trigger,OUTPUT);
  // digitalWrite(trigger,LOW);
  pinMode(watering_pump,OUTPUT);
  // pinMode(tank_pump,OUTPUT);
  digitalWrite(watering_pump,LOW);
  irrigating = 0;
  rain = 0;
  min_threshold = 20;
  max_threshold = 50;
  ///////////////////

  pinMode(flowsensor, INPUT);
  digitalWrite(flowsensor, HIGH); // Optional Internal Pull-Up
  attachInterrupt(digitalPinToInterrupt(flowsensor), flow, RISING); // Setup Interrupt
  currentTime = millis();
  cloopTime = currentTime;


  // digitalWrite(tank_pump,LOW);
  // lcd.setCursor(0,0);
  // lcd.print("AUTOMATED IRRIGATION");
  // lcd.setCursor(0,1);
  // lcd.print("SYSTEM");
  // lcd.setCursor(0,2);
  // lcd.print("BY-B10 GROUP"); 
  // delay(30);
  // lcd.clear(); 
  // lcd.setCursor(0,0);
  // lcd.print("WELCOME");
  // delay(10);
  // lcd.clear();
}



// WATER LEVEL SENSOR.
void loop(){
  flow_sensor();
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n'); // Read data until newline
    // Serial.println("Received: " + data);      // Print received data

    // Split data into individual values
    int comma1 = data.indexOf(',');
    int comma2 = data.substring(comma1 + 1, -1).indexOf(',');

    if (comma1 != -1 and comma2 != -1) {
      min_threshold = data.substring(0, comma1).toInt();
      rain= data.substring(comma1 + 1, comma2).toInt();
      max_threshold = data.substring(comma2 + 1, -1).toInt();
      // Serial.println(data);
      Serial.print(min_threshold);
      Serial.print(",");
      Serial.print(max_threshold);
      Serial.print(",");
      Serial.println(rain);
    }

  }
  float humidity = dht.readHumidity();
  float temp = dht.readTemperature();

  moisture_value= analogRead(moisture_sensor);
  moist_percent=map(moisture_value,0,1023,0,100);


  condition();

  Serial.print(temp);
  Serial.print(",");
  Serial.print(moist_percent);
  Serial.print(",");
  Serial.print(humidity);
  Serial.print(",");  
  Serial.print(vol);
  Serial.print(",");
  Serial.println(irrigating);
  // delay(10);
  // digitalWrite(trigger,LOW);
  // delayMicroseconds(2);
  // digitalWrite(trigger,HIGH);
  // delayMicroseconds(10); 
  // digitalWrite(trigger,LOW);
  // duration=pulseIn(echo,HIGH);
  // distance=duration*0.017; 
  // distance_percent=map( distance,0,1023,0,100);
  

  delay(500);
}


//MAIN WORKING
void condition(){
  if (moist_percent<min_threshold && rain == 0){
    // LCD_3();
    // digitalWrite(tank_pump,LOW);
    irrigating = 1;
    digitalWrite(watering_pump,HIGH);
    delay(10);
  }
  else if (moist_percent<min_threshold && rain == 1){
    // LCD_3();
    // digitalWrite(tank_pump,LOW);
    irrigating = 0;
    digitalWrite(watering_pump,LOW);
    delay(10);
  }
  else if (moist_percent>max_threshold){
    // LCD_2();
    // digitalWrite(tank_pump,HIGH);
    irrigating = 0;
    digitalWrite(watering_pump,LOW);
    delay(10);
  }

  // else if (moist_percent>85)
  // {
  // // LCD_4();
  // // digitalWrite(tank_pump,LOW);
  // digitalWrite(watering_pump,LOW);
  // delay(10);
  // }

  // else if (moist_percent<85)
  // {
  // // LCD_1();
  // // digitalWrite(tank_pump,HIGH);
  // digitalWrite(watering_pump,HIGH);
  // delay(10);
  // }
}



void flow_sensor(){
   currentTime = millis();
   // Every second, calculate and print litres/hour
   if(currentTime >= (cloopTime + 1000))
   {
    cloopTime = currentTime; // Updates cloopTime
    if(flow_frequency != 0)
    {
      
      l_minute = (flow_frequency / 7.5); // (Pulse frequency x 60 min) / 7.5Q = flowrate in L/hour
      
      l_minute = l_minute/60;
      
      vol = vol +l_minute;
      
      flow_frequency = 0; // Reset Counter
      // Serial.print(l_minute, DEC); // Print litres/hour
      // Serial.println(" L/Sec");
      // Serial.print(vol);
      // Serial.println(" L");
    }
    else {
      // Serial.println("flow rate = 0 ");

    }
   }
}







//DIFFRENT LCD DISPLAY FUNCTIONS
// void LCD_1(){
  // lcd.clear();
  // lcd.setCursor(0,0);
  // lcd.print("TANK LEVEL= ");
  // lcd.print(distance_percent);
  // lcd.print("%");
  // lcd.setCursor(0,1);
  // lcd.print("MOISTURE STATUS= ");
  // lcd.print(moist_percent);
  // lcd.print("%");
  // lcd.setCursor(0,2);
  // lcd.print("WATER PUMP:");
  // lcd.print("ON");
  // lcd.setCursor(0,3);
  // lcd.print("TANK PUMP:");
  // lcd.print("ON");
// }

// void LCD_2(){
  // lcd.clear();
  // lcd.setCursor(0,0);
  // lcd.print("TANK LEVEL= ");
  // lcd.print(distance_percent);
  // lcd.print("%");
  // lcd.setCursor(0,1);
  // lcd.print("MOISTURE STATUS= ");
  // lcd.print(moist_percent);
  // lcd.print("%");
  // lcd.setCursor(0,2);
  // lcd.print("WATER PUMP:");
  // lcd.print("OFF");
  // lcd.setCursor(0,3);
  // lcd.print("TANK PUMP:");
  // lcd.print("ON");
// }
  
// void LCD_3(){
  // lcd.clear();
  // lcd.setCursor(0,0);
  // lcd.print("TANK LEVEL= ");
  // lcd.print(distance_percent);
  // lcd.print("%");
  // lcd.setCursor(0,1);
  // lcd.print("MOISTURE STATUS= ");
  // lcd.print(moist_percent);
  // lcd.print("%");
  // lcd.setCursor(0,2);
  // lcd.print("WATER PUMP:");
  // lcd.print("ON");
  // lcd.setCursor(0,3);
  // lcd.print("TANK PUMP:");
  // lcd.print("OFF");
// }

// void LCD_4(){
  // lcd.clear();
  // lcd.setCursor(0,0);
  // lcd.print("TANK LEVEL= ");
  // lcd.print(distance_percent);
  // lcd.print("%");
  // lcd.setCursor(0,1);
  // lcd.print("MOISTURE STATUS= ");
  // lcd.print(moist_percent);
  // lcd.print("%");
  // lcd.setCursor(0,2);
  // lcd.print("WATER PUMP:");
  // lcd.print("OFF");
  // lcd.setCursor(0,3);
  // lcd.print("TANK PUMP:");
  // lcd.print("OFF");
// }
