"""Self-diagnosis for a built AeroRecorder.

A windowed PyInstaller build has nowhere to print, so a fault that only
appears in the frozen application is invisible. This runs the real startup
sequence, watches it for a while, and writes what actually happened to a
file.

Run with:  AeroRecorder.exe --diagnose
Report:    %LOCALAPPDATA%\\AeroRecorder\\diagnose.log
"""

from __future__ import annotations

import os
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path


def _report_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA", str(Path.home()))
    path = Path(local_app_data) / "AeroRecorder" / "diagnose.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def run_diagnosis(seconds: float = 12.0) -> int:
    lines: list[str] = []

    def say(text: str = "") -> None:
        lines.append(text)

    say("=" * 68)
    say(f"AeroRecorder diagnosis  {datetime.now():%Y-%m-%d %H:%M:%S}")
    say("=" * 68)
    say(f"frozen          : {getattr(sys, 'frozen', False)}")
    say(f"executable      : {sys.executable}")
    say(f"_MEIPASS        : {getattr(sys, '_MEIPASS', None)}")
    say(f"sys.stdin       : {sys.stdin!r}")
    say(f"sys.stdout      : {sys.stdout!r}")
    say("")

    # --- FFmpeg discovery -------------------------------------------------
    try:
        from .recorder import find_ffmpeg

        started = time.monotonic()
        ffmpeg = find_ffmpeg()
        say(f"find_ffmpeg()   : {ffmpeg}  ({time.monotonic() - started:.2f}s)")
        say(f"  exists        : {ffmpeg.exists() if ffmpeg else False}")
    except Exception:
        say("find_ffmpeg()   : RAISED")
        say(traceback.format_exc())
        ffmpeg = None
    say("")

    # --- Device enumeration, the step that reportedly sticks --------------
    from . import recorder as recorder_module

    for label, function in (
        ("list_microphones", recorder_module.list_microphones),
        ("list_webcams", recorder_module.list_webcams),
    ):
        started = time.monotonic()
        try:
            value = function()
            say(f"{label:17s}: {time.monotonic() - started:6.2f}s -> {value!r}")
        except Exception:
            say(f"{label:17s}: {time.monotonic() - started:6.2f}s -> RAISED")
            say(traceback.format_exc())

    try:
        from .system_audio import list_system_audio_devices

        started = time.monotonic()
        value = list_system_audio_devices()
        say(f"{'system audio':17s}: {time.monotonic() - started:6.2f}s -> {value!r}")
    except Exception:
        say(f"{'system audio':17s}: RAISED")
        say(traceback.format_exc())
    say("")

    # --- The real application --------------------------------------------
    say(f"--- starting the real UI and watching it for {seconds:.0f}s")
    try:
        import tkinter as tk

        from .ui import AeroRecorderApp

        root = tk.Tk()
        root.withdraw()
        app = AeroRecorderApp(root)

        # Count how many level samples reach the app, and how many reach the
        # Tk variable the meter widget is bound to.
        counters = {"from_thread": 0, "applied": 0}
        original_from_thread = app._audio_levels_from_thread
        original_apply = app._apply_audio_levels

        def counting_from_thread(mic: float, sysaudio: float) -> None:
            counters["from_thread"] += 1
            original_from_thread(mic, sysaudio)

        def counting_apply(mic: float, sysaudio: float) -> None:
            counters["applied"] += 1
            original_apply(mic, sysaudio)

        app._audio_levels_from_thread = counting_from_thread  # type: ignore[method-assign]
        app._apply_audio_levels = counting_apply  # type: ignore[method-assign]

        ticks = {"count": 0}
        original_drain = app._drain_ui_queue

        def counting_drain() -> None:
            ticks["count"] += 1
            original_drain()

        app._drain_ui_queue = counting_drain  # type: ignore[method-assign]
        root.after(40, counting_drain)

        samples: list[str] = []
        deadline = time.monotonic() + seconds
        next_sample = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            try:
                root.update()
            except Exception:
                say("root.update() RAISED")
                say(traceback.format_exc())
                break
            if time.monotonic() >= next_sample:
                next_sample += 2.0
                samples.append(
                    f"  t={seconds - (deadline - time.monotonic()):5.1f}s"
                    f"  ticks={ticks['count']:<5}"
                    f"  queue={app._ui_queue.qsize():<3}"
                    f"  stalled={app.watchdog.stalled_for():5.2f}s"
                    f"  lvl_in={counters['from_thread']:<5}"
                    f"  lvl_applied={counters['applied']:<5}"
                    f"  mic_level={app.microphone_level_var.get():.3f}"
                )
            time.sleep(0.01)

        say("")
        say("timeline:")
        lines.extend(samples)
        say("")
        say(f"final microphone : {app.microphone_var.get()!r}")
        say(f"final webcam     : {app.webcam_var.get()!r}")
        say(f"final system     : {app.system_audio_var.get()!r}")
        say(f"pump ticks       : {ticks['count']}  (expect roughly 25/second)")
        say(f"queue depth      : {app._ui_queue.qsize()}")
        say("")
        say("threads:")
        for thread in threading.enumerate():
            say(f"  {thread.name:32s} alive={thread.is_alive()} daemon={thread.daemon}")

        try:
            root.destroy()
        except Exception:
            pass
    except Exception:
        say("UI startup RAISED")
        say(traceback.format_exc())

    say("")
    say("=" * 68)

    report = "\n".join(lines) + "\n"
    path = _report_path()
    try:
        path.write_text(report, encoding="utf-8")
    except OSError:
        pass
    # Also to stdout, for a console build or a redirected run.
    try:
        print(report)
    except Exception:
        pass
    return 0
