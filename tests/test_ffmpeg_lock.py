from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aero_recorder.ffmpeg_lock import (
    FFmpegLock,
    LockfileError,
    load_lock,
)


VALID = {
    "version": "7.1",
    "build": "test-build-1",
    "url": "https://example.com/releases/download/v1/ffmpeg.zip",
    "sha256": "a" * 64,
    "size_bytes": 34000000,
    "license": "GPL-3.0",
    "source_url": "https://example.com/source",
    "archive_member": "bin/ffmpeg.exe",
}


def _write(payload: dict) -> Path:
    directory = Path(tempfile.mkdtemp())
    path = directory / "ffmpeg.lock.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class LockfileTests(unittest.TestCase):
    def test_valid_lockfile_loads(self) -> None:
        lock = load_lock(_write(VALID))
        self.assertIsInstance(lock, FFmpegLock)
        self.assertEqual(lock.version, "7.1")
        self.assertEqual(lock.sha256, "a" * 64)
        self.assertEqual(lock.size_bytes, 34000000)
        self.assertEqual(lock.archive_member, "bin/ffmpeg.exe")

    def test_missing_field_is_rejected(self) -> None:
        payload = dict(VALID)
        del payload["sha256"]
        with self.assertRaises(LockfileError) as context:
            load_lock(_write(payload))
        self.assertIn("sha256", str(context.exception))

    def test_short_hash_is_rejected(self) -> None:
        payload = {**VALID, "sha256": "abc123"}
        with self.assertRaises(LockfileError) as context:
            load_lock(_write(payload))
        self.assertIn("64", str(context.exception))

    def test_non_hex_hash_is_rejected(self) -> None:
        payload = {**VALID, "sha256": "z" * 64}
        with self.assertRaises(LockfileError):
            load_lock(_write(payload))

    def test_hash_is_normalised_to_lowercase(self) -> None:
        payload = {**VALID, "sha256": "A" * 64}
        self.assertEqual(load_lock(_write(payload)).sha256, "a" * 64)

    def test_insecure_url_is_rejected(self) -> None:
        payload = {**VALID, "url": "http://example.com/ffmpeg.exe"}
        with self.assertRaises(LockfileError) as context:
            load_lock(_write(payload))
        self.assertIn("https", str(context.exception))

    def test_floating_url_is_rejected(self) -> None:
        """A URL that can change under us defeats the whole point of pinning."""
        for bad in (
            "https://example.com/releases/download/latest/ffmpeg.zip",
            "https://example.com/ffmpeg-release-essentials.zip",
        ):
            with self.subTest(url=bad):
                with self.assertRaises(LockfileError) as context:
                    load_lock(_write({**VALID, "url": bad}))
                self.assertIn("immutable", str(context.exception).lower())

    def test_missing_file_is_rejected(self) -> None:
        with self.assertRaises(LockfileError):
            load_lock(Path(tempfile.mkdtemp()) / "absent.json")

    def test_malformed_json_is_rejected(self) -> None:
        directory = Path(tempfile.mkdtemp())
        path = directory / "ffmpeg.lock.json"
        path.write_text("{not json", encoding="utf-8")
        with self.assertRaises(LockfileError):
            load_lock(path)

    def test_cache_key_is_the_hash(self) -> None:
        self.assertEqual(load_lock(_write(VALID)).cache_key, "a" * 64)

    def test_bare_binary_downloads_are_supported(self) -> None:
        """A trimmed build may be published as a bare .exe, not an archive."""
        payload = {**VALID, "archive_member": "ffmpeg.exe", "is_archive": False}
        lock = load_lock(_write(payload))
        self.assertFalse(lock.is_archive)

    def test_archive_is_the_default(self) -> None:
        self.assertTrue(load_lock(_write(VALID)).is_archive)


class RepositoryLockfileTests(unittest.TestCase):
    def test_the_checked_in_lockfile_is_valid(self) -> None:
        from aero_recorder.ffmpeg_lock import default_lock_path

        lock = load_lock(default_lock_path())
        self.assertEqual(lock.license, "GPL-3.0")
        self.assertTrue(lock.url.startswith("https://"))


if __name__ == "__main__":
    unittest.main()
