"""Raspberry Pi model detection and prototype vs production profiles.

GPIO/I2C wiring is identical across Pi 3 / 4 / 5; differences (CPU, RAM, camera
pipeline) are captured in PlatformCapabilities so Phase 2+ can branch without
scattering model checks through the codebase.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PlatformProfile(Enum):
    """prototype = Pi 3 bench rig; production = Pi 4/5 deploy target."""

    PROTOTYPE = "prototype"
    PRODUCTION = "production"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PlatformCapabilities:
    profile: PlatformProfile
    board_model: str
    on_raspberry_pi: bool
    # Phase 2+ hints (Phase 1 ignores these)
    camera_stack: str
    suggested_detector: str
    detector_input_size: int

    @property
    def is_prototype(self) -> bool:
        return self.profile == PlatformProfile.PROTOTYPE

    @property
    def is_production(self) -> bool:
        return self.profile == PlatformProfile.PRODUCTION


def _read_board_model() -> str:
    if sys.platform != "linux":
        return ""
    try:
        with open("/proc/device-tree/model", encoding="utf-8") as f:
            return f.read().strip("\x00").strip()
    except OSError:
        return ""


def _profile_from_model(model: str) -> PlatformProfile:
    lower = model.lower()
    if "raspberry pi 3" in lower:
        return PlatformProfile.PROTOTYPE
    if "raspberry pi 4" in lower or "raspberry pi 5" in lower:
        return PlatformProfile.PRODUCTION
    if "raspberry pi" in lower:
        return PlatformProfile.UNKNOWN
    return PlatformProfile.UNKNOWN


def _profile_from_env() -> PlatformProfile | None:
    raw = os.environ.get("CAT_DETERRENT_PROFILE", "").strip().lower()
    if raw in ("prototype", "pi3", "3"):
        return PlatformProfile.PROTOTYPE
    if raw in ("production", "pi4", "pi5", "4", "5"):
        return PlatformProfile.PRODUCTION
    return None


def _capabilities_for(profile: PlatformProfile, model: str, on_pi: bool) -> PlatformCapabilities:
    if profile == PlatformProfile.PROTOTYPE:
        return PlatformCapabilities(
            profile=profile,
            board_model=model or "unknown",
            on_raspberry_pi=on_pi,
            camera_stack="picamera2",
            suggested_detector="mobilenet_ssd_lite_or_yolov8n_int8",
            detector_input_size=320,
        )
    if profile == PlatformProfile.PRODUCTION:
        return PlatformCapabilities(
            profile=profile,
            board_model=model or "unknown",
            on_raspberry_pi=on_pi,
            camera_stack="picamera2",
            suggested_detector="yolov8n_or_larger",
            detector_input_size=640,
        )
    return PlatformCapabilities(
        profile=profile,
        board_model=model or "unknown",
        on_raspberry_pi=on_pi,
        camera_stack="picamera2",
        suggested_detector="mobilenet_ssd_lite_or_yolov8n",
        detector_input_size=416,
    )


def get_platform() -> PlatformCapabilities:
    """Resolve board + profile (env override wins over auto-detect)."""
    model = _read_board_model()
    on_pi = "Raspberry Pi" in model if model else False
    env_profile = _profile_from_env()
    if env_profile is not None:
        profile = env_profile
    elif on_pi:
        profile = _profile_from_model(model)
    else:
        profile = PlatformProfile.UNKNOWN
    caps = _capabilities_for(profile, model, on_pi)
    logger.debug(
        "platform profile=%s model=%r on_pi=%s",
        caps.profile.value,
        caps.board_model,
        caps.on_raspberry_pi,
    )
    return caps


def should_use_mock(hardware_mock: bool | None) -> bool:
    """True when running off-Pi or when mock is explicitly requested."""
    if hardware_mock is True:
        return True
    if hardware_mock is False:
        return False
    return not get_platform().on_raspberry_pi