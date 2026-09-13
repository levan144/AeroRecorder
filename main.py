from __future__ import annotations

import sys
import tkinter as tk

from aero_recorder.single_instance import SingleInstance, broadcast_show_window
from aero_recorder.ui import AeroRecorderApp
from aero_recorder.winapi import enable_per_monitor_dpi_awareness


def main() -> None:
    if "--audio-meter-worker" in sys.argv:
        index = sys.argv.index("--audio-meter-worker")
        if index + 1 < len(sys.argv):
            from aero_recorder.audio_levels import run_audio_meter_worker

            raise SystemExit(run_audio_meter_worker(sys.argv[index + 1]))
        raise SystemExit(2)

    smoke_test = "--smoke-test" in sys.argv

    # Only one AeroRecorder window may exist. A second launch hands focus to
    # the copy that is already running rather than opening a rival window that
    # would fight over the same hotkeys, tray icon, and settings file.
    #
    # The smoke test is exempt: it runs in CI alongside a possible developer
    # instance, and exits immediately without touching shared state.
    guard = SingleInstance()
    if not smoke_test and not guard.acquire():
        broadcast_show_window()
        raise SystemExit(0)

    try:
        enable_per_monitor_dpi_awareness()
        root = tk.Tk()
        if smoke_test:
            root.withdraw()
        AeroRecorderApp(root)
        if smoke_test:
            root.update_idletasks()
            root.destroy()
            return
        root.mainloop()
    finally:
        guard.release()


if __name__ == "__main__":
    main()
