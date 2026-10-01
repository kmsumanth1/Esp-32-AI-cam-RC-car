# 🚗 ESP32 AI CAM RC Car 🤖

An **AI-powered Wi-Fi controlled RC car** built using an **ESP32-CAM and Arduino UNO**, combining real-time camera streaming, wireless vehicle control, and AI-based object detection.

The system allows the user to control the RC car remotely through Wi-Fi while using the ESP32-CAM to capture live video and identify objects in the environment.

---

## 🌟 Project Overview

The **ESP32 AI CAM RC Car** is a smart robotic vehicle designed to combine traditional RC-car functionality with computer vision and artificial intelligence.

The **ESP32-CAM** acts as the vision and wireless communication unit, while the **Arduino UNO** handles motor-control operations through the motor driver.

The project can be extended with AI capabilities such as:

- 👁️ Real-time object detection
- 🚧 Obstacle detection
- 🎥 Live camera streaming
- 📱 Wi-Fi-based remote control
- 🧠 AI-assisted navigation
- 🚗 Automatic movement based on detected objects
- 🎯 Object identification
- 🛑 Intelligent stopping when an object is detected

---

## ✨ Features

### 🎮 Remote RC Control

Control the vehicle wirelessly through a web interface.

Supported movements:

- ⬆️ Forward
- ⬇️ Backward
- ⬅️ Left
- ➡️ Right
- 🛑 Stop
- ⚡ Speed control

### 📷 ESP32-CAM Live Streaming

The ESP32-CAM provides a live camera feed that allows the user to monitor the surroundings of the vehicle.

### 🤖 AI Object Detection

The project integrates computer vision/AI concepts to detect objects captured by the camera.

Potential detection tasks include:

- People
- Vehicles
- Animals
- Obstacles
- Common objects

The detected objects can be used to make intelligent decisions for the vehicle.

### 📡 Wi-Fi Connectivity

The ESP32 provides wireless connectivity, allowing the RC car to be controlled from a smartphone, laptop, or other Wi-Fi-enabled device.

### 🧠 Intelligent Vehicle Control

AI detection can be integrated with the movement system to create autonomous behaviors.

For example:

```text
Camera
   ↓
Image Capture
   ↓
AI Object Detection
   ↓
Object Detected?
   ↓
Decision Making
   ↓
Arduino UNO
   ↓
Motor Driver
   ↓
DC Motors
```

---

# 🏗️ System Architecture

```text
                 ┌──────────────────────┐
                 │      Smartphone      │
                 │   / Laptop Browser   │
                 └──────────┬───────────┘
                            │
                         Wi-Fi
                            │
                            ▼
                 ┌──────────────────────┐
                 │      ESP32-CAM       │
                 │                      │
                 │ • Camera             │
                 │ • Wi-Fi              │
                 │ • Video Streaming    │
                 │ • Object Detection   │
                 └──────────┬───────────┘
                            │
                     Control Signals
                            │
                            ▼
                 ┌──────────────────────┐
                 │      Arduino UNO     │
                 │                      │
                 │ • Motor Control      │
                 │ • Direction Control  │
                 │ • PWM Speed Control  │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │      L298N Driver    │
                 │                      │
                 │ • Motor A            │
                 │ • Motor B            │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │      DC Motors       │
                 │                      │
                 │    🚗 RC Vehicle     │
                 └──────────────────────┘
```

---

# 🔧 Hardware Components

| Component | Purpose |
|---|---|
| ESP32-CAM | Camera, Wi-Fi and vision system |
| Arduino UNO | Motor and vehicle control |
| L298N Motor Driver | Drives the DC motors |
| 4WD Robot Car Chassis | Vehicle platform |
| DC Gear Motors | Vehicle movement |
| Battery | Power source |
| Jumper Wires | Electrical connections |
| Breadboard | Prototyping and connections |

---

# 💻 Software & Technologies

- **Arduino IDE**
- **C/C++**
- **ESP32**
- **Arduino UNO**
- **ESP32-CAM**
- **Wi-Fi**
- **Computer Vision**
- **Artificial Intelligence**
- **Object Detection**
- **Embedded Systems**
- **PWM Motor Control**
- **Web-based Control Interface**

---

# 📁 Project Structure

```text
Esp-32-AI-cam-RC-car/
│
├── ESP32-CAM/
│   └── esp32_cam.ino
│
├── Arduino-UNO/
│   └── motor_control.ino
│
├── web-interface/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── AI/
│   └── object_detection/
│
├── images/
│
├── README.md
│
└── LICENSE
```

> The actual folder structure may differ depending on your implementation.

---

# 🔌 Hardware Connection

The basic architecture is:

```text
ESP32-CAM
    │
    │ Control / Communication
    ▼
Arduino UNO
    │
    │ Motor Signals
    ▼
L298N Motor Driver
    │
    ├──────── Motor 1
    │
    └──────── Motor 2
```

The **L298N motor driver** is responsible for supplying the required current to the motors while the Arduino provides the control signals.

> ⚠️ Do not power the motors directly from the Arduino UNO or ESP32-CAM GPIO pins.

---

# 🚀 How It Works

### Step 1 — Start the System

Power the ESP32-CAM, Arduino UNO, motor driver, and vehicle.

### Step 2 — Establish Wi-Fi Connection

The ESP32-CAM connects to the configured Wi-Fi network.

### Step 3 — Open the Control Interface

The user accesses the RC car's web interface using a smartphone or computer.

### Step 4 — Control the Vehicle

Commands such as:

```text
FORWARD
BACKWARD
LEFT
RIGHT
STOP
```

are sent to the vehicle.

### Step 5 — Camera Streaming

The ESP32-CAM captures images/video and provides a live view.

### Step 6 — AI Object Detection

The camera frames can be processed by an AI/computer-vision model.

Example:

```text
Camera Frame
     ↓
Image Preprocessing
     ↓
AI Model
     ↓
Object Detection
     ↓
Bounding Box + Class
     ↓
Decision
```

### Step 7 — Intelligent Action

Depending on the detected object, the vehicle can perform an action.

For example:

```text
Object detected
       ↓
Is object too close?
       ↓
      YES
       ↓
     STOP
```

---

# 🧠 AI Object Detection

The AI component can be used to detect objects in the camera feed.

A typical detection result can contain:

```text
Object: Person
Confidence: 94%
Bounding Box: (x, y, width, height)
```

The detection information can then be used by the vehicle-control system.

### Example AI Behavior

```text
             Camera
                │
                ▼
       ┌─────────────────┐
       │ Object Detection│
       └────────┬────────┘
                │
          ┌─────┴─────┐
          │           │
       Detected    Nothing
          │           │
          ▼           ▼
       Analyze     Continue
       Distance    Movement
          │
          ▼
    Too Close?
       /    \
     YES     NO
      │       │
      ▼       ▼
    STOP    Continue
```

---

# 📱 Control Interface

The web interface can provide controls such as:

```text
        ┌───────────┐
        │     ▲     │
        │  Forward  │
        └───────────┘

┌──────────┐ ┌──────────┐ ┌──────────┐
│    ◀     │ │   STOP   │ │    ▶     │
│   LEFT   │ │    🛑    │ │  RIGHT   │
└──────────┘ └──────────┘ └──────────┘

        ┌───────────┐
        │     ▼     │
        │ Backward  │
        └───────────┘
```

The interface can also display the live ESP32-CAM video stream.

---

# 🔐 Safety Considerations

- Do not connect motors directly to ESP32 or Arduino GPIO pins.
- Use a suitable external power supply for the motors.
- Ensure the motor-driver ground and controller ground are connected appropriately.
- Check the voltage requirements of the ESP32-CAM before powering it.
- Avoid short circuits when experimenting with the battery and motor driver.
- Test the motors with the vehicle lifted from the ground before the first complete run.

---

# 🔮 Future Improvements

The project can be expanded into a more autonomous AI robot.

Possible improvements include:

- 🧠 Advanced object detection
- 🚧 Automatic obstacle avoidance
- 🗺️ Autonomous navigation
- 👤 Person tracking
- 🎯 Object tracking
- 🚦 Traffic-sign detection
- 🛣️ Lane detection
- 🧭 Path planning
- 📍 GPS integration
- 🎤 Voice-controlled movement
- 📱 Mobile application
- ☁️ Cloud-based monitoring
- 📊 Telemetry dashboard
- 🔋 Battery monitoring
- 🤖 Fully autonomous driving

---

# 🎯 Applications

This project demonstrates concepts applicable to:

- Autonomous robotics
- Computer vision
- AI-powered vehicles
- Smart surveillance robots
- Remote inspection systems
- Educational robotics
- IoT robotics
- Autonomous navigation
- Embedded AI

---

# 📚 Learning Outcomes

Through this project, the following concepts can be explored:

- ESP32 programming
- Arduino programming
- Embedded systems
- Wi-Fi communication
- Web-based IoT control
- Motor control
- PWM
- Computer vision
- Object detection
- AI integration
- Robotics
- Hardware-software integration

---

# 👨‍💻 Author

**KM Sumanth**

B.Tech — Computer Science & Engineering (AI & ML)

GitHub:  
https://github.com/kmsumanth1

---

# ⭐ Project Goal

The ultimate goal of this project is to transform a conventional RC car into an **AI-assisted robotic vehicle** capable of seeing its surroundings, detecting objects, receiving wireless commands, and eventually making intelligent navigation decisions.

> 🚗 + 📷 + 🤖 + 📡 = **AI-Powered Smart RC Car**

---

