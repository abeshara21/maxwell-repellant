#!/usr/bin/env python3
"""Phase 1: manual pan/tilt and water burst from the keyboard."""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
from collections.abc import Callable
from contextlib import contextmanager

from hardware import PumpController, ServoController
from hardware.config import PUMP_BURST_DURATION
from hardware.platform import get_platform

HELP_TEXT = """
Cat deterrent — manual control (Phase 1)
----------------------------------------
  Movement:  WASD or arrow keys
  Water:     Space (short burst)
  Quit:      Q or Ctrl+C

  Commands (any mode): status | center | help
"""


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")


@contextmanager
def _raw_terminal(stdin_fd: int):
    """Put stdin in cbreak mode for single-key input (Unix only)."""
    import termios
    import tty

    old = termios.tcgetattr(stdin_fd)
    try:
        tty.setcbreak(stdin_fd)
        yield
    finally:
        termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old)


def _read_key_nonblocking() -> str | None:
    """Read one key if available; decode arrow escape sequences."""
    import select

    if select.select([sys.stdin], [], [], 0)[0]:
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            if select.select([sys.stdin], [], [], 0.05)[0]:
                ch2 = sys.stdin.read(1)
                if ch2 == "[" and select.select([sys.stdin], [], [], 0.05)[0]:
                    ch3 = sys.stdin.read(1)
                    return {"A": "UP", "B": "DOWN", "C": "RIGHT", "D": "LEFT"}.get(
                        ch3, ch
                    )
            return ch
        return ch
    return None


class ManualControlSession:
    """Coordinates servos and pump with safe shutdown."""

    def __init__(self, mock: bool | None) -> None:
        self.servos = ServoController(mock=mock)
        self.pump = PumpController(mock=mock)
        self._running = True

    def shutdown(self) -> None:
        self._running = False
        self.pump.close()
        self.servos.close()

    def print_status(self) -> None:
        print(
            f"pan={self.servos.pan:.0f}°  tilt={self.servos.tilt:.0f}°  "
            f"pump={'ON' if self.pump.is_on else 'off'}"
        )

    def center(self) -> None:
        from hardware.config import PAN_MAX, PAN_MIN, TILT_MAX, TILT_MIN

        self.servos.set_pan((PAN_MIN + PAN_MAX) / 2)
        self.servos.set_tilt((TILT_MIN + TILT_MAX) / 2)
        self.print_status()

    def handle_token(self, token: str) -> bool:
        """Return False to exit the session."""
        key = token.strip().lower()
        if key in ("q", "quit", "exit"):
            return False
        if key in ("h", "help", "?"):
            print(HELP_TEXT)
            return True
        if key == "status":
            self.print_status()
            return True
        if key == "center":
            self.center()
            return True
        if key in ("w", "up"):
            self.servos.nudge_tilt(-5)
            self.print_status()
            return True
        if key in ("s", "down"):
            self.servos.nudge_tilt(5)
            self.print_status()
            return True
        if key in ("a", "left"):
            self.servos.nudge_pan(-5)
            self.print_status()
            return True
        if key in ("d", "right"):
            self.servos.nudge_pan(5)
            self.print_status()
            return True
        if key in ("fire", "space", " "):
            self.pump.burst(PUMP_BURST_DURATION)
            print(f"burst ({PUMP_BURST_DURATION}s)")
            return True
        if key == "":
            return True
        print(f"Unknown: {token!r} — type help")
        return True

    def handle_raw_key(self, key: str) -> bool:
        if key == "\x03":  # Ctrl+C in cbreak
            return False
        mapping: dict[str, str] = {
            "w": "w",
            "W": "w",
            "a": "a",
            "A": "a",
            "s": "s",
            "S": "s",
            "d": "d",
            "D": "d",
            " ": " ",
            "q": "q",
            "Q": "q",
            "UP": "up",
            "DOWN": "down",
            "LEFT": "left",
            "RIGHT": "right",
        }
        token = mapping.get(key)
        if token is None:
            return True
        return self.handle_token(token)

    def run_line_input(self) -> None:
        print(HELP_TEXT)
        self.print_status()
        while self._running:
            try:
                line = input("> ").strip()
            except EOFError:
                break
            if not self.handle_token(line):
                break

    def run_keyboard(self) -> None:
        print(HELP_TEXT)
        self.print_status()
        if sys.platform == "win32":
            self.run_line_input()
            return
        stdin_fd = sys.stdin.fileno()
        if not sys.stdin.isatty():
            self.run_line_input()
            return

        with _raw_terminal(stdin_fd):
            while self._running:
                key = _read_key_nonblocking()
                if key is None:
                    continue
                if not self.handle_raw_key(key):
                    break


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manual cat deterrent control")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Simulate hardware (use on dev machines without a Pi)",
    )
    parser.add_argument(
        "--line",
        action="store_true",
        help="Use line-based commands instead of raw keyboard (Windows-friendly)",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    _configure_logging(args.verbose)

    if args.mock or os.environ.get("CAT_DETERRENT_MOCK", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        mock: bool | None = True
    else:
        mock = None

    platform = get_platform()
    if platform.on_raspberry_pi:
        print(
            f"Board: {platform.board_model}  "
            f"profile={platform.profile.value} "
            f"(override: CAT_DETERRENT_PROFILE=prototype|production)"
        )
    session = ManualControlSession(mock=mock)

    def on_signal(_signum: int, _frame: object) -> None:
        print("\nShutting down…")
        session.shutdown()

    signal.signal(signal.SIGINT, on_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, on_signal)

    use_line = args.line or sys.platform == "win32"
    run: Callable[[], None] = session.run_line_input if use_line else session.run_keyboard

    try:
        run()
    finally:
        session.shutdown()
        print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())