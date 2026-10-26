# Comic Converter GUI

A desktop GUI for [go-comic-converter](https://github.com/celogeek/go-comic-converter): it converts
folders of images, CBZ, ZIP, CBR, RAR and PDF files into EPUBs for e-readers.

## Download

Get **`Comic Converter.exe`** from the [latest release](https://github.com/DanielLeon2143/comic-converter-gui/releases/latest).
It is a single, standalone file: go-comic-converter is packed inside it, nothing else needs to be
installed (Windows 10 or 11). Windows SmartScreen may warn the first time, as the EXE is not signed.

## Run from source

```
git clone --recursive https://github.com/DanielLeon2143/comic-converter-gui.git
```

Then `python comic_converter_gui.py` (or double-click `Comic Converter.bat`). It then needs
`go-comic-converter.exe` next to the script, on `PATH`, in `%USERPROFILE%\go\bin`, or set in the
Advanced tab.

## Features

- **Skeuomorphic look, light and dark**: brushed metal header, raised cards, glossy buttons, inset
  fields, LCD status display. Dark mode with the switch at the top right, or in Advanced >
  Appearance (Same as Windows / Light / Dark). The images of the widgets are drawn by `theme.py`.
- **Drag and drop** comics and folders from Explorer anywhere on the window. A dropped folder that
  contains archives asks whether to add each archive or convert the folder as one comic; other
  files are skipped.
- Queue of comics converted one after the other, with a status per comic and a progress bar
- Every option of the tool: device profile, reading mode (comic/manga/webtoon), format, quality,
  grayscale, crop, brightness/contrast, double pages, aspect ratio, zoom, colors, title page, font...
- Quality presets (good/great/best/max/no filter)
- Dry run, and "Show command" to copy the equivalent command line
- Options are remembered in `~/.go-comic-converter-gui.json`. By default the tool's own saved
  config is ignored (`-ignore-config`) so the window is the only source of options; this can be
  turned off in the Advanced tab.

## Build the EXE

```
python build.py
```

It builds `go-comic-converter.exe` from the `go-comic-converter` submodule (the upstream repo, at a
pinned commit: `git submodule update --init` if you cloned without `--recursive`), then packs it with the GUI into `dist\Comic Converter.exe` with PyInstaller.

Needs, from `PATH` or the `GO` / `CC` environment variables:
- [Go](https://go.dev/dl/) 1.27 or later
- a MinGW-w64 gcc, e.g. [w64devkit](https://github.com/skeeto/w64devkit) (portable, just unzip)
- PyInstaller: `pip install pyinstaller`

Notes:
- The cgo build is required: the pure Go build (`-tags nocgo`) crashes at startup without
  `libmupdf.dll`.
- The MuPDF libraries shipped by go-fitz are built against UCRT, so the build links with
  `-mcrtdll=ucrt` (otherwise: `undefined reference to __intrinsic_setjmpex`).

To update the converter: `git -C go-comic-converter pull`, then `python build.py`.

## License

[AGPL-3.0](LICENSE), because the EXE contains MuPDF, which is licensed under the AGPL-3.0.
go-comic-converter is MIT licensed. See [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
