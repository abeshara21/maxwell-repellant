"""Shared types for vision / detection."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Detection:
    """Single object detection in pixel coordinates."""

    label: str
    confidence: float
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def center_x(self) -> float:
        return (self.x1 + self.x2) / 2.0

    @property
    def center_y(self) -> float:
        return (self.y1 + self.y2) / 2.0

    def as_normalized(self, frame_width: int, frame_height: int) -> dict[str, float | str]:
        if frame_width <= 0 or frame_height <= 0:
            raise ValueError("frame dimensions must be positive")
        return {
            "label": self.label,
            "confidence": round(self.confidence, 4),
            "cx": round(self.center_x / frame_width, 4),
            "cy": round(self.center_y / frame_height, 4),
            "w": round((self.x2 - self.x1) / frame_width, 4),
            "h": round((self.y2 - self.y1) / frame_height, 4),
        }


def pick_best_cat(detections: list[Detection]) -> Detection | None:
    if not detections:
        return None
    return max(detections, key=lambda d: d.confidence)


@dataclass
class ClipMetadata:
    """Sidecar JSON for training / labeling (e.g. clawing vs normal)."""

    started_at: str
    ended_at: str
    duration_s: float
    frame_count: int
    camera_width: int
    camera_height: int
    best_cat_confidence: float
    behavior_label: str | None = None  # set offline: clawing | normal | unknown
    notes: str = ""
    bbox_samples: list[dict[str, float | str]] = field(default_factory=list)