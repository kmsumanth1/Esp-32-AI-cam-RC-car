/*
 * Arduino Uno motor controller (L298N dual H-bridge)
 *
 * Receives "<dir>,<speed>\n" from the ESP32-CAM on D2 (SoftwareSerial, 9600 baud):
 *   F forward   B backward   L turn left (in place)   R turn right (in place)   S stop
 * speed is 0-255 (PWM).
 *
 * Failsafe: if no valid command arrives for FAILSAFE_MS the motors stop. The web
 * dashboard resends the active command every ~150 ms, so releasing a button, losing
 * Wi-Fi or crashing the server all stop the car within half a second.
 */
#include <SoftwareSerial.h>

// Link from ESP32-CAM GPIO14
const uint8_t LINK_RX_PIN = 2;
const uint8_t LINK_TX_PIN = 3;  // unused
SoftwareSerial link(LINK_RX_PIN, LINK_TX_PIN);

// L298N: left motor on A, right motor on B. Remove the ENA/ENB jumpers.
const uint8_t ENA = 5;  // PWM
const uint8_t IN1 = 7;
const uint8_t IN2 = 8;
const uint8_t ENB = 6;  // PWM
const uint8_t IN3 = 9;
const uint8_t IN4 = 10;

const unsigned long FAILSAFE_MS = 500;
unsigned long lastCommandAt = 0;

char line[16];
uint8_t lineLen = 0;

void setSide(uint8_t en, uint8_t a, uint8_t b, int v) {
  v = constrain(v, -255, 255);
  if (v > 0) {
    digitalWrite(a, HIGH);
    digitalWrite(b, LOW);
  } else if (v < 0) {
    digitalWrite(a, LOW);
    digitalWrite(b, HIGH);
  } else {
    digitalWrite(a, LOW);
    digitalWrite(b, LOW);
  }
  analogWrite(en, abs(v));
}

void drive(int left, int right) {
  setSide(ENA, IN1, IN2, left);
  setSide(ENB, IN3, IN4, right);
}

void handleCommand(const char *cmd) {
  // Expected shape: X,NNN
  if (cmd[0] == '\0' || cmd[1] != ',') return;
  int speed = constrain(atoi(cmd + 2), 0, 255);

  switch (cmd[0]) {
    case 'F': drive(speed, speed); break;
    case 'B': drive(-speed, -speed); break;
    case 'L': drive(-speed, speed); break;
    case 'R': drive(speed, -speed); break;
    case 'S': drive(0, 0); break;
    default: return;  // ignore anything else (e.g. ESP32 boot text)
  }
  lastCommandAt = millis();
}

void setup() {
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);
  drive(0, 0);

  Serial.begin(115200);  // USB debug
  link.begin(9600);
  lastCommandAt = millis();
}

void loop() {
  while (link.available()) {
    char ch = link.read();
    if (ch == '\n') {
      line[lineLen] = '\0';
      handleCommand(line);
      lineLen = 0;
    } else if (ch != '\r' && lineLen < sizeof(line) - 1) {
      line[lineLen++] = ch;
    }
  }

  if (millis() - lastCommandAt > FAILSAFE_MS) {
    drive(0, 0);
  }
}
