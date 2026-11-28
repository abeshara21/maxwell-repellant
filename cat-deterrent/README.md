# Cat Deterrent — Phase 1 (Manual Control)

Manual keyboard control of pan/tilt servos (PCA9685) and a short water burst (GPIO relay).

## Setup (Raspberry Pi)

**Prototype:** Pi 3. **Production:** Pi 4/5. Same repo and wiring; board-specific vision defaults live in `hardware/platform.py`.

```bash
cd cat-deterrent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Enable I2C in `raspi-config` before using the servo driver.

Optional: `export CAT_DETERRENT_PROFILE=prototype` or `production` to override auto-detected profile.

## Run

```bash
python manual_control.py
```

On a development PC without hardware:

```bash
python manual_control.py --mock --line
```

### Controls

| Input | Action |
|-------|--------|
| WASD / arrows | Pan and tilt (5° steps) |
| Space | Water burst (`PUMP_BURST_DURATION` in `hardware/config.py`) |
| `center` | Return to mid-range angles |
| `status` | Print current angles |
| Q or Ctrl+C | Quit (pump off, GPIO released) |

## Layout

- `hardware/config.py` — pins, channels, angle limits
- `hardware/servo_controller.py` — PCA9685 pan/tilt
- `hardware/pump_controller.py` — relay / pump
- `manual_control.py` — interactive UI

Hardware is mocked automatically off the Pi; pass `--mock` to force simulation on the Pi.

## Phase 2 — Cat detection & clip capture

No servos required. See **[VISION.md](VISION.md)**.

```bash
python cat_watch.py
```