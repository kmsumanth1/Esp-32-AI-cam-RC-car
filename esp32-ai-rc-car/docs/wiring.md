# Wiring

## Signal wiring

| From                    | To                      | Purpose                          |
| ----------------------- | ----------------------- | -------------------------------- |
| ESP32-CAM GPIO14 (TX)   | Arduino Uno D2 (RX)     | Drive commands, 9600 baud        |
| ESP32-CAM GND           | Arduino Uno GND         | Common ground (required)         |
| Uno D5                  | L298N ENA               | Left motor speed (PWM)           |
| Uno D7                  | L298N IN1               | Left motor direction             |
| Uno D8                  | L298N IN2               | Left motor direction             |
| Uno D6                  | L298N ENB               | Right motor speed (PWM)          |
| Uno D9                  | L298N IN3               | Right motor direction            |
| Uno D10                 | L298N IN4               | Right motor direction            |
| Uno GND                 | L298N GND               | Common ground                    |

Only one signal wire crosses between the boards (ESP32 TX to Uno RX), and it is 3.3 V into a
5 V input, which the Uno reads as HIGH, so no level shifter is needed. If you ever add a
Uno-to-ESP32 wire, use a voltage divider (the Uno's 5 V can damage the ESP32's 3.3 V pins).

## Power

- L298N: battery pack (7-12 V) to the 12V terminal. **Remove the ENA and ENB jumpers** so the
  Uno's PWM pins control speed.
- Arduino Uno: powered from the L298N 5V output or its own USB/battery supply.
- ESP32-CAM: give it a **stable 5 V supply that can deliver 500 mA or more**. Powering it from the
  Uno's 5V pin or straight from the motor supply is the most common cause of random resets
  ("brownouts") when the motors start. A separate 5 V regulator with a 100-470 uF capacitor
  close to the module fixes it.

## Flashing

- **ESP32-CAM:** use an ESP32-CAM-MB programmer board, or an FTDI adapter with GPIO0 tied to
  GND during upload (remove it and press reset afterwards). Board: "AI Thinker ESP32-CAM".
  Disconnect GPIO14 from the Uno if uploads fail.
- **Arduino Uno:** normal USB upload. Board: "Arduino Uno".

Add photos of your build and a wiring diagram to this folder, plus a short demo GIF.
