"""AeroRecorder tests.

Two pieces of test-wide setup live here because they must apply before any
test module is imported.

1. Keep test noise out of the real user-facing logs under %LOCALAPPDATA%.
   Tests deliberately trigger failures and construct the application without
   a running main loop, both of which would otherwise be logged as faults.

2. Never let a test open a real dialog. Several code paths defer a
   tkinter.messagebox call to a later event-loop turn. If one fires during a
   test there is nobody to dismiss it, and the run hangs until the CI timeout
   kills it, twenty minutes later, with no diagnostic. Every dialog function
   is replaced with an immediate return: "no" for questions, None for
   notices.

3. Fail a hung run fast. faulthandler dumps every thread's stack and exits if
   the whole suite exceeds the limit, so a hang produces a traceback rather
   than a silent timeout.
"""

from __future__ import annotations

import faulthandler
import os
import sys
import tkinter.messagebox as _messagebox

os.environ.setdefault("AERORECORDER_SUPPRESS_ERROR_LOG", "1")

for _name, _result in (
    ("showerror", None),
    ("showwarning", None),
    ("showinfo", None),
    ("askyesno", False),
    ("askokcancel", False),
    ("askretrycancel", False),
    ("askquestion", "no"),
    ("askyesnocancel", None),
):
    setattr(_messagebox, _name, lambda *args, _result=_result, **kwargs: _result)

# The full suite takes well under a minute locally. A dump every two minutes
# is silent on a healthy run and shows exactly where a stuck run is stuck.
# Non-fatal so the step's own timeout still ends the job with the dumps in
# the log; a fatal dump risks the output being lost when the process exits.
faulthandler.dump_traceback_later(timeout=120, repeat=True, file=sys.stderr)
