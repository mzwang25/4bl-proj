//Includes the Arduino Stepper Library
#include <Stepper.h>
#include "odedata.h"
 
// Defines the number of steps per rotation
const int stepsPerRevolution = 512;
 
// Creates an instance of stepper class
// Pins entered in sequence IN1-IN3-IN2-IN4 for proper step sequence
Stepper myStepper = Stepper(stepsPerRevolution, 8, 10, 9, 11);
 
void setup() {
  // Nothing to do (Stepper Library sets pins as outputs)
  Serial.begin(115200);
}
 
int getSpeed(int Hz){
  return round(60.0*Hz/stepsPerRevolution);  
}
 
int getStep(int motorSpeed, double duration){
  return round((double)motorSpeed*stepsPerRevolution*duration/60);
}

int counter = 0;

void loop() {
  if(counter >= LENGTH)
    counter = 0;
    
  int currentHz = FREQUENCIES[counter++];
  Serial.println(currentHz);
  
  if(currentHz != 0) {  
    const double halfNoteRatio = 1.05946309436;
    // go from 440 to 1760 Hz, one per each half note, each lasting 1 sec
    int speed = getSpeed(currentHz);
    int steps = getStep(speed, 0.5);
    myStepper.setSpeed(speed);
    myStepper.step(steps);
  }

}
