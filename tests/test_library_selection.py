from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AERORECORDER_SUPPRESS_ERROR_LOG", "1")

from aero_recorder.models import RecordingResult  # noqa: E402


class LibraryAutoSelectTests(unittest.TestCase):
    """After a recording is saved the library should open on that recording.

    Finishing a capture and then having to find the new file yourself is a
    needless step; the one recording the user just made is the one they want.
    """

    @classmethod
    def setUpClass(cls) -> None:
        import tkinter as tk

        try:
            cls.root = tk.Tk()
            cls.root.withdraw()
        except tk.TclError as exc:  # pragma: no cover - headless
            raise unittest.SkipTest(f"no display: {exc}") from exc

        from aero_recorder.ui import AeroRecorderApp

        cls.directory = tempfile.TemporaryDirectory()
        cls.app = AeroRecorderApp(cls.root)
        cls.app.settings.output_folder = cls.directory.name
        cls._settle()

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.root.destroy()
        except Exception:  # pragma: no cover
            pass
        cls.directory.cleanup()

    @classmethod
    def _settle(cls, ticks: int = 25) -> None:
        import time

        for _ in range(ticks):
            try:
                cls.root.update()
            except Exception:
                pass
            time.sleep(0.005)

    def _make_recording(self, name: str) -> Path:
        path = Path(self.directory.name) / name
        path.write_bytes(b"\x00" * 2048)
        return path

    def test_saving_a_recording_opens_the_library(self) -> None:
        path = self._make_recording("Aero Recording open-library.mp4")
        self.app.current_page = "recorder"
        self.app._recording_finished(RecordingResult(path, True, ""))
        self._settle()
        self.assertEqual(self.app.current_page, "library")

    def test_the_new_recording_is_selected(self) -> None:
        path = self._make_recording("Aero Recording selected.mp4")
        self.app._recording_finished(RecordingResult(path, True, ""))
        self._settle()
        self.assertEqual(self.app._selected_recording(), path)

    def test_selecting_enables_the_library_actions(self) -> None:
        path = self._make_recording("Aero Recording actions.mp4")
        self.app._recording_finished(RecordingResult(path, True, ""))
        self._settle()
        self.assertTrue(self.app.play_button.enabled)
        self.assertTrue(self.app.delete_button.enabled)

    def test_the_newest_recording_wins_over_older_ones(self) -> None:
        self._make_recording("Aero Recording older-a.mp4")
        self._make_recording("Aero Recording older-b.mp4")
        newest = self._make_recording("Aero Recording newest.mp4")
        self.app._recording_finished(RecordingResult(newest, True, ""))
        self._settle()
        self.assertEqual(self.app._selected_recording(), newest)

    def test_select_recording_reports_whether_it_found_the_path(self) -> None:
        path = self._make_recording("Aero Recording findable.mp4")
        self.app._show_page("library")
        self._settle()
        self.assertTrue(self.app._select_recording(path))
        missing = Path(self.directory.name) / "not-on-disk.mp4"
        self.assertFalse(self.app._select_recording(missing))

    def test_a_failed_recording_does_not_switch_pages(self) -> None:
        self.app._show_page("recorder")
        self._settle()
        missing = Path(self.directory.name) / "failed.mp4"
        self.app._recording_finished(RecordingResult(missing, False, "boom"))
        self._settle()
        self.assertEqual(
            self.app.current_page,
            "recorder",
            "a failed recording has nothing to show in the library",
        )

    def test_a_failed_recording_does_not_open_a_modal_inside_the_pump(self) -> None:
        """A modal here would stall the UI queue, as it did for update checks."""
        import aero_recorder.ui as uimod

        calls: list[str] = []
        original = uimod.messagebox.showerror
        uimod.messagebox.showerror = lambda *a, **k: calls.append("inline") or "ok"
        try:
            missing = Path(self.directory.name) / "failed2.mp4"
            self.app._recording_finished(RecordingResult(missing, False, "boom"))
            inline = len(calls)
        finally:
            uimod.messagebox.showerror = original
        self.assertEqual(inline, 0, "showerror was called synchronously")


if __name__ == "__main__":
    unittest.main()
