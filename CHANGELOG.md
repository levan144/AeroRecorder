# Changelog

All notable changes to AeroRecorder are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-09-13

First public release.

### Added

- Full-screen, region, and window capture, with per-monitor and all-monitor support
- Microphone and Windows system-audio recording with live level meters
- Optional FFmpeg noise reduction for microphone input
- Hardware encoding via NVIDIA NVENC, AMD AMF, and Intel Quick Sync, with automatic detection and CPU fallback
- Pause and resume that excludes paused time from the result
- Configurable 0, 3, 5, or 10 second countdown
- Editable global start/stop and pause/resume shortcuts
- Optional circular or rectangular webcam overlay in any corner
- Blur or cover any number of privacy-sensitive screen regions
- Optional pointer halo with animated click rings
- Timed 5 to 60 second GIF capture with optimised palettes
- Recordings library with play, rename, reveal, copy path, and delete
- Compact always-on-top recording bar with pause, mute, and stop
- Windows system-tray icon
- Small file, Balanced, High quality, Presentation, and Gaming presets
- Portable build that stores settings beside the application
- Update notifications from GitHub Releases, with a setting to disable them
- License information in Settings → About → Licenses

[Unreleased]: https://github.com/levan144/AeroRecorder/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/levan144/AeroRecorder/releases/tag/v1.0.0
