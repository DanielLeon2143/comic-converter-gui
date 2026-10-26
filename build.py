"""Builds dist/Comic Converter.exe: the GUI with go-comic-converter packed inside.

    python build.py

Needs Go (1.27+) and a MinGW-w64 gcc, from PATH or from the GO and CC environment variables,
and PyInstaller (pip install pyinstaller). The converter is built from ./go-comic-converter.

The cgo build is used, as the pure Go one (-tags nocgo) needs libmupdf.dll at runtime.
The MuPDF libs of go-fitz are built against UCRT, so gcc links with -mcrtdll=ucrt.
"""

import os
import shutil
import struct
import subprocess
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "go-comic-converter"
BUILD = ROOT / "build"
DIST = ROOT / "dist"


def run(cmd, **kw):
    print(">", subprocess.list2cmdline([str(c) for c in cmd]), flush=True)
    subprocess.run([str(c) for c in cmd], check=True, **kw)


def tool(env_name, name):
    path = os.environ.get(env_name) or shutil.which(name)
    if not path:
        sys.exit(f"{name} not found: put it on PATH or set {env_name}")
    return path


def build_converter():
    go, cc = tool("GO", "go"), tool("CC", "gcc")
    env = dict(os.environ, CGO_ENABLED="1", CC=cc, GOTOOLCHAIN="local",
               CGO_CFLAGS="-O2 -mcrtdll=ucrt", CGO_LDFLAGS="-mcrtdll=ucrt")
    # gcc runs its helpers (as, ld) from its own folder.
    env["PATH"] = str(Path(cc).parent) + os.pathsep + env["PATH"]
    out = BUILD / "go-comic-converter.exe"
    run([go, "build", "-trimpath", "-ldflags", "-s -w", "-o", out, "."], cwd=SRC, env=env)
    return out


def png(size):
    """A book icon, drawn pixel by pixel."""
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            u, v = x / size, y / size
            px = (0, 0, 0, 0)
            if 0.16 < u < 0.84 and 0.10 < v < 0.90:
                px = (41, 98, 255, 255)  # cover
                if u < 0.26:
                    px = (25, 60, 170, 255)  # spine
                elif 0.36 < u < 0.74 and 0.24 < v < 0.36:
                    px = (255, 255, 255, 255)  # title
                elif 0.36 < u < 0.74 and (0.46 < v < 0.50 or 0.56 < v < 0.60 or 0.66 < v < 0.70):
                    px = (190, 210, 255, 255)  # lines
            row += bytes(px)
        rows.append(bytes(row))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b""))


def make_icon():
    """An .ico of PNG images, which Windows Vista and later read."""
    images = [png(s) for s in (16, 32, 48, 256)]
    head = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries = b""
    for s, data in zip((16, 32, 48, 256), images):
        entries += struct.pack("<BBBBHHII", s % 256, s % 256, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    path = BUILD / "icon.ico"
    path.write_bytes(head + entries + b"".join(images))
    return path


def main():
    try:
        import PIL  # noqa: F401 - the page preview needs it, PyInstaller packs it from here
    except ImportError:
        sys.exit("Pillow not found: pip install pillow")
    BUILD.mkdir(exist_ok=True)
    exe = build_converter()
    icon = make_icon()
    run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
         "--name", "Comic Converter", "--icon", icon,
         "--add-binary", f"{exe}{os.pathsep}.",
         "--distpath", DIST, "--workpath", BUILD / "pyinstaller", "--specpath", BUILD,
         ROOT / "comic_converter_gui.py"])
    # The intermediate go-comic-converter.exe is a command line tool, not the app: don't leave it around.
    shutil.rmtree(BUILD, ignore_errors=True)
    print(f"\nDone: {DIST / 'Comic Converter.exe'}")


if __name__ == "__main__":
    main()
