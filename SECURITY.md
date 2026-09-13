# Security Policy

## Supported versions

Only the latest release receives security fixes.

| Version | Supported |
|---|---|
| 1.0.x   | Yes |
| < 1.0   | No  |

## Reporting a vulnerability

**Please do not open a public issue for a security vulnerability.**

Report it privately through
[GitHub Security Advisories](https://github.com/levan144/AeroRecorder/security/advisories/new),
or by email to **levanjavakhishvili.1@gmail.com**.

Please include a description of the issue, the steps to reproduce it, the affected
version, and the impact as you understand it.

You can expect an acknowledgement within 5 days and an assessment within 14 days.
Confirmed vulnerabilities are fixed in the next release, and you will be credited
unless you prefer otherwise.

## Scope

AeroRecorder records locally and uploads nothing. Its only outbound network request
is a version check against the GitHub Releases API, which can be disabled in
Settings.

The FFmpeg binary is a third-party component. Vulnerabilities in FFmpeg itself should
be reported to the FFmpeg project; AeroRecorder will pick up the fix by upgrading its
pinned build.
