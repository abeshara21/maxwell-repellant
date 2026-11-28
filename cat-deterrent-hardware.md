# Cat Deterrent Prototype – Hardware & Development Plan

**Project Goal**: Raspberry Pi-based system that detects a cat in a designated area and aims a water jet at it.

**Current Phase**: Object detection (camera + vision) and training clip capture  
**Also available**: Phase 1 manual hardware control (when servos/pump are wired)  
**Future Phase**: Closed-loop aiming (cat position as feedback)

---

## Platform Strategy (Prototype → Production)

| Stage | Board | Role |
|-------|--------|------|
| **Prototype (now)** | **Raspberry Pi 3** | Bench wiring, Phase 1 manual control, light Phase 2 experiments |
| **Production (later)** | **Raspberry Pi 4 or 5** | Faster inference, higher resolution, 24/7-style reliability |

**Same codebase for both.** GPIO header pins, I2C (PCA9685), relay on GPIO 17, and CSI camera ribbon layout are compatible across Pi 3 / 4 / 5. Application logic should not hard-code a board model — use `hardware/platform.py` for profile-specific defaults (especially vision in Phase 2+).

**Optional override** (e.g. testing production presets on a Pi 3):

```bash
export CAT_DETERRENT_PROFILE=prototype   # or production
```

### Pi 3 prototype notes

- Use a **5 V / 2.5 A+** supply (micro-USB on Pi 3). Power servos from the **external PSU** on PCA9685 V+, not from the Pi.
- Camera Module V2 on the **CSI** port works on Pi 3; prefer **Raspberry Pi OS (Bullseye or newer)** for `picamera2` in Phase 2.
- Expect **lower FPS** and smaller detector input sizes on Pi 3; tune in `platform.py` (`suggested_detector`, `detector_input_size`).

### Pi 4/5 production notes

- Prefer **Pi 4 (2 GB+)** or **Pi 5** for Phase 2–3 (larger models, optional higher camera resolution).
- USB-C power on Pi 4/5; same peripheral wiring as prototype.

---

## Hardware Bill of Materials (Recommended 12V Pump Version)

| Component | Specification / Notes | Purpose |
|-----------|-----------------------|---------|
| Raspberry Pi | **Pi 3** for prototype; **Pi 4/5** for final build (CSI port required) | Main controller |
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
- **PSU +5V** → Raspberry Pi (GPIO 5V pin or official PSU), PCA9685 VCC (logic), PCA9685 V+ (servo power), Relay VCC  
  *(Pi 3: micro-USB from adequate 5 V supply; Pi 4/5: USB-C.)*
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

## Software Architecture (Upgradable)

Design rules so moving from Pi 3 → Pi 4/5 does not require rewrites:

1. **`hardware/config.py`** — pins, servo channels, angle limits, burst timing only (no board-specific logic).
2. **`hardware/platform.py`** — board detection, `prototype` vs `production` profile, Phase 2+ vision defaults.
3. **`hardware/servo_controller.py` / `pump_controller.py`** — hardware IO only; mockable for off-Pi dev.
4. **Phase 2+** — camera + detector modules read `get_platform()` for resolution/model choice; control loop stays unchanged.

**Suggested File Structure**:
```
cat-deterrent/
├── hardware/
│   ├── config.py                # Pins, channels, limits
│   ├── platform.py              # Pi 3 vs 4/5 profiles
│   ├── servo_controller.py      # PCA9685 pan/tilt
│   └── pump_controller.py       # Relay control
├── manual_control.py            # Phase 1 UI
├── requirements.txt
├── README.md
└── RASPBERRY-PI-RUN-AND-TEST.md
```

---

## Software Development Roadmap

### Phase 1 – Basic Manual Control (Start Here)
Goal: Full manual control of pan, tilt, and water burst via keyboard or simple terminal commands.

**Recommended Libraries**:
- `adafruit-circuitpython-pca9685` or `adafruit-circuitpython-servokit`
- `gpiozero` for the relay
- Optional later: `picamera2` (Phase 2; supported on Pi 3 with current Raspberry Pi OS)

**Initial Features**:
- Arrow keys or WASD → move pan/tilt
- Spacebar → short water burst
- Safety limits on servo angles
- Clean shutdown on Ctrl+C

### Phase 2 – Object Detection
- Enable Pi Camera with `picamera2`
- **Prototype (Pi 3)**: lightweight detector, ~320px input (see `platform.py`)
- **Production (Pi 4/5)**: YOLOv8n or larger, higher resolution if needed
- Output bounding box center (x, y) in image coordinates

### Phase 3 – Closed-Loop Aiming
- Map image coordinates → desired pan/tilt angles
- Simple proportional (or PID) control loop
- Only fire water when the cat is centered within a deadband
- Optional: continuous tracking while cat is in frame

---

## Configuration Constants (Suggested)

```python
# config.py — same on Pi 3 and Pi 4/5
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
- Do **not** branch on Pi model outside `platform.py`.
- Use type hints and clear docstrings — this will help Cursor generate the next phases cleanly.
- Test servo movement and pump independently before combining them.

---

**Status**: Prototype on **Pi 3**, production target **Pi 4/5**; wiring defined, Phase 1 implemented, platform profiles in code.