# Third-Party Licenses

AeroRecorder is distributed under the PolyForm Noncommercial License 1.0.0 (see `LICENSE`).

It redistributes the third-party components listed below, each under its own license.
Nothing here restricts your rights under those licenses.

---

## FFmpeg

- **License:** GNU General Public License version 3 or later (GPL-3.0-or-later)
- **Website:** https://ffmpeg.org
- **Full license text:** `tools/FFMPEG-LICENSE.txt`
- **Source offer:** `tools/FFMPEG-SOURCE-OFFER.txt`

FFmpeg performs all video and audio encoding in AeroRecorder.

AeroRecorder invokes `ffmpeg.exe` as a **separate process** through the operating
system. It does not link against FFmpeg libraries and does not share an address space
with FFmpeg. Under GPL-3.0 section 5, this constitutes mere aggregation, so FFmpeg's
license does not extend to AeroRecorder's own source code.

The obligation that does apply is to offer FFmpeg's corresponding source code.
See `tools/FFMPEG-SOURCE-OFFER.txt`, distributed alongside the binary.

---

## PyAudioWPatch

- **License:** Apache License 2.0
- **Website:** https://github.com/s0d3s/PyAudioWPatch

Used for WASAPI loopback capture, which is how AeroRecorder records Windows system
audio without requiring a virtual audio driver.

```
Copyright (c) 2022 S0D3S

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

AeroRecorder redistributes PyAudioWPatch unmodified. The upstream distribution
contains no `NOTICE` file.

---

## PyAudio

- **License:** MIT
- **Website:** https://people.csail.mit.edu/hubert/pyaudio/

PyAudioWPatch is a fork of PyAudio, so PyAudio's original copyright applies to the
portions it derives from.

```
Copyright (c) 2006 Hubert Pham

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

---

## PortAudio

- **License:** MIT
- **Website:** https://www.portaudio.com

PortAudio is statically compiled into the PyAudioWPatch extension module
(`_portaudiowpatch`), and is therefore redistributed with AeroRecorder.

```
Copyright (c) 1999-2011 Ross Bencina and Phil Burk

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

---

## Python

- **License:** Python Software Foundation License Version 2
- **Website:** https://www.python.org
- **Full text:** https://docs.python.org/3/license.html

The Python runtime is embedded into AeroRecorder builds by PyInstaller.

```
Copyright (c) 2001-2026 Python Software Foundation. All Rights Reserved.
```

---

## Tcl/Tk

- **License:** Tcl/Tk License (BSD-style)
- **Website:** https://www.tcl-lang.org
- **Full text:** https://www.tcl-lang.org/software/tcltk/license.html

The Tcl and Tk libraries are embedded into AeroRecorder builds by PyInstaller and
provide the Tkinter user interface.

```
Copyright (c) Regents of the University of California, Sun Microsystems, Inc.,
Scriptics Corporation, and other parties.

This software is copyrighted by the Regents of the University of California,
Sun Microsystems, Inc., Scriptics Corporation, and other parties. The following
terms apply to all files associated with the software unless explicitly disclaimed
in individual files.

The authors hereby grant permission to use, copy, modify, distribute, and license
this software and its documentation for any purpose, provided that existing
copyright notices are retained in all copies and that this notice is included
verbatim in any distributions.
```

---

## PyInstaller

- **License:** GPL-2.0 with a bootloader exception
- **Website:** https://pyinstaller.org

PyInstaller is a **build-time tool** and is not itself redistributed with
AeroRecorder. The bootloader it embeds into the produced executable carries an
explicit exception permitting its use in applications under any license.

No license obligation arises for AeroRecorder from PyInstaller.

---

## A note on scope

Apart from the components above, AeroRecorder is written entirely against the Python
standard library. There are no other bundled dependencies.
