# Raspberry Pi — Run and Test (Phase 1)

Step-by-step guide for installing, running, and safely testing manual control on real hardware.

---

## Before you start

You should have:

- **Raspberry Pi 3** for prototype (this guide applies as-is) or Pi 4/5 for production, with **Raspberry Pi OS** (32- or 64-bit)
- Power, network (Wi‑Fi or Ethernet), keyboard + monitor **or** SSH from another computer
- Phase 1 wiring per [`cat-deterrent-hardware.md`](../cat-deterrent-hardware.md) (PCA9685 on I2C, relay on **GPIO 17**, servos on channels 0–1)
- **Common ground** between PSU, Pi, PCA9685, and relay
- Servo power on PCA9685 **V+** (5 V), not from the Pi 5 V pin

**Safety**

- Start with **no water** in the pump line until servos and relay behave correctly.
- Keep the nozzle pointed away from people and electronics during testing.
- Stop with **Ctrl+C** or `quit` — the program turns the pump off on exit.

---

## 1. Prepare the Pi (one time)

### 1.1 Update the system

```bash
sudo apt update
sudo apt full-upgrade -y
```

### 1.2 Enable I2C (required for PCA9685)

```bash
sudo raspi-config
```

1. **Interface Options** → **I2C** → **Yes**
2. Finish and **reboot**:

```bash
sudo reboot
```

### 1.3 Install OS packages for Python and GPIO

```bash
sudo apt install -y python3-venv python3-pip python3-dev \
  i2c-tools libgpiod2
```

### 1.4 Add your user to the `gpio` and `i2c` groups (optional but helpful)

```bash
sudo usermod -aG gpio,i2c $USER
```

Log out and back in (or reboot) for group membership to apply.

---

## 2. Get the project on the Pi

### Option A — Git clone (if you pushed to GitHub)

```bash
cd ~
git clone https://github.com/abeshara21/maxwell-repellant.git
cd maxwell-repellant/cat-deterrent
```

### Option B — Copy from your PC

Copy the whole `maxwell-repellant` folder (USB drive, `scp`, etc.), then:

```bash
cd ~/maxwell-repellant/cat-deterrent
```

*(Adjust the path if your folder lives elsewhere.)*

---

## 3. Python environment and dependencies

```bash
cd ~/maxwell-repellant/cat-deterrent   # or your path

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

You should see `(.venv)` at the start of your shell prompt while the venv is active.

---

## 4. Hardware checks (before running the app)

### 4.1 Confirm the PCA9685 on I2C

With everything powered (Pi + servo driver):

```bash
sudo i2cdetect -y 1
```

You should see **`40`** in the grid (default PCA9685 address). If you see `UU` or nothing at `0x40`, check SDA/SCL wiring, power to the board, and that I2C is enabled.

### 4.2 Confirm you are not in mock mode

On a real Pi, the code uses hardware automatically. Do **not** set:

```bash
export CAT_DETERRENT_MOCK=1
```

Do **not** pass `--mock` unless you are debugging without hardware.

---

## 5. Quick one-off hardware smoke tests (optional)

Run these from `cat-deterrent` with the venv activated.

### 5.1 Pan servo only

```bash
python -c "
from hardware.servo_controller import ServoController
s = ServoController(mock=False)
s.set_pan(45)
input('Pan at 45° — press Enter for 135°...')
s.set_pan(135)
s.set_pan(90)
s.close()
"
```

Watch the **pan** servo only. If it does not move, recheck channel 0 wiring and servo power.

### 5.2 Tilt servo only

```bash
python -c "
from hardware.servo_controller import ServoController
s = ServoController(mock=False)
s.set_tilt(50)
input('Tilt at 50° — press Enter for 120°...')
s.set_tilt(120)
s.set_tilt(90)
s.close()
"
```

### 5.3 Relay / pump only (dry run — no water yet)

```bash
python -c "
from hardware.pump_controller import PumpController
import time
p = PumpController(mock=False)
input('Press Enter for a 0.5 s relay pulse...')
p.burst(0.5)
input('Press Enter to exit...')
p.close()
"
```

You should hear a relay click. Confirm the pump circuit is correct before adding water.

---

## 6. Run full manual control

### 6.1 Line mode (recommended first time)

Easier to type commands and read output:

```bash
python manual_control.py --line
```

### 6.2 Live keyboard mode (WASD / arrows)

Use a terminal attached directly to the Pi (or SSH with a TTY):

```bash
python manual_control.py
```

If keys do not respond over SSH, use `--line` or run from a local monitor + keyboard.

### 6.3 Controls

| Input | Action |
|-------|--------|
| `left` / `right` / `up` / `down` (or a/d/w/s in keyboard mode) | Pan / tilt |
| `fire` or space (keyboard mode) | Water burst (~0.5 s) |
| `center` | Mid-range angles |
| `status` | Print pan, tilt, pump state |
| `quit` or Ctrl+C | Exit and shut down GPIO safely |

Example session (line mode):

```text
> status
> right
> right
> center
> fire
> quit
```

---

## 7. Recommended test sequence (first day)

1. **Power only Pi + PCA9685** — run `i2cdetect`, then pan/tilt one-liners (section 5.1–5.2).
2. **Adjust limits** in `hardware/config.py` if servos buzz at the ends (`PAN_MIN` / `PAN_MAX`, etc.).
3. **Wire relay, pump dry** — run relay pulse test (section 5.3).
4. **Run `manual_control.py --line`** — move pan/tilt, then one short `fire`.
5. **Add water** — short bursts only; keep burst duration in config small (`PUMP_BURST_DURATION`).

Test **servos** and **pump** separately before combining aiming + water.

---

## 8. Run from SSH (headless)

```bash
ssh pi@<your-pi-ip>
cd ~/maxwell-repellant/cat-deterrent
source .venv/bin/activate
python manual_control.py --line
```

For systemd or auto-start on boot, set that up later; Phase 1 is meant for interactive testing.

---

## 9. Troubleshooting

| Symptom | Things to try |
|--------|----------------|
| `No module named 'adafruit_servokit'` | `source .venv/bin/activate` and `pip install -r requirements.txt` |
| `i2cdetect` shows no `40` | Enable I2C, check SDA/SCL (GPIO 2/3), 3.3 V logic VCC on PCA9685, common GND |
| Servo jitters or resets Pi | Power servos from PSU 5 V on PCA9685 V+, add 100–470 µF cap near driver |
| Relay always on/off wrong | Confirm **low-level trigger**; GPIO 17 matches `RELAY_PIN` in `hardware/config.py` |
| Log says "mock mode" on the Pi | Unset `CAT_DETERRENT_MOCK`; do not use `--mock` |
| Permission errors on GPIO | `sudo python manual_control.py --line` once, or fix group membership (section 1.4) |
| Pump runs continuously after crash | Cycle power on relay/pump; always exit with Ctrl+C or `quit` |

Verbose logging:

```bash
python manual_control.py --line -v
```

---

## 10. Match your wiring to config

Defaults in `hardware/config.py`:

| Setting | Value |
|---------|--------|
| Pan channel | 0 |
| Tilt channel | 1 |
| Relay GPIO | **17** |
| Pan range | 10° – 170° |
| Tilt range | 30° – 150° |
| Burst length | 0.5 s |

Change only these constants if your wiring differs — do not patch the controller files for pin changes.

---

## 11. After Phase 1 works

- Commit any config tweaks on the Pi or sync changes back to your PC and push to GitHub.
- Phase 2 will add the camera; the camera ribbon is not required for these tests.

For a short overview of the code layout, see [`README.md`](README.md).