# Cat Deterrent Prototype – Raspberry Pi Setup Guide

**Goal**: Get a Raspberry Pi ready for development of the cat deterrent (manual control first, then vision).

---

## 1. What You Need to Get Started

### Required
| Item | Notes |
|------|-------|
| Raspberry Pi | Pi 3, 4, or 5 (Pi 4/5 recommended) |
| microSD card | 16 GB minimum (32 GB preferred). U3/A2 cards are faster |
| Power supply | Official 5V supply matching your Pi model (or the multi-rail PSU later) |
| HDMI cable + monitor | Or use a headless setup |
| USB keyboard + mouse | For initial setup (optional if headless) |
| Ethernet cable or Wi-Fi | Network access |

### Project Hardware (can add after Pi is running)
- Raspberry Pi Camera Module V2
- PCA9685 servo driver
- 2× MG90S servos + pan-tilt bracket
- 12V pump + relay module
- Arcity multi-output PSU (5V + 12V)

---

## 2. Flash the SD Card

### Using Raspberry Pi Imager (recommended)
1. Download **Raspberry Pi Imager** from the official site.
2. Insert the microSD card into your computer.
3. Open Imager → **Choose OS** → Raspberry Pi OS (64-bit recommended).
4. **Choose Storage** → select your SD card.
5. Click the gear icon (Advanced options) and set:
   - Hostname (e.g. `cat-deterrent`)
   - Enable SSH
   - Set username + password
   - Configure Wi-Fi (SSID + password)
   - Set locale
6. Click **Write**.  
   - It is normal for the card to disappear from File Explorer.
   - If it hangs at low percentages, try a USB 2.0 port or run Imager as Administrator.
7. When finished, eject the card and insert it into the Pi.

### Alternative tools
- balenaEtcher
- Rufus (DD mode)

---

## 3. First Boot & Basic Setup

1. Connect HDMI, keyboard, mouse, and power.
2. The Pi will boot to the desktop (or login prompt).
3. Complete the initial wizard if it appears.
4. Open a terminal and update the system:
   ```bash
   sudo apt update && sudo apt full-upgrade -y
   sudo reboot
   ```

### Enable SSH (if not done in Imager)
```bash
sudo raspi-config
# Interface Options → SSH → Yes
```

### Find the Pi’s IP address
```bash
hostname -I
```
Then you can SSH from another computer:
```bash
ssh username@<ip-address>
```

---

## 4. Connect the Camera Module V2

1. Power off the Pi.
2. Insert the CSI ribbon cable into the camera port (contacts facing the correct direction — usually toward the HDMI port on Pi 3).
3. Lock the latch.
4. Boot and install the camera library:
   ```bash
   sudo apt install -y python3-picamera2
   ```
5. Test:
   ```bash
   libcamera-hello --timeout 0
   ```
   or with a short Python script (see earlier camera setup notes).

---

## 5. Recommended Project Structure

```
cat-deterrent/
├── hardware/
│   ├── servo_controller.py
│   ├── pump_controller.py
│   └── config.py
├── manual_control.py
├── requirements.txt
└── README.md
```

Create it on the Pi:
```bash
mkdir -p ~/cat-deterrent/hardware
cd ~/cat-deterrent
```

---

## 6. Typical Development Workflow

1. **Flash & first boot** (done once).
2. **SSH into the Pi** from your main computer.
3. **Edit code** — pick one method below ([§6.1 Edit code on the Pi](#61-edit-code-on-the-pi-three-ways)).
4. **Test hardware incrementally**:
   - Camera only
   - Servos only (via PCA9685)
   - Relay + pump only
   - Combined manual control
5. **Iterate** — keep hardware control classes separate so vision and control loops can be addedlater.
6. **Version control** (optional but recommended): 
   ```bash
   git init
   git add .
   git commit -m "Initial manual control"
   ```

### 6.1 Edit code on the Pi (three ways)

You already need SSH working (step 2). The Pi’s IP is from `hostname -I` on the Pi, or your router’s device list.

#### Option A — Edit directly on the Pi (`nano`, quick fixes)

**On the Pi** (keyboard + monitor) or **over SSH** from your PC:

```bash
ssh YOUR_USER@192.168.1.XXX    # use your Pi IP

cd ~/maxwell-repellant/cat-deterrent   # or wherever you cloned the repo
nano hardware/config.py                 # or any file
```

| Key / action | What it does |
|----------------|---------------|
| Arrow keys | Move cursor |
| Type | Edit text |
| `Ctrl+O`, Enter | Save |
| `Ctrl+X` | Quit |

```bash
python manual_control.py --line        # run from the same folder
```

**`vim`** is available but steeper to learn; use `nano` until you want `vim` tutorials.

---

#### Option B — VS Code Remote-SSH (edit on your PC, files live on the Pi)

Best for a full editor on Windows while code stays on the Pi.

1. **On Windows:** install [VS Code](https://code.visualstudio.com/) and the extension **Remote - SSH** (Microsoft).
2. **Optional — SSH config** (makes connecting easier). Edit `C:\Users\YOUR_USER\.ssh\config`:

   ```
   Host cat-pi
       HostName 192.168.1.XXX
       User YOUR_USER
   ```

   Replace IP and username (same as in Raspberry Pi Imager).

3. In VS Code: `F1` → **Remote-SSH: Connect to Host…** → pick `cat-pi` (or `YOUR_USER@192.168.1.XXX`).
4. Enter your Pi password when prompted (first time may install the VS Code server on the Pi — wait for it to finish).
5. **File → Open Folder** → e.g. `/home/YOUR_USER/maxwell-repellant` or `~/cat-deterrent`.
6. Edit files in the sidebar; save with `Ctrl+S`.
7. Open a terminal in VS Code (**Terminal → New Terminal**); that shell is **on the Pi**:

   ```bash
   cd cat-deterrent
   source .venv/bin/activate
   python manual_control.py --line
   ```

**First-time on Pi** (once), clone the repo if you have not:

```bash
git clone https://github.com/abeshara21/maxwell-repellant.git
cd maxwell-repellant/cat-deterrent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

---

#### Option C — Cursor Remote-SSH (same idea as VS Code)

Cursor can attach to the Pi over SSH like VS Code.

1. On Windows, open **Cursor**.
2. Install **Remote - SSH** if Cursor prompts you (same extension family as VS Code).
3. `Ctrl+Shift+P` → **Remote-SSH: Connect to Host…** → `YOUR_USER@192.168.1.XXX` or your `Host cat-pi` from `~/.ssh\config`.
4. **Open Folder** → your project on the Pi (`maxwell-repellant`).
5. Edit in Cursor; use the integrated terminal on the Pi to run Python tests.

**Tip:** You can also keep the repo on your Windows PC (`Maxwell Repellant`), push to GitHub, and on the Pi run `git pull` — useful when you prefer editing locally without Remote-SSH.

---

#### Which option to choose?

| Method | When to use |
|--------|-------------|
| **nano on SSH** | One-line config changes, no extra setup |
| **VS Code Remote-SSH** | Comfortable GUI, debugging, many files |
| **Cursor Remote-SSH** | Same as VS Code if you use Cursor daily |
| **Edit on PC + `git pull` on Pi** | No Remote-SSH; good with GitHub already set up |

---

## 7. Next Steps After Basic Setup

- [ ] Confirm camera works
- [ ] Wire PCA9685 + servos and test pan/tilt
- [ ] Wire relay + 12V pump and test short bursts
- [ ] Implement `manual_control.py` (keyboard control)
- [ ] Add object detection
- [ ] Add closed-loop aiming

---

## Quick Reference Commands

| Task | Command |
|------|---------|
| Update system | `sudo apt update && sudo apt full-upgrade -y` |
| Enable camera | `sudo raspi-config` → Interface Options |
| Test camera | `libcamera-hello` |
| Find IP | `hostname -I` |
| Reboot | `sudo reboot` |
| Shutdown | `sudo shutdown -h now` |

---

**Status**: Ready for SD card flashing and first boot.  
Once the Pi is online and the camera is confirmed, move to servo and pump testing.
