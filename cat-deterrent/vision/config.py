"""Vision pipeline settings (camera, detector, clip storage)."""

from __future__ import annotations

import os
from pathlib import Path

# COCO class id for "cat" in YOLO pretrained models
COCO_CAT_CLASS_ID = 15

DATA_DIR = Path(os.environ.get("CAT_DETERRENT_DATA_DIR", "data/clips"))

_default_max_gb = float(os.environ.get("CAT_DETERRENT_MAX_CLIP_GB", "1"))
MAX_STORAGE_BYTES = int(_default_max_gb * 1024**3)

DETECTION_CONFIDENCE = float(os.environ.get("CAT_DETERRENT_DET_CONF", "0.45"))
YOLO_MODEL_NAME = os.environ.get("CAT_DETERRENT_YOLO_MODEL", "yolov8n.pt")

# Camera capture (main stream)
CAMERA_WIDTH = int(os.environ.get("CAT_DETERRENT_CAM_WIDTH", "640"))
CAMERA_HEIGHT = int(os.environ.get("CAT_DETERRENT_CAM_HEIGHT", "480"))
CAMERA_FPS = int(os.environ.get("CAT_DETERRENT_CAM_FPS", "15"))

# Run detector every N frames (Pi 3 CPU relief)
DETECT_EVERY_N_FRAMES = int(os.environ.get("CAT_DETERRENT_DETECT_EVERY", "2"))

CLIP_MIN_SECONDS = float(os.environ.get("CAT_DETERRENT_CLIP_MIN_S", "2.0"))
CLIP_MAX_SECONDS = float(os.environ.get("CAT_DETERRENT_CLIP_MAX_S", "120.0"))
CLIP_TAIL_SECONDS = float(os.environ.get("CAT_DETERRENT_CLIP_TAIL_S", "3.0"))

# Cap metadata JSON samples per clip (bbox trail for labeling)
MAX_BBOX_SAMPLES_PER_CLIP = 300