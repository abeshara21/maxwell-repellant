"""Record MP4 clips while a cat is visible; attach JSON for labeling."""

from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic

import cv2
import numpy as np

from vision.config import (
    CLIP_MAX_SECONDS,
    CLIP_MIN_SECONDS,
    CLIP_TAIL_SECONDS,
    MAX_BBOX_SAMPLES_PER_CLIP,
)
from vision.storage import RollingClipStore
from vision.types import ClipMetadata, Detection, pick_best_cat

logger = logging.getLogger(__name__)


class ClipRecorder:
    """Starts recording when cats appear; ends after tail timeout or max duration."""

    def __init__(
        self,
        store: RollingClipStore,
        width: int,
        height: int,
        fps: int,
        enabled: bool = True,
    ) -> None:
        self.store = store
        self.width = width
        self.height = height
        self.fps = max(fps, 1)
        self.enabled = enabled
        self._recording = False
        self._writer: cv2.VideoWriter | None = None
        self._video_path: Path | None = None
        self._meta_path: Path | None = None
        self._started_at: datetime | None = None
        self._start_mono: float = 0.0
        self._last_cat_mono: float = 0.0
        self._frame_count = 0
        self._best_conf = 0.0
        self._bbox_samples: list[dict[str, float | str]] = []

    @property
    def is_recording(self) -> bool:
        return self._recording

    def _stamp_paths(self) -> tuple[Path, Path]:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        base = self.store.directory / f"clip_{ts}_cat"
        return base.with_suffix(".mp4"), base.with_suffix(".json")

    def _open_writer(self) -> None:
        self._video_path, self._meta_path = self._stamp_paths()
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self._writer = cv2.VideoWriter(
            str(self._video_path),
            fourcc,
            float(self.fps),
            (self.width, self.height),
        )
        if not self._writer.isOpened():
            raise RuntimeError(f"cannot open video writer {self._video_path}")
        self._started_at = datetime.now(timezone.utc)
        self._start_mono = monotonic()
        self._last_cat_mono = self._start_mono
        self._frame_count = 0
        self._best_conf = 0.0
        self._bbox_samples = []
        self._recording = True
        logger.info("clip recording started %s", self._video_path.name)

    def _close_writer(self, save: bool) -> None:
        if self._writer is not None:
            self._writer.release()
            self._writer = None
        self._recording = False

        if not save or self._video_path is None or self._started_at is None:
            if self._video_path and self._video_path.exists():
                self._video_path.unlink(missing_ok=True)
            self._reset_state()
            return

        duration = max(self._frame_count / self.fps, 0.0)
        if duration < CLIP_MIN_SECONDS:
            logger.info("discarding short clip %.1fs < %.1fs", duration, CLIP_MIN_SECONDS)
            self._video_path.unlink(missing_ok=True)
            self._reset_state()
            return

        ended_at = datetime.now(timezone.utc)
        meta = ClipMetadata(
            started_at=self._started_at.isoformat(),
            ended_at=ended_at.isoformat(),
            duration_s=round(duration, 2),
            frame_count=self._frame_count,
            camera_width=self.width,
            camera_height=self.height,
            best_cat_confidence=round(self._best_conf, 4),
            behavior_label=None,
            notes="Auto-captured cat in frame; label behavior offline (clawing vs normal).",
            bbox_samples=self._bbox_samples,
        )
        if self._meta_path:
            self.store.write_metadata(self._meta_path, asdict(meta))
        self.store.register_clip(self._video_path, self._meta_path)
        logger.info("saved clip %s (%.1fs)", self._video_path.name, duration)
        self._reset_state()

    def _reset_state(self) -> None:
        self._video_path = None
        self._meta_path = None
        self._started_at = None
        self._frame_count = 0
        self._best_conf = 0.0
        self._bbox_samples = []

    def _append_sample(self, det: Detection, t_rel: float) -> None:
        if len(self._bbox_samples) >= MAX_BBOX_SAMPLES_PER_CLIP:
            return
        sample = det.as_normalized(self.width, self.height)
        sample["t"] = round(t_rel, 3)
        self._bbox_samples.append(sample)

    def on_frame(
        self,
        frame_bgr: np.ndarray,
        detections: list[Detection],
        cat_present: bool,
    ) -> None:
        if not self.enabled:
            return

        now = monotonic()
        if cat_present:
            best = pick_best_cat(detections)
            if best is not None:
                self._best_conf = max(self._best_conf, best.confidence)
            if not self._recording:
                self._open_writer()
            self._last_cat_mono = now
            if best is not None and self._recording:
                t_rel = now - self._start_mono
                self._append_sample(best, t_rel)

        if self._recording:
            assert self._writer is not None
            self._writer.write(frame_bgr)
            self._frame_count += 1
            elapsed = now - self._start_mono
            tail = now - self._last_cat_mono

            if elapsed >= CLIP_MAX_SECONDS:
                self._close_writer(save=True)
                if cat_present:
                    self._open_writer()
                return

            if not cat_present and tail >= CLIP_TAIL_SECONDS:
                self._close_writer(save=True)

    def flush(self) -> None:
        if self._recording:
            self._close_writer(save=True)