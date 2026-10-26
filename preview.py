"""Page previews: the pages of a comic, in the order go-comic-converter puts them, as thumbnails.

Folders and CBZ/ZIP files are read directly. CBR/RAR and PDF files, and the converted result, go
through go-comic-converter: it writes an EPUB, whose pages are read back here.
Nothing here touches Tk, so it can run in a thread: thumbnails are returned as PNG in base64.
"""

import base64
import functools
import io
import json
import os
import posixpath
import re
import subprocess
import zipfile

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".tiff", ".jxl")
ZIP_EXTS = (".cbz", ".zip")
CONVERTER_EXTS = (".cbr", ".rar", ".pdf")  # read by go-comic-converter only


class Page:
    def __init__(self, label, load, source_id=None):
        self.label = label          # shown under the thumbnail
        self.load = load            # returns the bytes of the image
        self.source_id = source_id  # index of the page in the source (the converter's task id), None for a title page


# ---------- order of the pages ----------
# Port of go-comic-converter internal/pkg/sortpath, as it behaves on Windows: paths are split on
# "\" only, so the folders inside a zip ("a/b/") are compared as one piece of text.

_SPLIT = re.compile(r"^(.*?)(\d+(?:\.\d+)?)(?:-(\d+(?:\.\d+)?))?$")


def _part(text):
    m = _SPLIT.match(text)
    if not m:
        return text, text, 0.0
    return text, m.group(1), float(m.group(2))


def _cmp_part(a, b):
    if a[2] == 0 or b[2] == 0:
        return (a[0] > b[0]) - (a[0] < b[0])
    if a[1] == b[1]:
        return (a[2] > b[2]) - (a[2] < b[2])
    return (a[1] > b[1]) - (a[1] < b[1])


def _parse(filename, mode):
    f = filename.lower()
    cut = max(f.rfind("/"), f.rfind("\\")) + 1  # filepath.Split splits on both
    pathname, name = f[:cut], f[cut:]
    if pathname.endswith("\\"):
        pathname = pathname[:-1]
    dot = name.rfind(".")
    if dot >= 0:
        name = name[:dot]
    parts = [_part(p) if mode > 0 else (p, p, 0.0) for p in pathname.split("\\")]
    parts.append(_part(name) if mode == 2 else (name, name, 0.0))
    return parts


def _cmp_paths(a, b):
    for x, y in zip(a, b):
        c = _cmp_part(x, y)
        if c:
            return c
    return len(a) - len(b)


def sort_like_converter(paths, mode):
    keys = {p: _parse(p, mode) for p in paths}
    return sorted(paths, key=functools.cmp_to_key(lambda a, b: _cmp_paths(keys[a], keys[b])))


def _is_image(name):
    return os.path.splitext(name)[1].lower() in IMAGE_EXTS and not os.path.basename(name).startswith(".")


# ---------- pages of the source ----------

def source_pages(path, sort_mode):
    """The pages of a folder or CBZ/ZIP, in the converter's order. None for the formats only the
    converter can read (CBR/RAR, PDF)."""
    if os.path.isdir(path):
        root = os.path.normpath(path)
        images = [os.path.join(d, f) for d, _, files in os.walk(root) for f in files if _is_image(f)]
        return [Page(os.path.relpath(p, root), functools.partial(_read_file, p), i)
                for i, p in enumerate(sort_like_converter(images, sort_mode))]
    ext = os.path.splitext(path)[1].lower()
    if ext in ZIP_EXTS:
        with zipfile.ZipFile(path) as z:
            names = [i.filename for i in z.infolist() if not i.is_dir() and _is_image(i.filename)]
        return [Page(n, functools.partial(_read_zip, path, n), i)
                for i, n in enumerate(sort_like_converter(names, sort_mode))]
    return None


def _read_file(p):
    with open(p, "rb") as f:
        return f.read()


def _read_zip(path, name):
    with zipfile.ZipFile(path) as z:
        return z.read(name)


# ---------- pages of an EPUB ----------

def epub_pages(epub):
    """The images of an EPUB written by go-comic-converter, in reading order."""
    with zipfile.ZipFile(epub) as z:
        container = z.read("META-INF/container.xml").decode("utf-8")
        opf = re.search(r'full-path="([^"]+)"', container).group(1)
        text = z.read(opf).decode("utf-8")
        base = posixpath.dirname(opf)
        hrefs = {}
        for tag in re.findall(r"<item\b[^>]*>", text):
            i, h = re.search(r'\bid="([^"]+)"', tag), re.search(r'\bhref="([^"]+)"', tag)
            if i and h:
                hrefs[i.group(1)] = posixpath.normpath(posixpath.join(base, h.group(1)))
        spreads = dict(re.findall(r'<itemref\b[^>]*\bidref="([^"]+)"[^>]*properties="page-spread-(left|right)"', text))
        pages = []
        backgrounds = {}  # stylesheet -> background color of the pages
        for ref in re.findall(r'<itemref\b[^>]*\bidref="([^"]+)"', text):
            page = hrefs.get(ref)
            if not page:
                continue
            html = z.read(page).decode("utf-8", "replace")
            here = posixpath.dirname(page)
            # A page is a screen (the viewport) with its images placed in it: a big page is stored as
            # several tiles. The page is drawn the way the e-reader shows it, margins included.
            tiles = []
            for tag in re.findall(r"<img\b[^>]*>", html):
                src = re.search(r'\bsrc="([^"]+)"', tag)
                if src:
                    style = dict(re.findall(r"(left|top|width|height)\s*:\s*(-?\d+(?:\.\d+)?)px", tag))
                    tiles.append((posixpath.normpath(posixpath.join(here, src.group(1))),
                                  {k: float(v) for k, v in style.items()}))
            if not tiles:
                m = re.search(r'(?:xlink:href|href)="([^"]+\.(?:jpe?g|png|webp|jxl))"', html, re.I)
                if not m:
                    continue
                tiles = [(posixpath.normpath(posixpath.join(here, m.group(1))), {})]
            vp = re.search(r'name="viewport"[^>]*content="width=(\d+),\s*height=(\d+)"', html)
            css = re.search(r'<link\b[^>]*href="([^"]+\.css)"', html)
            css = posixpath.normpath(posixpath.join(here, css.group(1))) if css else None
            if css not in backgrounds:
                try:
                    bg = re.search(r"body\s*{[^}]*background(?:-color)?\s*:\s*(#[0-9a-fA-F]{6})", z.read(css).decode())
                except (KeyError, TypeError):
                    bg = None
                backgrounds[css] = bg.group(1) if bg else "#FFFFFF"
            sid = re.match(r"page_(\d+)_p\d+", ref)
            label = "Title page" if "title" in ref.lower() else f"Page {len(pages) + 1}"
            if ref in spreads:
                label += " ◧" if spreads[ref] == "left" else " ◨"  # side of the spread on the e-reader
            viewport = (int(vp.group(1)), int(vp.group(2))) if vp else None
            pages.append(Page(label, functools.partial(_render_page, epub, viewport, backgrounds[css], tiles),
                              int(sid.group(1)) if sid else None))
    return pages


def _render_page(epub, viewport, background, tiles):
    """The page as the e-reader shows it: its viewport, its background, its images where it places them."""
    with zipfile.ZipFile(epub) as z:
        images = [(Image.open(io.BytesIO(z.read(name))).convert("RGB"), pos) for name, pos in tiles]
    placed = []
    for im, p in images:
        w, h = round(p.get("width", im.width)), round(p.get("height", im.height))
        placed.append((im if (w, h) == im.size else im.resize((max(w, 1), max(h, 1))),
                       round(p.get("left", 0)), round(p.get("top", 0))))
    if viewport:
        size = viewport
    else:  # no viewport: just the images
        size = (max(x + im.width for im, x, _ in placed), max(y + im.height for im, _, y in placed))
    out = Image.new("RGB", size, background)
    for im, x, y in placed:
        out.paste(im, (x, y))
    buf = io.BytesIO()
    out.save(buf, "PNG", compress_level=1)
    return buf.getvalue()


# ---------- converter ----------

def run_converter(exe, args, popen_kwargs, on_progress, is_cancelled, on_start=None):
    """Runs go-comic-converter with -json. Returns None when it worked, else the error text."""
    proc = subprocess.Popen([exe] + args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                            bufsize=1, **popen_kwargs)
    if on_start:
        on_start(proc)
    errors = []
    for line in proc.stdout:
        if is_cancelled():
            proc.terminate()
            break
        s = line.strip()
        if s.startswith("{"):
            try:
                msg = json.loads(s)
            except json.JSONDecodeError:
                continue
            if msg.get("type") == "epubprogress":
                on_progress(msg.get("data") or {})
        elif s:
            errors.append(s)
    code = proc.wait()
    if is_cancelled():
        return "cancelled"
    return None if code == 0 else ("\n".join(errors[-3:]) or f"exit code {code}")


# ---------- thumbnails ----------

def thumbnail(data, width, height):
    """PNG (base64) of the image scaled to fit width x height, and its original size."""
    img = Image.open(io.BytesIO(data))
    size = img.size
    img.draft("RGB", (width * 2, height * 2))  # JPEG: decode at a reduced size, much faster
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGBA").convert("RGB") if "A" in img.mode or img.mode == "P" else img.convert("RGB")
    img.thumbnail((width, height), Image.Resampling.BILINEAR, reducing_gap=2.0)
    buf = io.BytesIO()
    img.save(buf, "PNG", compress_level=1)
    return base64.b64encode(buf.getvalue()).decode("ascii"), size
