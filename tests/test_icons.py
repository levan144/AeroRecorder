from __future__ import annotations

import unittest

from aero_recorder.icons import ICON_DRAWERS, draw_icon


class IconRegistryTests(unittest.TestCase):
    def test_every_navigation_icon_is_available(self) -> None:
        self.assertEqual(
            set(ICON_DRAWERS),
            {"capture", "library", "setup"},
        )

    def test_drawers_are_callable(self) -> None:
        for name, drawer in ICON_DRAWERS.items():
            with self.subTest(icon=name):
                self.assertTrue(callable(drawer))


class DrawingTests(unittest.TestCase):
    """Drawing needs a real Tk canvas, so these build one."""

    @classmethod
    def setUpClass(cls) -> None:
        import tkinter as tk

        try:
            cls.root = tk.Tk()
            cls.root.withdraw()
        except tk.TclError as exc:  # pragma: no cover - headless CI
            raise unittest.SkipTest(f"no display available: {exc}") from exc

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.root.destroy()
        except Exception:  # pragma: no cover
            pass

    def _canvas(self):
        import tkinter as tk

        return tk.Canvas(self.root, width=26, height=26, highlightthickness=0)

    def test_each_icon_draws_at_least_one_shape(self) -> None:
        for name in ICON_DRAWERS:
            with self.subTest(icon=name):
                canvas = self._canvas()
                draw_icon(canvas, name, 26, "#ffffff")
                self.assertGreater(
                    len(canvas.find_all()),
                    0,
                    f"{name} drew nothing",
                )

    def test_redrawing_replaces_rather_than_accumulates(self) -> None:
        canvas = self._canvas()
        draw_icon(canvas, "capture", 26, "#ffffff")
        first = len(canvas.find_all())
        draw_icon(canvas, "capture", 26, "#ff0000")
        second = len(canvas.find_all())
        self.assertEqual(
            first,
            second,
            "redrawing must clear the canvas, not stack shapes on top",
        )

    def test_shapes_stay_within_the_icon_box(self) -> None:
        size = 26
        for name in ICON_DRAWERS:
            with self.subTest(icon=name):
                canvas = self._canvas()
                draw_icon(canvas, name, size, "#ffffff")
                for item in canvas.find_all():
                    x1, y1, x2, y2 = canvas.bbox(item)
                    self.assertGreaterEqual(x1, -2, f"{name} overflows left")
                    self.assertGreaterEqual(y1, -2, f"{name} overflows top")
                    self.assertLessEqual(x2, size + 2, f"{name} overflows right")
                    self.assertLessEqual(y2, size + 2, f"{name} overflows bottom")

    def test_icons_scale_with_the_requested_size(self) -> None:
        small = self._canvas()
        draw_icon(small, "setup", 16, "#ffffff")
        small_box = small.bbox("all")

        large = self._canvas()
        draw_icon(large, "setup", 48, "#ffffff")
        large_box = large.bbox("all")

        self.assertLess(
            small_box[2] - small_box[0],
            large_box[2] - large_box[0],
            "a larger requested size must produce a larger drawing",
        )

    def test_unknown_icon_is_ignored_rather_than_raising(self) -> None:
        canvas = self._canvas()
        draw_icon(canvas, "does-not-exist", 26, "#ffffff")  # must not raise
        self.assertEqual(len(canvas.find_all()), 0)


if __name__ == "__main__":
    unittest.main()
