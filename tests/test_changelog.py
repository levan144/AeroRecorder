from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from get_changelog_section import ChangelogError, extract_section  # noqa: E402

SAMPLE = """# Changelog

All notable changes are documented here.

## [Unreleased]

### Added

- Something in flight

## [1.1.0] - 2026-10-01

### Added

- A second feature

### Fixed

- A bug

## [1.0.0] - 2026-09-13

First public release.

### Added

- The first feature

[Unreleased]: https://example.com/compare
[1.1.0]: https://example.com/tag/v1.1.0
[1.0.0]: https://example.com/tag/v1.0.0
"""


class ExtractSectionTests(unittest.TestCase):
    def test_middle_version_stops_at_the_next_heading(self) -> None:
        section = extract_section(SAMPLE, "1.1.0")
        self.assertIn("A second feature", section)
        self.assertIn("A bug", section)
        self.assertNotIn("The first feature", section)
        self.assertNotIn("Something in flight", section)

    def test_last_version_stops_before_the_link_block(self) -> None:
        section = extract_section(SAMPLE, "1.0.0")
        self.assertIn("The first feature", section)
        self.assertIn("First public release.", section)
        self.assertNotIn("[Unreleased]: https://", section)

    def test_version_heading_itself_is_not_included(self) -> None:
        section = extract_section(SAMPLE, "1.0.0")
        self.assertFalse(section.lstrip().startswith("## ["))

    def test_leading_v_is_accepted(self) -> None:
        self.assertEqual(extract_section(SAMPLE, "v1.0.0"), extract_section(SAMPLE, "1.0.0"))

    def test_unknown_version_raises(self) -> None:
        with self.assertRaises(ChangelogError) as context:
            extract_section(SAMPLE, "9.9.9")
        self.assertIn("9.9.9", str(context.exception))

    def test_empty_section_raises(self) -> None:
        text = "# Changelog\n\n## [1.0.0] - 2026-09-13\n\n## [0.9.0] - 2026-01-01\n\n- old\n"
        with self.assertRaises(ChangelogError) as context:
            extract_section(text, "1.0.0")
        self.assertIn("empty", str(context.exception).lower())

    def test_result_has_no_leading_or_trailing_blank_lines(self) -> None:
        section = extract_section(SAMPLE, "1.1.0")
        self.assertEqual(section, section.strip())


class RepositoryChangelogTests(unittest.TestCase):
    def test_the_real_changelog_has_a_section_for_the_current_version(self) -> None:
        """Makes it impossible to tag a release whose changelog section is missing."""
        from aero_recorder import __version__

        root = Path(__file__).resolve().parent.parent
        text = (root / "CHANGELOG.md").read_text(encoding="utf-8")
        section = extract_section(text, __version__)
        self.assertTrue(section.strip())


class CommandLineTests(unittest.TestCase):
    def test_non_ascii_survives_a_cp1252_console(self) -> None:
        """Windows consoles default to cp1252; the changelog contains arrows.

        The release workflow runs this on a Windows runner, so an encoding
        crash here would fail the release itself.
        """
        import os
        import subprocess
        import tempfile

        text = "# Changelog\n\n## [1.0.0] - 2026-09-13\n\n- Settings → About\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CHANGELOG.md"
            path.write_text(text, encoding="utf-8")
            script = Path(__file__).resolve().parent.parent / "scripts" / "get_changelog_section.py"
            result = subprocess.run(
                [sys.executable, str(script), "1.0.0", "--file", str(path)],
                capture_output=True,
                env={**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"},
                timeout=30,
            )
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertIn("→".encode("utf-8"), result.stdout)


if __name__ == "__main__":
    unittest.main()
