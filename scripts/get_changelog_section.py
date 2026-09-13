"""Extract one version's section from CHANGELOG.md.

Usage:
    python scripts/get_changelog_section.py 1.0.0
    python scripts/get_changelog_section.py v1.0.0 --file CHANGELOG.md

Used by the release workflow to turn the changelog entry into the GitHub
release body, so release notes are written once.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


class ChangelogError(RuntimeError):
    """Raised when the requested version has no usable section."""


HEADING = re.compile(r"^##\s+\[([^\]]+)\]")
LINK_DEFINITION = re.compile(r"^\[[^\]]+\]:\s+\S+")


def extract_section(text: str, version: str) -> str:
    wanted = version.lstrip("vV")
    lines = text.splitlines()

    start: int | None = None
    for index, line in enumerate(lines):
        match = HEADING.match(line)
        if match and match.group(1).lstrip("vV") == wanted:
            start = index + 1
            break

    if start is None:
        raise ChangelogError(
            f"CHANGELOG.md has no section for version {version!r}. "
            f"Add a '## [{wanted}] - YYYY-MM-DD' heading."
        )

    collected: list[str] = []
    for line in lines[start:]:
        if HEADING.match(line) or LINK_DEFINITION.match(line):
            break
        collected.append(line)

    section = "\n".join(collected).strip()
    if not section:
        raise ChangelogError(
            f"The CHANGELOG.md section for version {version!r} is empty. "
            "A release must describe what changed."
        )
    return section


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="Version to extract, with or without a leading v")
    parser.add_argument("--file", default="CHANGELOG.md", help="Path to the changelog")
    arguments = parser.parse_args()

    try:
        text = Path(arguments.file).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        print(extract_section(text, arguments.version))
    except ChangelogError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
