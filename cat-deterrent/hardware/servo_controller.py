"""PCA9685 pan/tilt servo control."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .config import (
    PAN_MAX,
    PAN_MIN,
    PAN_STEP,
    SERVO_PAN_CHANNEL,
    SERVO_TILT_CHANNEL,
    TILT_MAX,
    TILT_MIN,
    TILT_STEP,
)
from .platform import should_use_mock

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def _clamp(angle: float, low: float, high: float) -> float:
    return max(low, min(high, angle))


class ServoController:
    """Drives pan and tilt servos via a PCA9685 (Adafruit ServoKit)."""

    def __init__(self, mock: bool | None = None) -> None:
        use_mock = should_use_mock(mock)
        self._mock = use_mock
        self._pan = (PAN_MIN + PAN_MAX) / 2
        self._tilt = (TILT_MIN + TILT_MAX) / 2
        self._kit = None

        if self._mock:
            logger.info("ServoController running in mock mode")
            self._sync_hardware()
            return

        from adafruit_servokit import ServoKit

        self._kit = ServoKit(channels=16)
        self._sync_hardware()

    @property
    def pan(self) -> float:
        return self._pan

    @property
    def tilt(self) -> float:
        return self._tilt

    def set_pan(self, angle: float) -> float:
        """Set pan angle in degrees; returns the clamped angle applied."""
        self._pan = _clamp(angle, PAN_MIN, PAN_MAX)
        self._write_channel(SERVO_PAN_CHANNEL, self._pan)
        return self._pan

    def set_tilt(self, angle: float) -> float:
        """Set tilt angle in degrees; returns the clamped angle applied."""
        self._tilt = _clamp(angle, TILT_MIN, TILT_MAX)
        self._write_channel(SERVO_TILT_CHANNEL, self._tilt)
        return self._tilt

    def nudge_pan(self, delta: float = PAN_STEP) -> float:
        return self.set_pan(self._pan + delta)

    def nudge_tilt(self, delta: float = TILT_STEP) -> float:
        return self.set_tilt(self._tilt + delta)

    def _write_channel(self, channel: int, angle: float) -> None:
        if self._mock:
            logger.debug("mock servo ch=%s angle=%.1f", channel, angle)
            return
        assert self._kit is not None
        self._kit.servo[channel].angle = angle

    def _sync_hardware(self) -> None:
        self._write_channel(SERVO_PAN_CHANNEL, self._pan)
        self._write_channel(SERVO_TILT_CHANNEL, self._tilt)

    def close(self) -> None:
        """Release resources (no-op in mock mode)."""
        self._kit = None