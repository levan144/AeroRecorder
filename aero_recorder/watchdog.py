"""Detect and record a stalled Tk main loop.

When the interface stops responding there is normally nothing to go on: the
process is alive, no exception is raised, and the window simply ignores
input. This watchdog turns that silence into evidence.

The main loop calls :meth:`MainLoopWatchdog.beat` on every pump tick. A
background thread notices when beats stop arriving and writes a stack trace
for every thread in the process, which shows precisely what the main thread
is blocked on.
"""

from __future__ import annotations

import os
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path


DEFAULT_STALL_SECONDS = 6.0
DEFAULT_POLL_SECONDS = 2.0
# Avoid filling the disk if the loop stays wedged.
MIN_SECONDS_BETWEEN_DUMPS = 30.0


def stall_log_path() -> Path | None:
    # Tests construct the application without running a main loop, which looks
    # exactly like a stall. Keep those out of the real log.
    if os.environ.get("AERORECORDER_SUPPRESS_ERROR_LOG"):
        return None
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return None
    return Path(local_app_data) / "AeroRecorder" / "stalls.log"


class MainLoopWatchdog:
    """Watch for the Tk main loop going unresponsive."""

    def __init__(
        self,
        stall_seconds: float = DEFAULT_STALL_SECONDS,
        poll_seconds: float = DEFAULT_POLL_SECONDS,
    ) -> None:
        self.stall_seconds = stall_seconds
        self.poll_seconds = poll_seconds
        self._last_beat = time.monotonic()
        self._last_dump = 0.0
        self._main_thread_id = threading.get_ident()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def beat(self) -> None:
        """Called from the Tk main loop to say it is still running."""
        with self._lock:
            self._last_beat = time.monotonic()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._main_thread_id = threading.get_ident()
        self._thread = threading.Thread(
            target=self._run, name="AeroRecorderWatchdog", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread = None

    def stalled_for(self) -> float:
        with self._lock:
            return time.monotonic() - self._last_beat

    def _run(self) -> None:
        while not self._stop.wait(self.poll_seconds):
            stalled = self.stalled_for()
            if stalled < self.stall_seconds:
                continue
            now = time.monotonic()
            if now - self._last_dump < MIN_SECONDS_BETWEEN_DUMPS:
                continue
            self._last_dump = now
            try:
                self._dump(stalled)
            except Exception:
                # Diagnostics must never destabilise the application.
                pass

    def _dump(self, stalled: float) -> None:
        path = stall_log_path()
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)

        frames = sys._current_frames()
        names = {thread.ident: thread.name for thread in threading.enumerate()}
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = [
            "",
            "=" * 72,
            f"{stamp}  MAIN LOOP STALLED for {stalled:.1f}s",
            "=" * 72,
        ]
        for ident, frame in frames.items():
            label = names.get(ident, "unknown")
            marker = "  <-- TK MAIN LOOP" if ident == self._main_thread_id else ""
            lines.append(f"\n--- thread {ident} ({label}){marker}")
            lines.extend(
                "    " + line.rstrip()
                for chunk in traceback.format_stack(frame)
                for line in chunk.splitlines()
            )

        with path.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
