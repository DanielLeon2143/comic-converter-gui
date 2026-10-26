# Third-party software

`Comic Converter.exe` (the release download) contains the following software.

| Component | License | Source |
|---|---|---|
| [go-comic-converter](https://github.com/celogeek/go-comic-converter) | MIT, Copyright 2022 Celogeek | the `go-comic-converter` submodule of this repository |
| [MuPDF](https://mupdf.com) 1.28.0, through [go-fitz](https://github.com/gen2brain/go-fitz) v1.28.2 | GNU AGPL-3.0, Copyright Artifex Software | [mupdf-1.28.0-source.tar.gz](https://mupdf.com/downloads/archive/mupdf-1.28.0-source.tar.gz), [go-fitz v1.28.2](https://github.com/gen2brain/go-fitz/tree/v1.28.2) |
| [Literata](https://github.com/googlefonts/literata) font, embedded by go-comic-converter | SIL Open Font License 1.1 | `go-comic-converter/internal/pkg/fonts/OFL.txt` |
| The Go modules of go-comic-converter | see each module (BSD, MIT, Apache-2.0) | `go-comic-converter/go.mod` |
| [Python](https://www.python.org) 3.14 and Tcl/Tk 9.0, packed by [PyInstaller](https://pyinstaller.org) | PSF License, Tcl/Tk license (BSD style), PyInstaller bootloader: GPL-2.0 with an exception allowing this use | python.org, tcl.tk |

Because MuPDF is licensed under the AGPL-3.0, this repository (the GUI and the build script) is
licensed under the AGPL-3.0 too: see [LICENSE](LICENSE). The complete source needed to rebuild the
EXE is this repository, its submodule at the pinned commit, and the sources linked above.
