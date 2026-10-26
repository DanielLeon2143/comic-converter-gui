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

Then `pip install pillow` (for the page preview) and `python comic_converter_gui.py` (or double-click `Comic Converter.bat`). It then needs
`go-comic-converter.exe` next to the script, on `PATH`, in `%USERPROFILE%\go\bin`, or set in the
Advanced tab.

## Features

- **Start screen**: drop comics or folders on the window, or use *Select Folder* (several at once with
  Ctrl/Shift-click) and *Select File*.
- **Workspace** once comics are added:
  - **Preview** of the pages of a comic, chosen above the preview (◀ ▶ or the list). *Original* shows
    the pages in the exact order of the EPUB (same sort as go-comic-converter); *Converted* shows what
    the e-reader gets with the current settings (crop, grayscale, split double pages, title page).
    Click a page to see it bigger, arrow keys for the next one.
  - **Export** options on the right: output folder, device, reading mode, format, quality, split size,
    title page, grayscale, contrast, crop, and *Convert all*.
  - **Comics** list with the status and the EPUB of each one, an overall progress bar, and the log.
    Made for bulk conversions: hundreds of comics, *Clear finished*, *Open output folder*.
- **Settings** (top right): every option of go-comic-converter, in tabs.
- Skeuomorphic look, light and dark (switch at the top right, or Settings > Advanced > Appearance).
- Options are remembered in `~/.go-comic-converter-gui.json`. By default the tool's own saved
  config is ignored (`-ignore-config`), so the window is the only source of options.

## Build the EXE

```
python build.py
```

It builds `go-comic-converter.exe` from the `go-comic-converter` submodule (the upstream repo, at a
pinned commit: `git submodule update --init` if you cloned without `--recursive`), then packs it with the GUI into `dist\Comic Converter.exe` with PyInstaller.

Needs, from `PATH` or the `GO` / `CC` environment variables:
- [Go](https://go.dev/dl/) 1.27 or later
- a MinGW-w64 gcc, e.g. [w64devkit](https://github.com/skeeto/w64devkit) (portable, just unzip)
- PyInstaller and Pillow: `pip install pyinstaller pillow`

Notes:
- The cgo build is required: the pure Go build (`-tags nocgo`) crashes at startup without
  `libmupdf.dll`.
- The MuPDF libraries shipped by go-fitz are built against UCRT, so the build links with
  `-mcrtdll=ucrt` (otherwise: `undefined reference to __intrinsic_setjmpex`).

To update the converter: `git -C go-comic-converter pull`, then `python build.py`.

## License

[AGPL-3.0](LICENSE), because the EXE contains MuPDF, which is licensed under the AGPL-3.0.
go-comic-converter is MIT licensed. See [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
