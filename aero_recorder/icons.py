"""Vector navigation icons drawn directly onto a Tk canvas.

Drawn rather than loaded from image files because:

- They scale to any DPI without shipping 1x/2x/3x bitmaps.
- They recolour instantly for hover and active states, which a PhotoImage
  cannot do without a second asset.
- No binary assets to bundle, licence, or wire into PyInstaller.

Every drawer receives a square box of ``size`` pixels and works in fractions
of that box, so the same code renders correctly at 16px or 48px.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    import tkinter as tk


IconDrawer = Callable[["tk.Canvas", float, str], None]


def _stroke(size: float) -> float:
    """Line weight that stays visually consistent as the icon scales."""
    return max(1.0, round(size / 13.0))


def draw_capture(canvas: tk.Canvas, size: float, color: str) -> None:
    """A camera body with a lens, for the capture page."""
    width = _stroke(size)
    # Body
    canvas.create_rectangle(
        size * 0.10,
        size * 0.28,
        size * 0.90,
        size * 0.80,
        outline=color,
        width=width,
    )
    # Viewfinder bump
    canvas.create_line(
        size * 0.34,
        size * 0.28,
        size * 0.42,
        size * 0.17,
        fill=color,
        width=width,
    )
    canvas.create_line(
        size * 0.42,
        size * 0.17,
        size * 0.62,
        size * 0.17,
        fill=color,
        width=width,
    )
    canvas.create_line(
        size * 0.62,
        size * 0.17,
        size * 0.70,
        size * 0.28,
        fill=color,
        width=width,
    )
    # Lens
    canvas.create_oval(
        size * 0.37,
        size * 0.40,
        size * 0.63,
        size * 0.66,
        outline=color,
        width=width,
    )


def draw_library(canvas: tk.Canvas, size: float, color: str) -> None:
    """A film strip, for the recordings library."""
    width = _stroke(size)
    canvas.create_rectangle(
        size * 0.12,
        size * 0.20,
        size * 0.88,
        size * 0.80,
        outline=color,
        width=width,
    )
    # Sprocket holes down both edges
    for index in range(3):
        top = size * (0.29 + index * 0.18)
        bottom = top + size * 0.09
        canvas.create_rectangle(
            size * 0.20,
            top,
            size * 0.30,
            bottom,
            outline=color,
            width=max(1.0, width * 0.7),
        )
        canvas.create_rectangle(
            size * 0.70,
            top,
            size * 0.80,
            bottom,
            outline=color,
            width=max(1.0, width * 0.7),
        )
    # Centre divider
    canvas.create_line(
        size * 0.50,
        size * 0.20,
        size * 0.50,
        size * 0.80,
        fill=color,
        width=max(1.0, width * 0.7),
    )


def draw_setup(canvas: tk.Canvas, size: float, color: str) -> None:
    """Sliders, for the settings page.

    Sliders rather than the usual gear: they read more clearly than a cog at
    small sizes, where a gear's teeth collapse into a blur.
    """
    width = _stroke(size)
    knob = size * 0.085

    rows = ((0.28, 0.64), (0.50, 0.36), (0.72, 0.56))
    for row_y, knob_x in rows:
        canvas.create_line(
            size * 0.14,
            size * row_y,
            size * 0.86,
            size * row_y,
            fill=color,
            width=max(1.0, width * 0.8),
        )
        canvas.create_oval(
            size * knob_x - knob,
            size * row_y - knob,
            size * knob_x + knob,
            size * row_y + knob,
            outline=color,
            fill=color,
            width=width,
        )


ICON_DRAWERS: dict[str, IconDrawer] = {
    "capture": draw_capture,
    "library": draw_library,
    "setup": draw_setup,
}


def draw_icon(canvas: tk.Canvas, name: str, size: float, color: str) -> None:
    """Clear the canvas and draw ``name`` in ``color``.

    An unknown name leaves the canvas empty rather than raising, so a typo in
    a nav definition degrades to a blank icon instead of crashing startup.
    """
    canvas.delete("all")
    drawer = ICON_DRAWERS.get(name)
    if drawer is None:
        return
    drawer(canvas, size, color)
