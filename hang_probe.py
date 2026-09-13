import ctypes, subprocess, time
from ctypes import wintypes

u32 = ctypes.windll.user32
u32.IsHungAppWindow.argtypes = [wintypes.HWND]
u32.IsHungAppWindow.restype = wintypes.BOOL

EXE = r"dist\AeroRecorder\AeroRecorder.exe"
p = subprocess.Popen([EXE])
print(f"launched pid {p.pid}")

def windows_of(pid):
    out = []
    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(h, l):
        want = wintypes.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(want))
        if want.value == pid:
            buf = ctypes.create_unicode_buffer(256)
            u32.GetWindowTextW(h, buf, 256)
            cls = ctypes.create_unicode_buffer(256)
            u32.GetClassNameW(h, cls, 256)
            out.append((h, buf.value, cls.value, bool(u32.IsWindowVisible(h))))
        return True
    u32.EnumWindows(cb, 0)
    return out

for wait in (4, 8, 14, 20, 28):
    time.sleep(wait - (0 if wait == 4 else 0))
    wins = windows_of(p.pid)
    print(f"\n--- t={wait}s   alive={p.poll() is None}")
    for h, title, cls, vis in wins:
        hung = bool(u32.IsHungAppWindow(h))
        print(f"    hwnd={h:<9} vis={int(vis)} hung={'YES' if hung else 'no '} cls={cls:<14} title={title!r}")
    if not wins:
        print("    (no top-level windows found)")
    time.sleep(0)
    break

# now watch over time
for i in range(6):
    time.sleep(4)
    wins = windows_of(p.pid)
    line = []
    for h, title, cls, vis in wins:
        if cls.startswith("Tk") or "Aero" in title:
            line.append(f"{cls}:hung={'Y' if u32.IsHungAppWindow(h) else 'n'}")
    print(f"  t={8+i*4:>3}s  {' '.join(line) if line else '(none)'}")

p.terminate()
try: p.wait(timeout=5)
except Exception: p.kill()
print("\nterminated")
