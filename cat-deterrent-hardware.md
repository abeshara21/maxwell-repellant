# Cat Deterrent Prototype – Hardware & Development Plan

**Project Goal**: Raspberry Pi-based system that detects a cat in a designated area and aims a water jet at it.

**Current Phase**: Basic manual hardware control  
**Next Phase**: Object detection (camera + vision)  
**Future Phase**: Closed-loop aiming (cat position as feedback)

---

## Hardware Bill of Materials (Recommended 12V Pump Version)

| Component | Specification / Notes | Purpose |
|-----------|-----------------------|---------|
| Raspberry Pi | Any modern model (Pi 4/5 recommended) with CSI port | Main controller |
| Raspberry Pi Camera Module V2 | 8MP IMX219, CSI ribbon | Vision / object detection |
| PCA9685 Servo Driver | 16-channel I2C PWM | Clean servo control + current isolation |
| Micro Servos | 2× MG90S (or SG90) | Pan + Tilt |
| Pan-Tilt Bracket | Plastic 2-axis kit for 9g servos | Mechanical aiming platform |
| 12V Diaphragm Pump | ~0.48 MPa, self-priming | Water jet |
| 1-Channel Relay Module | 5V logic, optocoupler, low-level trigger | Switch 12V pump |
| Power Supply | Arcity multi-output: +5V/8A, +12V/8A | Powers everything from one unit |
| Tubing | 8 mm ID silicone | From pump to nozzle |
| Nozzle | Adjustable jet nozzle for 8 mm ID tube | Solid stream (not mist) |
| Misc | Jumper wires, capacitor (100–470 µF), mounting hardware | — |

---

## Wiring Summary

### Power
- **PSU +5V** → Raspberry Pi (5V pin or USB-C), PCA9685 VCC (logic), PCA9685 V+ (servo power), Relay VCC
- **PSU +12V** → Relay COM
- **Common Ground**: PSU GND, Pi GND, PCA9685 GND, Relay GND, Pump negative

### Control Signals
| From | To | Pin / Channel | Notes |
|------|----|---------------|-------|
| Pi GPIO 2 (SDA) | PCA9685 SDA | I2C | Servo driver |
| Pi GPIO 3 (SCL) | PCA9685 SCL | I2C | Servo driver |
| Pi GPIO 17 | Relay IN | Digital | Pump on/off |
| PCA9685 Ch 0 | Pan Servo | PWM | Horizontal |
| PCA9685 Ch 1 | Tilt Servo | PWM | Vertical |
| Relay NO | Pump + | — | Pump only runs when relay is activated |
| CSI Port | Camera Module V2 | Ribbon | Camera |

**Important**:
- Servos are powered from PCA9685 V+ (external 5V), **not** from the Pi’s 5V pin.
- Add a 100–470 µF capacitor across the servo power rails near the PCA9685.
- Use 16–18 AWG for the 12V pump circuit.

---

## Software Development Roadmap

### Phase 1 – Basic Manual Control (Start Here)
Goal: Full manual control of pan, tilt, and water burst via keyboard or simple terminal commands.

**Recommended Libraries**:
- `adafruit-circuitpython-pca9685` or `adafruit-circuitpython-servokit`
- `RPi.GPIO` or `gpiozero` for the relay
- Optional: `picamera2` (for later camera work)

**Suggested File Structure**:
```
cat-deterrent/
├── hardware/
│   ├── servo_controller.py      # PCA9685 pan/tilt
│   ├── pump_controller.py       # Relay control
│   └── config.py                # Pins, channels, limits
├── manual_control.py            # Keyboard / terminal interface
├── requirements.txt
└── README.md
```

**Initial Features**:
- Arrow keys or WASD → move pan/tilt
- Spacebar → short water burst
- Safety limits on servo angles
- Clean shutdown on Ctrl+C

### Phase 2 – Object Detection
- Enable Pi Camera with `picamera2`
- Run a lightweight detector (e.g. MobileNet-SSD, YOLOv8n, or a simple cat-specific model)
- Output bounding box center (x, y) in image coordinates

### Phase 3 – Closed-Loop Aiming
- Map image coordinates → desired pan/tilt angles
- Simple proportional (or PID) control loop
- Only fire water when the cat is centered within a deadband
- Optional: continuous tracking while cat is in frame

---

## Configuration Constants (Suggested)

```python
# config.py
SERVO_PAN_CHANNEL = 0
SERVO_TILT_CHANNEL = 1
RELAY_PIN = 17

PAN_MIN = 10
PAN_MAX = 170
TILT_MIN = 30
TILT_MAX = 150

PUMP_BURST_DURATION = 0.5  # seconds
```

---

## Notes for Cursor
- Start by implementing Phase 1 only.
- Keep hardware control in separate classes so object detection and control loops can be added later without rewriting the low-level code.
- Use type hints and clear docstrings — this will help Cursor generate the next phases cleanly.
- Test servo movement and pump independently before combining them.

---

**Status**: Hardware defined, schematic confirmed, ready for Phase 1 (manual control) implementation.
