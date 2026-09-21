#include <Servo.h>

// -------------------------------------
// Create two servo objects
// myServo  = vertical axis (Y)
// myServo2 = horizontal axis (X)
// -------------------------------------
Servo myServo;
Servo myServo2;

// Current servo positions (start centered)
int servoPos = 90;
int servoPos2 = 90;

// --------------------------------------
// Servo movement limits
// These protect the SG90 from hitting its mechanical stops
// --------------------------------------
const int SERVO_MIN = 40;   // vertical min
const int SERVO_MAX = 140;  // vertical max

const int SERVO_MIN2 = 40;  // horizontal min
const int SERVO_MAX2 = 140; // horizontal max

// Buffer to store incoming serial command
String input = "";

void setup() {
  Serial.begin(9600);

  // --------------------------------------
  // Attach servos to pins
  // myServo  -> pin 7  (vertical)
  // myServo2 -> pin 6  (horizontal)
  // --------------------------------------
  myServo.attach(7);
  myServo.write(servoPos);

  myServo2.attach(6);
  myServo2.write(servoPos2);
}

void loop() {
  // --------------------------------------
  // Read serial input one character at a time
  // Commands look like:  X120\n   or   Y85\n
  // --------------------------------------
  while (Serial.available()) {
    char c = Serial.read();

    // End of command → process it
    if (c == '\n') {
      processCommand(input);
      input = "";  // clear buffer
    } 
    else {
      // Build the command string
      input += c;
    }
  }
}

// --------------------------------------
// Process a full command such as "X120" or "Y85"
// axis = first character ('X' or 'Y')
// value = number after the axis
// --------------------------------------
void processCommand(String cmd) {
  char axis = cmd.charAt(0);          // 'X' or 'Y'
  int value = cmd.substring(1).toInt(); // convert number part to int

  // --------------------------------------
  // Horizontal servo (myServo2)
  // --------------------------------------
  if (axis == 'X') {
    // Keep movement inside safe limits
    value = constrain(value, SERVO_MIN2, SERVO_MAX2);
    myServo2.write(value);
  }

  // --------------------------------------
  // Vertical servo (myServo)
  // --------------------------------------
  if (axis == 'Y') {
    // Keep movement inside safe limits
    value = constrain(value, SERVO_MIN, SERVO_MAX);
    myServo.write(value);
  }
}
