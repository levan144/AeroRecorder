"""Single-instance enforcement for AeroRecorder.

Only one AeroRecorder window should ever exist. Launching the application a
second time hands focus back to the running copy instead of opening another
window and competing for the same hotkeys, tray icon, and settings file.

The mechanism is a Windows named mutex plus a registered broadcast message,
both from the Win32 API. No sockets, no lock files, and no third-party
dependency.

Why a named mutex rather than a lock file:

- The kernel releases it automatically when the process dies, including on a
  crash or a kill. A lock file left behind by a crash would wedge the
  application permanently.
- Acquisition is atomic, so two copies launched simultaneously cannot both
  believe they are first.

Why the name is scoped to ``Local\\``:

- ``Local\\`` places the object in the current logon session's namespace.
  A ``Global\\`` name is visible to every session on the machine, which would
  let one user's AeroRecorder block another user's, and would let any
  unprivileged process squat the name to deny service.
"""

from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from types import TracebackType

# A fixed random suffix keeps these names from colliding with any other
# program's objects. It must never change: both names are part of the
# protocol between a running copy and a newly launched one.
_UNIQUE_SUFFIX = "b7f3a1c94e2d"

MUTEX_NAME = f"Local\\AeroRecorder-SingleInstance-{_UNIQUE_SUFFIX}"
SHOW_WINDOW_MESSAGE_NAME = f"AeroRecorder-ShowWindow-{_UNIQUE_SUFFIX}"

ERROR_ALREADY_EXISTS = 183
HWND_BROADCAST = 0xFFFF


class SingleInstance:
    """Hold a named mutex for the lifetime of this process.

    ``acquire()`` returns True when this process is the first copy, and False
    when another copy already holds the name.

    On a non-Windows platform the guard always succeeds, so the application
    still runs; single-instance behaviour is a Windows feature here.
    """

    __slots__ = ("_name", "_handle")

    def __init__(self, name: str = MUTEX_NAME) -> None:
        self._name = name
        self._handle: int | None = None

    @property
    def name(self) -> str:
        return self._name

    def acquire(self) -> bool:
        if os.name != "nt":
            return True
        if self._handle is not None:
            # Already held by this instance of the guard.
            return True

        kernel32 = ctypes.windll.kernel32
        kernel32.CreateMutexW.argtypes = [
            wintypes.LPVOID,
            wintypes.BOOL,
            wintypes.LPCWSTR,
        ]
        kernel32.CreateMutexW.restype = wintypes.HANDLE

        # A NULL security descriptor gives the default DACL, which grants
        # access to this user only. That is what we want.
        handle = kernel32.CreateMutexW(None, True, self._name)
        last_error = kernel32.GetLastError()

        if not handle:
            # The mutex could not be created at all. Fail open: refusing to
            # start because of an API failure would be worse than allowing a
            # second window.
            return True

        if last_error == ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            return False

        self._handle = handle
        return True

    def release(self) -> None:
        """Release the name. Safe to call more than once."""
        handle, self._handle = self._handle, None
        if handle and os.name == "nt":
            kernel32 = ctypes.windll.kernel32
            try:
                kernel32.ReleaseMutex(handle)
            except OSError:
                pass
            try:
                kernel32.CloseHandle(handle)
            except OSError:
                pass

    def __enter__(self) -> bool:
        return self.acquire()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.release()


def show_window_message() -> int:
    """Return the registered broadcast message id, or 0 when unavailable.

    ``RegisterWindowMessageW`` returns the same id for the same string in
    every process on the system, which is exactly the handshake needed: a
    newly launched copy can address the running copy without knowing its
    window handle or process id.
    """
    if os.name != "nt":
        return 0
    try:
        user32 = ctypes.windll.user32
        user32.RegisterWindowMessageW.argtypes = [wintypes.LPCWSTR]
        user32.RegisterWindowMessageW.restype = wintypes.UINT
        return int(user32.RegisterWindowMessageW(SHOW_WINDOW_MESSAGE_NAME) or 0)
    except (AttributeError, OSError):
        return 0


def broadcast_show_window() -> bool:
    """Ask an already-running AeroRecorder to show itself.

    Returns True when the message was posted. Only AeroRecorder registers this
    message string, so other applications ignore it.
    """
    if os.name != "nt":
        return False
    message = show_window_message()
    if not message:
        return False
    try:
        user32 = ctypes.windll.user32
        user32.PostMessageW.argtypes = [
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        return bool(user32.PostMessageW(HWND_BROADCAST, message, 0, 0))
    except (AttributeError, OSError):
        return False
