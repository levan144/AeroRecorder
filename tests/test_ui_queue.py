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
        import tkinter as tk

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


if __name__ == "__main__":
    unittest.main()
