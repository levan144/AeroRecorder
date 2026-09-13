from pathlib import Path


project_root = Path(SPECPATH)
portable_binaries = []
portable_data = []


def _require(path: Path, remedy: str) -> Path:
    """Abort the build if a required file is absent.

    Every file here is one the application cannot ship without. Silently
    building without it produces an installer that cannot record, or one that
    violates FFmpeg's license, and neither failure shows up until a user hits
    it.
    """
    if not path.exists():
        raise SystemExit(f"\nBUILD ABORTED: {path} is missing.\n{remedy}\n")
    return path


ffmpeg = _require(
    project_root / "tools" / "ffmpeg.exe",
    "Run: powershell -ExecutionPolicy Bypass -File .\\scripts\\get-ffmpeg.ps1",
)
portable_binaries.append((str(ffmpeg), "tools"))

ffmpeg_license = _require(
    project_root / "tools" / "FFMPEG-LICENSE.txt",
    "FFmpeg is GPL-licensed and its license text must ship with the binary.\n"
    "Run: powershell -ExecutionPolicy Bypass -File .\\scripts\\get-ffmpeg.ps1 -Force",
)
portable_data.append((str(ffmpeg_license), "tools"))

source_offer = _require(
    project_root / "tools" / "FFMPEG-SOURCE-OFFER.txt",
    "GPL section 6 requires a written offer for FFmpeg's source to ship with the binary.",
)
portable_data.append((str(source_offer), "tools"))

for name in ("LICENSE", "LICENSE-THIRD-PARTY.md"):
    portable_data.append(
        (str(_require(project_root / name, f"{name} must exist before building.")), ".")
    )

portable_data.append(
    (
        str(_require(project_root / "ffmpeg.lock.json", "The FFmpeg lockfile must ship with the build.")),
        ".",
    )
)

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=portable_binaries,
    datas=portable_data,
    hiddenimports=["pyaudiowpatch"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AeroRecorder",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(project_root / "assets" / "AeroRecorder.ico"),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    manifest=str(project_root / "packaging" / "app.manifest"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AeroRecorder",
)
