# Contributing to AeroRecorder

Thank you for your interest. A few things are worth knowing before you start.

## License terms for contributions

AeroRecorder is licensed under the **PolyForm Noncommercial License 1.0.0**. It is
free to use for personal, educational, research, charitable, and government purposes,
and commercial use is not permitted.

This is a *source-available* license, not an open-source license as defined by the
Open Source Initiative, because it restricts the field of use.

By submitting a pull request you agree that your contribution is licensed under the
same terms, and that the project maintainer may relicense the project in future,
including under different terms.

If that is not acceptable to you, please open an issue to discuss before writing code.

## Reporting a bug

Open an issue using the **Bug report** template. Please include your Windows version,
your AeroRecorder version (Settings → About), what you did, what you expected, and
what happened instead.

For questions and ideas that are not defects, use **Discussions** rather than Issues.

## Development setup

Requirements: Windows 10 version 1803 or newer, and an official Python 3.11+
installation that includes Tkinter.

```powershell
python -m tkinter                                            # verify Tkinter works
powershell -ExecutionPolicy Bypass -File .\scripts\get-ffmpeg.ps1
python -m pip install -r .\requirements.txt
python main.py
```

## Before opening a pull request

```powershell
python -m unittest discover -s tests -v
python main.py --smoke-test
ruff check .
ruff format --check .
```

All four must pass. CI runs exactly these.

## Coding conventions

- `from __future__ import annotations` at the top of every module
- Type annotations on all function signatures
- Standard library only; new third-party dependencies need discussion first
- Tests must not start the GUI or record the screen
- Branch from `main`, keep branches short-lived, and delete them after merge

## Commit messages

Conventional Commits: `feat:`, `fix:`, `docs:`, `build:`, `test:`, `refactor:`, `chore:`.
Keep the subject line under 72 characters.
