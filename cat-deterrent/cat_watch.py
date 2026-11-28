#!/usr/bin/env python3
"""Detect cats in the camera view, report location, and record clips for labeling."""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from pathlib import Path

import cv2

from hardware.platform import get_platform
from vision.camera import CameraStream
from vision.clip_recorder import ClipRecorder
from vision.config import (
    CAMERA_FPS,
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
    DATA_DIR,
    DETECT_EVERY_N_FRAMES,
    DETECTION_CONFIDENCE,
    MAX_STORAGE_BYTES,
    YOLO_MODEL_NAME,
)
from vision.detector import CatDetector
from vision.storage import RollingClipStore
from vision.types import Detection, pick_best_cat


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")


def _draw_overlay(frame, detections: list[Detection]) -> None:
    for det in detections:
        cv2.rectangle(frame, (det.x1, det.y1), (det.x2, det.y2), (0, 200, 80), 2)
        label = f"{det.label} {det.confidence:.2f}"
        cv2.putText(
            frame,
            label,
            (det.x1, max(det.y1 - 8, 12)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 200, 80),
            1,
            cv2.LINE_AA,
        )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cat detection, localization, and clip capture")
    parser.add_argument("--mock", action="store_true", help="No Pi camera / no YOLO (dry run)")
    parser.add_argument("--video-file", type=Path, help="Use a video file instead of live camera")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR, help="Clip output directory")
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=MAX_STORAGE_BYTES,
        help="Rolling storage cap in bytes (default from CAT_DETERRENT_MAX_CLIP_GB)",
    )
    parser.add_argument("--conf", type=float, default=DETECTION_CONFIDENCE)
    parser.add_argument("--model", default=YOLO_MODEL_NAME)
    parser.add_argument("--width", type=int, default=CAMERA_WIDTH)
    parser.add_argument("--height", type=int, default=CAMERA_HEIGHT)
    parser.add_argument("--fps", type=int, default=CAMERA_FPS)
    parser.add_argument(
        "--no-record",
        action="store_true",
        help="Detection only; do not write clips",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Show OpenCV window (needs display or X forwarding)",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    _configure_logging(args.verbose)

    platform = get_platform()
    if platform.on_raspberry_pi:
        print(f"Board: {platform.board_model}  profile={platform.profile.value}")

    store = RollingClipStore(args.data_dir, args.max_bytes)
    camera = CameraStream(
        width=args.width,
        height=args.height,
        fps=args.fps,
        mock=args.mock,
        video_file=args.video_file,
    )
    detector = CatDetector(mock=args.mock, confidence=args.conf, model_name=args.model)
    recorder = ClipRecorder(
        store,
        width=camera.width,
        height=camera.height,
        fps=args.fps,
        enabled=not args.no_record,
    )

    frame_index = 0
    last_detections: list[Detection] = []
    running = True

    def on_signal(_sig: int, _frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, on_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, on_signal)

    print(
        f"cat_watch: data={args.data_dir.resolve()} "
        f"cap={args.max_bytes / (1024**3):.2f} GiB  record={'off' if args.no_record else 'on'}"
    )
    print("Ctrl+C to stop.")

    try:
        while running:
            ok, frame = camera.read()
            if not ok:
                time.sleep(0.05)
                continue

            run_detect = frame_index % DETECT_EVERY_N_FRAMES == 0
            if run_detect:
                last_detections = detector.detect(frame)
                best = pick_best_cat(last_detections)
                if best is not None:
                    nx = best.center_x / camera.width
                    ny = best.center_y / camera.height
                    print(
                        f"cat @ norm=({nx:.3f}, {ny:.3f}) "
                        f"px=({best.center_x:.0f}, {best.center_y:.0f}) "
                        f"conf={best.confidence:.2f}"
                    )

            cat_present = len(last_detections) > 0
            recorder.on_frame(frame, last_detections, cat_present)

            if args.preview:
                vis = frame.copy()
                _draw_overlay(vis, last_detections)
                if recorder.is_recording:
                    cv2.circle(vis, (24, 24), 10, (0, 0, 255), -1)
                cv2.imshow("cat_watch", vis)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    running = False

            frame_index += 1
            time.sleep(max(0.0, 1.0 / args.fps - 0.001))
    finally:
        recorder.flush()
        camera.close()
        if args.preview:
            cv2.destroyAllWindows()
        print(f"storage: {store.total_bytes() / (1024**2):.1f} MiB used")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())