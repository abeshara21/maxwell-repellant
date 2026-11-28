"""Camera capture via picamera2 (Pi) or OpenCV fallback."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from hardware.platform import get_platform, should_use_mock
from vision.config import CAMERA_FPS, CAMERA_HEIGHT, CAMERA_WIDTH

logger = logging.getLogger(__name__)


class CameraStream:
    """BGR frame source for cat watch."""

    def __init__(
        self,
        width: int = CAMERA_WIDTH,
        height: int = CAMERA_HEIGHT,
        fps: int = CAMERA_FPS,
        mock: bool | None = None,
        video_file: Path | None = None,
    ) -> None:
        self.width = width
        self.height = height
        self.fps = fps
        self.video_file = video_file
        self._use_mock = should_use_mock(mock) or video_file is not None
        self._backend: str = "none"
        self._picam: Any = None
        self._cap: Any = None
        self._open()

    def _open(self) -> None:
        if self.video_file is not None:
            self._cap = cv2.VideoCapture(str(self.video_file))
            if not self._cap.isOpened():
                raise RuntimeError(f"cannot open video file {self.video_file}")
            self._backend = "file"
            self.width = int(self._cap.get(3)) or self.width
            self.height = int(self._cap.get(4)) or self.height
            logger.info("CameraStream file %s", self.video_file)
            return

        if not self._use_mock and get_platform().on_raspberry_pi:
            try:
                from picamera2 import Picamera2

                self._picam = Picamera2()
                config = self._picam.create_video_configuration(
                    main={"size": (self.width, self.height), "format": "RGB888"},
                    controls={"FrameRate": self.fps},
                )
                self._picam.configure(config)
                self._picam.start()
                self._backend = "picamera2"
                logger.info("CameraStream picamera2 %sx%s@%sfps", self.width, self.height, self.fps)
                return
            except Exception as exc:
                logger.warning("picamera2 unavailable (%s), falling back to OpenCV", exc)

        self._cap = cv2.VideoCapture(0)
        if self._cap.isOpened():
            self._cap.set(3, self.width)
            self._cap.set(4, self.height)
            self._backend = "opencv"
            logger.info("CameraStream OpenCV index 0")
        else:
            self._backend = "synthetic"
            logger.warning("no camera; synthetic blank frames")

    def read(self) -> tuple[bool, np.ndarray]:
        if self._backend == "picamera2":
            assert self._picam is not None
            rgb = self._picam.capture_array()
            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            return True, bgr

        if self._backend in ("opencv", "file"):
            assert self._cap is not None
            ok, frame = self._cap.read()
            if not ok and self._backend == "file":
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = self._cap.read()
            if not ok:
                return False, np.zeros((self.height, self.width, 3), dtype=np.uint8)
            if frame.shape[1] != self.width or frame.shape[0] != self.height:
                frame = cv2.resize(frame, (self.width, self.height))
            return True, frame

        blank = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        cv2.putText(
            blank,
            "MOCK CAMERA",
            (40, self.height // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (180, 180, 180),
            2,
            cv2.LINE_AA,
        )
        return True, blank

    def close(self) -> None:
        if self._picam is not None:
            self._picam.stop()
            self._picam.close()
            self._picam = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None