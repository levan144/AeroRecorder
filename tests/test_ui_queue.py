from __future__ import annotations

import queue
import unittest


class UiQueuePumpTests(unittest.TestCase):
    """The UI queue is the only channel background work has to the interface.

    Every tray click, device scan, update check, preview result and recording
    result travels through it. If the pump ever stops, the application looks
    alive but silently ignores all of them, and the only way out is to kill
    the process. It must therefore survive a callback that raises.
    """

    @classmethod
    def setUpClass(cls) -> None:
        import os
        import tkinter as tk

        # These tests deliberately raise inside callbacks. Keep the simulated
        # failures out of the real error log.
        os.environ["AERORECORDER_SUPPRESS_ERROR_LOG"] = "1"

        try:
            cls.root = tk.Tk()
            cls.root.withdraw()
        except tk.TclError as exc:  # pragma: no cover - headless
            raise unittest.SkipTest(f"no display: {exc}") from exc

        from aero_recorder.ui import AeroRecorderApp

        cls.app = AeroRecorderApp(cls.root)
        cls._settle()

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.root.destroy()
        except Exception:  # pragma: no cover
            pass

    @classmethod
    def _settle(cls, ticks: int = 30) -> None:
        import time

        for _ in range(ticks):
            try:
                cls.root.update()
            except Exception:
                pass
            time.sleep(0.005)

    def test_callbacks_are_delivered(self) -> None:
        seen: list[str] = []
        self.app._ui_queue.put(lambda: seen.append("delivered"))
        self._settle()
        self.assertEqual(seen, ["delivered"])

    def test_a_raising_callback_does_not_stop_the_pump(self) -> None:
        seen: list[str] = []

        def poison() -> None:
            raise ValueError("simulated failure inside a queued callback")

        self.app._ui_queue.put(poison)
        self._settle()

        self.app._ui_queue.put(lambda: seen.append("after"))
        self._settle()

        self.assertEqual(
            seen,
            ["after"],
            "the pump must keep running after a callback raises",
        )

    def test_a_raising_callback_does_not_block_the_ones_behind_it(self) -> None:
        seen: list[str] = []

        def poison() -> None:
            raise RuntimeError("boom")

        self.app._ui_queue.put(lambda: seen.append("first"))
        self.app._ui_queue.put(poison)
        self.app._ui_queue.put(lambda: seen.append("third"))
        self._settle()

        self.assertEqual(
            seen,
            ["first", "third"],
            "callbacks queued behind a failing one must still run",
        )

    def test_the_queue_drains_completely(self) -> None:
        seen: list[int] = []
        for index in range(10):
            self.app._ui_queue.put(lambda i=index: seen.append(i))
        self._settle()
        self.assertEqual(len(seen), 10)
        self.assertEqual(self.app._ui_queue.qsize(), 0)

    def test_many_failures_in_a_row_still_leave_the_pump_alive(self) -> None:
        def poison() -> None:
            raise OSError("repeated failure")

        for _ in range(5):
            self.app._ui_queue.put(poison)
        self._settle()

        seen: list[str] = []
        self.app._ui_queue.put(lambda: seen.append("survived"))
        self._settle()
        self.assertEqual(seen, ["survived"])

    def test_queue_is_a_plain_queue(self) -> None:
        self.assertIsInstance(self.app._ui_queue, queue.Queue)

    def test_audio_levels_never_enter_the_ui_queue(self) -> None:
        """Level samples must be coalesced, not queued.

        The meter produces samples continuously. Queuing each one lets it
        outrun the pump, and the queue then grows without bound until tray
        clicks, preview results and even Exit are stuck behind tens of
        thousands of stale level updates.
        """
        before = self.app._ui_queue.qsize()
        for index in range(5000):
            self.app._audio_levels_from_thread(index / 5000.0, 0.5)
        after = self.app._ui_queue.qsize()

        self.assertEqual(
            after,
            before,
            f"5000 level samples added {after - before} entries to the UI queue",
        )

    def test_only_the_newest_level_sample_is_kept(self) -> None:
        self.app._audio_levels_from_thread(0.1, 0.2)
        self.app._audio_levels_from_thread(0.7, 0.8)
        self.assertEqual(self.app._latest_levels, (0.7, 0.8))

    def test_polling_applies_and_clears_the_latest_sample(self) -> None:
        self.app._audio_levels_from_thread(0.42, 0.24)
        self.app._poll_audio_levels()
        self.assertIsNone(self.app._latest_levels)
        self.assertAlmostEqual(self.app.microphone_level_var.get(), 0.42, places=4)
        self.assertAlmostEqual(self.app.system_audio_level_var.get(), 0.24, places=4)

    def test_a_flood_of_levels_does_not_starve_other_callbacks(self) -> None:
        seen: list[str] = []
        self.app._ui_queue.put(lambda: seen.append("important"))
        for index in range(20000):
            self.app._audio_levels_from_thread(0.5, 0.5)
        self._settle()
        self.assertEqual(
            seen,
            ["important"],
            "a normal callback was starved by audio level traffic",
        )

    def test_alert_does_not_open_a_dialog_inside_the_pump(self) -> None:
        """A modal opened inside the pump stalls it until dismissed.

        If the window is withdrawn to the tray that dialog can be invisible,
        which stalls the pump permanently. _alert must therefore defer the
        dialog rather than open it inline.
        """
        opened_inline: list[str] = []

        import aero_recorder.ui as uimod

        original = uimod.messagebox.showerror

        def spy(*args, **kwargs):
            opened_inline.append("called")
            return "ok"

        uimod.messagebox.showerror = spy
        try:
            # Queue an _alert exactly as a background handler would.
            self.app._ui_queue.put(
                lambda: self.app._alert("error", "Title", "Message")
            )
            # Drain once. The alert must NOT have opened yet.
            self.root.update()
            inline = len(opened_inline)
        finally:
            uimod.messagebox.showerror = original

        self.assertEqual(
            inline,
            0,
            "_alert opened a modal synchronously inside the pump",
        )

    def test_the_pump_survives_an_alert_being_queued(self) -> None:
        import aero_recorder.ui as uimod

        original = uimod.messagebox.showerror
        uimod.messagebox.showerror = lambda *a, **k: "ok"
        try:
            self.app._ui_queue.put(
                lambda: self.app._alert("error", "Title", "Message")
            )
            self._settle()
            seen: list[str] = []
            self.app._ui_queue.put(lambda: seen.append("alive"))
            self._settle()
        finally:
            uimod.messagebox.showerror = original

        self.assertEqual(seen, ["alive"], "the pump stopped after an alert")


if __name__ == "__main__":
    unittest.main()
