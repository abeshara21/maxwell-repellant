"""Cat detection and localization (COCO pretrained YOLO)."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from hardware.platform import get_platform, should_use_mock
from vision.config import COCO_CAT_CLASS_ID, DETECTION_CONFIDENCE, YOLO_MODEL_NAME
from vision.types import Detection

logger = logging.getLogger(__name__)


class CatDetector:
    """Runs YOLO on BGR frames; returns cat boxes only."""

    def __init__(
        self,
        mock: bool | None = None,
        confidence: float = DETECTION_CONFIDENCE,
        model_name: str = YOLO_MODEL_NAME,
    ) -> None:
        self.confidence = confidence
        self._mock = should_use_mock(mock)
        self._model: Any = None
        self._imgsz = get_platform().detector_input_size

        if self._mock:
            logger.info("CatDetector mock mode (no inference)")
            return

        from ultralytics import YOLO

        self._model = YOLO(model_name)
        logger.info(
            "CatDetector loaded %s imgsz=%s conf=%.2f",
            model_name,
            self._imgsz,
            confidence,
        )

    def detect(self, frame_bgr: np.ndarray) -> list[Detection]:
        if self._mock:
            return []

        assert self._model is not None
        results = self._model.predict(
            source=frame_bgr,
            imgsz=self._imgsz,
            conf=self.confidence,
            classes=[COCO_CAT_CLASS_ID],
            verbose=False,
        )
        if not results:
            return []
        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return []

        detections: list[Detection] = []
        xyxy = boxes.xyxy.cpu().numpy()
        confs = boxes.conf.cpu().numpy()
        for (x1, y1, x2, y2), conf in zip(xyxy, confs, strict=True):
            detections.append(
                Detection(
                    label="cat",
                    confidence=float(conf),
                    x1=int(x1),
                    y1=int(y1),
                    x2=int(x2),
                    y2=int(y2),
                )
            )
        return detections