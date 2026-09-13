from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from .runtime import application_root


@dataclass(frozen=True, slots=True)
class LicenseFile:
    filename: str
    title: str


LICENSE_FILES: tuple[LicenseFile, ...] = (
    LicenseFile("LICENSE", "AeroRecorder license"),
    LicenseFile("LICENSE-THIRD-PARTY.md", "Third-party licenses"),
)


def bundle_root() -> Path | None:
    """Return the PyInstaller extraction directory, or None when not frozen."""
    location = getattr(sys, "_MEIPASS", None)
    return Path(location) if location else None


def _candidate_paths(filename: str) -> list[Path]:
    candidates: list[Path] = []
    bundle = bundle_root()
    if bundle is not None:
        candidates.append(bundle / filename)
    candidates.append(application_root() / filename)
    return candidates


def read_license(filename: str) -> str:
    """Return the text of a bundled license document.

    Never raises. A missing or unreadable document yields an explanatory
    message so that the About dialog degrades rather than crashing.
    """
    for candidate in _candidate_paths(filename):
        try:
            return candidate.read_text(encoding="utf-8")
        except (FileNotFoundError, OSError, UnicodeDecodeError):
            continue
    return (
        f"{filename} could not be found in this installation.\n\n"
        "The full text is available at "
        "https://github.com/levan144/AeroRecorder"
    )


def license_document(filename: str) -> tuple[str, str]:
    """Return the display title and text for a license document."""
    title = next(
        (entry.title for entry in LICENSE_FILES if entry.filename == filename),
        filename,
    )
    return title, read_license(filename)
