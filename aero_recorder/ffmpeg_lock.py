"""Read and validate ffmpeg.lock.json.

The lockfile is the single source of truth for which FFmpeg binary
AeroRecorder ships. The fetch script, the build, CI, and the license page all
read it, so a malformed lockfile must fail loudly here rather than produce a
build with the wrong or an unverified binary.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .runtime import application_root

LOCKFILE_NAME = "ffmpeg.lock.json"
REQUIRED_FIELDS = (
    "version",
    "build",
    "url",
    "sha256",
    "size_bytes",
    "license",
    "source_url",
    "archive_member",
)
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

# Path fragments that mean the URL can change underneath us. A pinned hash
# against a moving URL just guarantees the build breaks at a random moment.
_FLOATING_URL_MARKERS = (
    "/latest/",
    "/latest",
    "-latest-",
    "release-essentials",
    "release-full",
    "git-essentials",
    "git-full",
)


class LockfileError(RuntimeError):
    """Raised when ffmpeg.lock.json is absent, malformed, or invalid."""


@dataclass(frozen=True, slots=True)
class FFmpegLock:
    version: str
    build: str
    url: str
    sha256: str
    size_bytes: int
    license: str
    source_url: str
    archive_member: str
    is_archive: bool = True
    license_member: str = ""
    license_url: str = ""

    @property
    def cache_key(self) -> str:
        return self.sha256


def default_lock_path() -> Path:
    return application_root() / LOCKFILE_NAME


def load_lock(path: Path | None = None) -> FFmpegLock:
    location = path or default_lock_path()
    try:
        payload = json.loads(location.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LockfileError(f"{LOCKFILE_NAME} was not found at {location}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise LockfileError(f"{location} could not be read: {exc}") from exc

    if not isinstance(payload, dict):
        raise LockfileError(f"{location} must contain a JSON object")

    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        raise LockfileError(f"{location} is missing required field(s): {', '.join(missing)}")

    digest = str(payload["sha256"]).strip().lower()
    if not SHA256_PATTERN.match(digest):
        raise LockfileError(
            f"{location}: sha256 must be 64 lowercase hexadecimal characters, "
            f"got {len(digest)} character(s)"
        )

    url = str(payload["url"]).strip()
    if not url.startswith("https://"):
        raise LockfileError(f"{location}: url must use https, got {url!r}")
    lowered = url.lower()
    for marker in _FLOATING_URL_MARKERS:
        if marker in lowered:
            raise LockfileError(
                f"{location}: url must be immutable, but {marker!r} means it "
                f"can change without notice: {url}"
            )

    try:
        size = int(payload["size_bytes"])
    except (TypeError, ValueError) as exc:
        raise LockfileError(f"{location}: size_bytes must be an integer") from exc

    return FFmpegLock(
        version=str(payload["version"]),
        build=str(payload["build"]),
        url=url,
        sha256=digest,
        size_bytes=size,
        license=str(payload["license"]),
        source_url=str(payload["source_url"]),
        archive_member=str(payload["archive_member"]),
        is_archive=bool(payload.get("is_archive", True)),
        license_member=str(payload.get("license_member", "")),
        license_url=str(payload.get("license_url", "")),
    )
