# Cat detection & training clips (Phase 2)

Detect cats with the Pi camera, print image location, and auto-record short clips when a cat is in frame. Clips roll over when storage exceeds a configurable cap (default **1 GB**).

Clawing vs normal is **not** classified yet — use generic COCO cat detection now, then label clips offline for a future fine-tuned model.

## Pi setup

```bash
sudo apt install -y python3-picamera2 libcamera-apps
cd ~/maxwell-repellant/cat-deterrent
source .venv/bin/activate
pip install -r requirements.txt
```

First run downloads `yolov8n.pt` (~6 MB).

## Run

```bash
python cat_watch.py
```

| Option | Purpose |
|--------|---------|
| `--preview` | Show live boxes (needs display) |
| `--no-record` | Detection only, no files |
| `--data-dir PATH` | Clip folder (default `data/clips`) |
| `--max-bytes N` | Rolling cap in bytes |
| `--conf 0.45` | Detection threshold |
| `--video-file path` | Test from file instead of camera |

### Storage env vars

```bash
export CAT_DETERRENT_DATA_DIR=data/clips
export CAT_DETERRENT_MAX_CLIP_GB=1
```

When the cap is exceeded, **oldest** `.mp4` + `.json` pairs are deleted.

## Output

Each saved event:

- `clip_YYYYMMDD_HHMMSS_cat.mp4` — video
- `clip_YYYYMMDD_HHMMSS_cat.json` — metadata + normalized bbox trail (`bbox_samples`)

Label for training:

```bash
python tools/label_clip.py data/clips/clip_20251128_120000_cat.json clawing
python tools/label_clip.py data/clips/clip_20251128_120500_cat.json normal
```

## Dev on Windows (no hardware)

```bash
pip install -r requirements-vision.txt
python cat_watch.py --mock --no-record
```

Use a local video with a cat:

```bash
python cat_watch.py --video-file sample.mp4 --data-dir data/clips
```

## Next steps

- Collect labeled clips (clawing vs normal).
- Fine-tune YOLO or train a small behavior classifier on crops / clips.
- Wire detections into pan/tilt (Phase 3) when servos are ready.