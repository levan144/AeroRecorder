from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aero_recorder.licenses import (
    LICENSE_FILES,
    license_document,
    read_license,
)


class LicenseDiscoveryTests(unittest.TestCase):
    def test_known_documents_are_declared(self) -> None:
        names = {entry.filename for entry in LICENSE_FILES}
        self.assertEqual(
            names,
            {"LICENSE", "LICENSE-THIRD-PARTY.md"},
        )

    def test_document_is_read_from_the_application_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "LICENSE").write_text("PolyForm text", encoding="utf-8")
            with patch("aero_recorder.licenses.application_root", return_value=root):
                self.assertEqual(read_license("LICENSE"), "PolyForm text")

    def test_missing_document_reports_rather_than_raising(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("aero_recorder.licenses.application_root", return_value=root):
                text = read_license("LICENSE")
        self.assertIn("could not be found", text)

    def test_bundle_root_is_searched_before_the_application_root(self) -> None:
        with (
            tempfile.TemporaryDirectory() as bundle_dir,
            tempfile.TemporaryDirectory() as app_dir,
        ):
            bundle, app = Path(bundle_dir), Path(app_dir)
            (bundle / "LICENSE").write_text("bundled", encoding="utf-8")
            (app / "LICENSE").write_text("on disk", encoding="utf-8")
            with patch("aero_recorder.licenses.application_root", return_value=app):
                with patch("aero_recorder.licenses.bundle_root", return_value=bundle):
                    self.assertEqual(read_license("LICENSE"), "bundled")

    def test_license_document_returns_title_and_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "LICENSE-THIRD-PARTY.md").write_text("# Third-Party", encoding="utf-8")
            with patch("aero_recorder.licenses.application_root", return_value=root):
                title, text = license_document("LICENSE-THIRD-PARTY.md")
        self.assertEqual(title, "Third-party licenses")
        self.assertEqual(text, "# Third-Party")


class RepositoryLicenseTests(unittest.TestCase):
    def test_every_declared_document_exists_in_the_repository(self) -> None:
        from aero_recorder.runtime import application_root

        for entry in LICENSE_FILES:
            with self.subTest(document=entry.filename):
                self.assertTrue(
                    (application_root() / entry.filename).is_file(),
                    f"{entry.filename} is declared but missing from the repository",
                )

    def test_the_real_documents_are_readable_and_non_empty(self) -> None:
        for entry in LICENSE_FILES:
            with self.subTest(document=entry.filename):
                title, text = license_document(entry.filename)
                self.assertTrue(title)
                self.assertNotIn("could not be found", text)
                self.assertGreater(len(text.strip()), 100)


class VersionSourceTests(unittest.TestCase):
    def test_version_is_semver(self) -> None:

        from aero_recorder import __version__

        self.assertRegex(__version__, r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")

    def test_version_is_one_point_zero_or_later(self) -> None:
        from aero_recorder import __version__

        major = int(__version__.split(".")[0])
        self.assertGreaterEqual(major, 1)

    def test_installer_script_does_not_hardcode_a_version(self) -> None:
        from aero_recorder.runtime import application_root

        script = (application_root() / "installer" / "AeroRecorder.iss").read_text(encoding="utf-8")
        self.assertNotIn('#define MyAppVersion "', script)
        self.assertIn("MyAppVersion", script)


if __name__ == "__main__":
    unittest.main()
