"""12V pump control via GPIO relay."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from .config import PUMP_BURST_DURATION, RELAY_PIN
from .platform import should_use_mock

if TYPE_CHECKING:
    from gpiozero import OutputDevice

logger = logging.getLogger(__name__)


class PumpController:
    """Switches the water pump through a low-level-trigger relay on RELAY_PIN."""

    def __init__(self, mock: bool | None = None) -> None:
        use_mock = should_use_mock(mock)
        self._mock = use_mock
        self._relay: OutputDevice | None = None

        self._mock_on = False
        if self._mock:
            logger.info("PumpController running in mock mode")
            return

        from gpiozero import OutputDevice

        # Low-level trigger: on() pulls IN low and energizes the relay.
        self._relay = OutputDevice(RELAY_PIN, active_high=False, initial_value=False)

    @property
    def is_on(self) -> bool:
        if self._mock:
            return getattr(self, "_mock_on", False)
        assert self._relay is not None
        return bool(self._relay.value)

    def on(self) -> None:
        if self._mock:
            self._mock_on = True
            logger.info("mock pump ON")
            return
        assert self._relay is not None
        self._relay.on()

    def off(self) -> None:
        if self._mock:
            self._mock_on = False
            logger.info("mock pump OFF")
            return
        assert self._relay is not None
        self._relay.off()

    def burst(self, duration: float = PUMP_BURST_DURATION) -> None:
        """Run the pump for a fixed duration (seconds)."""
        if duration <= 0:
            return
        self.on()
        try:
            time.sleep(duration)
        finally:
            self.off()

    def close(self) -> None:
        """Ensure pump is off and release GPIO."""
        self.off()
        if self._relay is not None:
            self._relay.close()
            self._relay = None