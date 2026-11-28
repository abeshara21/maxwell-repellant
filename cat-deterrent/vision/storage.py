"""Rolling on-disk clip store with a configurable byte ceiling."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class RollingClipStore:
    """Keeps total `.mp4` (+ sidecar `.json`) size under `max_bytes` by deleting oldest clips."""

    def __init__(self, directory: Path, max_bytes: int) -> None:
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        self.directory = directory
        self.max_bytes = max_bytes
        self.directory.mkdir(parents=True, exist_ok=True)

    def _clip_paths(self) -> list[Path]:
        return sorted(
            self.directory.glob("*.mp4"),
            key=lambda p: p.stat().st_mtime,
        )

    def total_bytes(self) -> int:
        total = 0
        for path in self.directory.iterdir():
            if path.suffix.lower() in (".mp4", ".json"):
                total += path.stat().st_size
        return total

    def enforce_limit(self) -> list[Path]:
        """Delete oldest clips until usage is at or below the cap. Returns removed mp4 paths."""
        removed: list[Path] = []
        while self.total_bytes() > self.max_bytes:
            clips = self._clip_paths()
            if not clips:
                break
            oldest = clips[0]
            sidecar = oldest.with_suffix(".json")
            size_before = oldest.stat().st_size + (
                sidecar.stat().st_size if sidecar.exists() else 0
            )
            oldest.unlink(missing_ok=True)
            sidecar.unlink(missing_ok=True)
            removed.append(oldest)
            logger.info(
                "rolled storage: removed %s (~%.1f MiB)",
                oldest.name,
                size_before / (1024**2),
            )
        return removed

    def register_clip(self, video_path: Path, metadata_path: Path | None = None) -> None:
        if not video_path.exists():
            raise FileNotFoundError(video_path)
        self.enforce_limit()
        logger.info(
            "clip stored %s (total %.1f / %.1f MiB)",
            video_path.name,
            self.total_bytes() / (1024**2),
            self.max_bytes / (1024**2),
        )

    def write_metadata(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)