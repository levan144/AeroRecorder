from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import threading
import time
from array import array
from collections.abc import Callable, Iterable
from typing import Any

from .runtime import application_root

METER_SAMPLES_PER_SECOND = 30
"""Upper bound on meter updates per second.

The meter is a visual indicator; more than this is wasted work and risks
the reader falling behind the writer.
"""

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def pcm_level(data: bytes) -> float:
    if len(data) < 2:
        return 0.0
    samples = array("h")
    samples.frombytes(data[: len(data) - (len(data) % 2)])
    if not samples:
        return 0.0
    rms = math.sqrt(sum(sample * sample for sample in samples) / len(samples))
    if rms <= 0:
        return 0.0
    decibels = 20.0 * math.log10(min(1.0, rms / 32768.0))
    return max(0.0, min(1.0, (decibels + 60.0) / 60.0))


def _normalized_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


# Host APIs in order of preference. Windows lists the same physical device once
# per API, and they are not equivalent: only WASAPI gives real-time, unbuffered
# access. Measured on a real machine, the DirectSound entry for a microphone
# returned 7,669 reads a second of repeated, clipped buffers while the WASAPI
# entry returned 46.8 a second, exactly real time, with clean audio.
_HOST_API_PREFERENCE = (
    "windows wasapi",
    "windows wdm-ks",
    "mme",
    "windows directsound",
)


def _host_api_rank(info: dict[str, Any], host_api_names: dict[int, str] | None) -> int:
    """Higher is better. Unknown APIs rank below every known one."""
    if not host_api_names:
        return 0
    name = str(host_api_names.get(int(info.get("hostApi", -1)), "")).strip().lower()
    for rank, preferred in enumerate(reversed(_HOST_API_PREFERENCE), start=1):
        if name == preferred:
            return rank
    return 0


def best_input_device(
    devices: Iterable[dict[str, Any]],
    requested: str,
    *,
    loopback: bool,
    host_api_names: dict[int, str] | None = None,
) -> dict[str, Any] | None:
    """Pick the device entry to open for ``requested``.

    Name match comes first: the right device on a worse API beats the wrong
    device on a better one. Among equally good name matches, the host API
    breaks the tie in favour of WASAPI.
    """
    requested_name = _normalized_name(requested)
    candidates = [
        info
        for info in devices
        if int(info.get("maxInputChannels", 0)) > 0
        and bool(info.get("isLoopbackDevice", False)) == loopback
    ]
    if not candidates:
        return None

    def score(info: dict[str, Any]) -> tuple[int, int, int]:
        name = _normalized_name(str(info.get("name", "")))
        exact = int(name == requested_name)
        overlap = len(requested_name) if requested_name and requested_name in name else 0
        return exact, overlap, _host_api_rank(info, host_api_names)

    selected = max(candidates, key=score)
    return selected if score(selected)[:2] != (0, 0) or not requested_name else None


class AudioLevelMonitor:
    """Read live levels from a crash-isolated PyAudio helper process."""

    def __init__(self) -> None:
        self._process: subprocess.Popen[str] | None = None
        self._thread: threading.Thread | None = None

    def start(
        self,
        microphone: str | None,
        system_audio: str | None,
        callback: Callable[[float, float], None],
    ) -> None:
        # Never block the caller: start() is invoked from the Tk main loop
        # whenever a device changes or a recording ends.
        self.stop(wait=False)
        if not microphone and not system_audio:
            callback(0.0, 0.0)
            return
        payload = json.dumps({"microphone": microphone, "system_audio": system_audio})
        if getattr(sys, "frozen", False):
            command = [sys.executable, "--audio-meter-worker", payload]
        else:
            command = [
                sys.executable,
                str(application_root() / "main.py"),
                "--audio-meter-worker",
                payload,
            ]
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="ascii",
                errors="replace",
                creationflags=CREATE_NO_WINDOW,
            )
        except OSError:
            callback(0.0, 0.0)
            return
        self._process = process
        self._thread = threading.Thread(
            target=self._read_levels,
            args=(process, callback),
            daemon=True,
        )
        self._thread.start()

    def stop(self, *, wait: bool = True) -> None:
        """Stop the helper process.

        With ``wait=False`` the process is signalled and reaped on a
        background thread. Callers on the Tk main loop must use that, because
        waiting here blocks every redraw: the terminate/join pair below can
        cost up to four seconds, which the user sees as a frozen window.
        """
        process, self._process = self._process, None
        thread, self._thread = self._thread, None

        def reap() -> None:
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=2)
                except (OSError, subprocess.TimeoutExpired):
                    try:
                        process.kill()
                    except OSError:
                        pass
            if thread and thread is not threading.current_thread():
                thread.join(timeout=2.0)
            # The reader holds the stdout pipe. Closing it here prevents a
            # handle leaking on every meter restart, which happens whenever a
            # device changes or a recording ends.
            stdout = getattr(process, "stdout", None)
            if stdout is not None:
                try:
                    stdout.close()
                except (OSError, AttributeError):
                    pass

        if wait:
            reap()
        elif process or thread:
            threading.Thread(target=reap, daemon=True).start()

    @staticmethod
    def _read_levels(
        process: subprocess.Popen[str],
        callback: Callable[[float, float], None],
    ) -> None:
        if not process.stdout:
            return
        for line in process.stdout:
            try:
                microphone, system_audio = (float(value) for value in line.split(",", 1))
            except ValueError:
                continue
            callback(microphone, system_audio)


def run_audio_meter_worker(payload: str) -> int:
    try:
        import pyaudiowpatch as pyaudio
    except ImportError:
        return 1
    try:
        requested = json.loads(payload)
    except json.JSONDecodeError:
        return 2
    microphone = requested.get("microphone")
    system_audio = requested.get("system_audio")
    audio = pyaudio.PyAudio()
    streams: list[tuple[str, Any]] = []
    try:
        devices = [
            audio.get_device_info_by_index(index) for index in range(audio.get_device_count())
        ]
        host_api_names = {
            index: str(audio.get_host_api_info_by_index(index).get("name", ""))
            for index in range(audio.get_host_api_count())
        }
        for kind, device_name, loopback in (
            ("microphone", microphone, False),
            ("system", system_audio, True),
        ):
            if not device_name:
                continue
            device = best_input_device(
                devices,
                str(device_name),
                loopback=loopback,
                host_api_names=host_api_names,
            )
            if device is None:
                continue
            channels = max(1, min(2, int(device.get("maxInputChannels", 1))))
            rate = int(device.get("defaultSampleRate", 48_000))
            try:
                stream = audio.open(
                    format=pyaudio.paInt16,
                    channels=channels,
                    rate=rate,
                    input=True,
                    input_device_index=int(device["index"]),
                    frames_per_buffer=1024,
                )
            except Exception:
                continue
            streams.append((kind, stream))
        # Pacing comes from the reads themselves: stream.read blocks until a
        # full buffer of audio exists, which is real time. Sleeping on top of
        # that would consume audio more slowly than it arrives, so the device
        # buffer would grow without bound and the reported level would fall
        # further and further behind what the user is actually saying.
        #
        # Output is rate limited instead, reporting the peak seen since the
        # last line so short sounds are never missed between reports.
        emit_interval = 1.0 / METER_SAMPLES_PER_SECOND
        peak = {"microphone": 0.0, "system": 0.0}
        last_emit = 0.0
        while streams:
            read_failed = False
            for kind, stream in streams:
                try:
                    level = pcm_level(stream.read(1024, exception_on_overflow=False))
                except Exception:
                    level, read_failed = 0.0, True
                if level > peak[kind]:
                    peak[kind] = level

            now = time.monotonic()
            if now - last_emit >= emit_interval:
                print(f"{peak['microphone']:.4f},{peak['system']:.4f}", flush=True)
                last_emit = now
                peak["microphone"] = 0.0
                peak["system"] = 0.0

            if read_failed:
                # A failing read returns instantly, so without this the loop
                # becomes a hot spin. Only applies when reads are not pacing.
                time.sleep(emit_interval)
    except (BrokenPipeError, OSError):
        pass
    finally:
        for _kind, stream in streams:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
        audio.terminate()
    return 0
