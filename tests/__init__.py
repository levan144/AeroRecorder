"""AeroRecorder tests.

Tests construct the application and deliberately trigger failures, which
would otherwise write into the real user-facing logs under %LOCALAPPDATA%.
The flag below keeps test noise out of those files.
"""

import os

os.environ.setdefault("AERORECORDER_SUPPRESS_ERROR_LOG", "1")
