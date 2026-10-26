"""Desktop GUI for go-comic-converter (https://github.com/celogeek/go-comic-converter).

Runs the go-comic-converter command line tool with the options picked in the window,
over a queue of comics, and follows its progress through its -json output.
"""

import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

from theme import Theme, set_title_bar_dark, windows_dark_mode

APP_NAME = "Comic Converter"
EXE_NAME = "go-comic-converter.exe" if os.name == "nt" else "go-comic-converter"
SETTINGS_FILE = Path.home() / ".go-comic-converter-gui.json"
INPUT_TYPES = [("Comics", "*.cbz *.zip *.cbr *.rar *.pdf"), ("All files", "*.*")]
ARCHIVE_EXTS = (".cbz", ".zip", ".cbr", ".rar", ".pdf")
# Where PyInstaller unpacks the bundled files, when running as an EXE.
BUNDLE_DIR = getattr(sys, "_MEIPASS", None)

# (code, device, description, resolution, features)
PROFILES = [
    ("HR", "Kindle", "Kindle High Resolution", "2400x3840", "color, manga"),
    ("SR", "Kindle", "Kindle Standard Resolution", "1200x1920", "color, manga"),
    ("KS3", "Kindle", "Kindle Scribe 3", "1980x2640", "manga, landscape"),
    ("KSC", "Kindle", "Kindle Scribe Colorsoft", "1980x2640", "color, manga, landscape"),
    ("K12", "Kindle", "Kindle 12", "1072x1448", "manga"),
    ("KPW12", "Kindle", "Kindle Paperwhite 12/Signature Edition", "1264x1680", "manga"),
    ("KCS", "Kindle", "Kindle Colorsoft", "1264x1680", "color, manga"),
    ("KS2", "Kindle", "Kindle Scribe 2", "1860x2480", "manga, landscape"),
    ("K11", "Kindle", "Kindle 11", "1072x1448", "manga"),
    ("KS", "Kindle", "Kindle Scribe", "1860x2480", "manga, landscape"),
    ("KPW5", "Kindle", "Kindle Paperwhite 5/Signature Edition", "1236x1648", "panel view, manga"),
    ("K10", "Kindle", "Kindle 10", "600x800", "panel view, manga"),
    ("KO3", "Kindle", "Kindle Oasis 3", "1264x1680", "panel view, manga"),
    ("KPW4", "Kindle", "Kindle Paperwhite 4", "1072x1448", "panel view, manga"),
    ("KO2", "Kindle", "Kindle Oasis 2", "1264x1680", "panel view, manga"),
    ("KO1", "Kindle", "Kindle Oasis 1", "1072x1448", "panel view, manga"),
    ("K8", "Kindle", "Kindle 8", "600x800", "panel view, manga"),
    ("KPW3", "Kindle", "Kindle Paperwhite 3", "1072x1448", "panel view, manga"),
    ("K7", "Kindle", "Kindle 7", "600x800", "panel view, manga"),
    ("KV", "Kindle", "Kindle Voyage", "1072x1448", "panel view, manga"),
    ("KPW2", "Kindle", "Kindle Paperwhite 2", "758x1024", "panel view, manga"),
    ("K5", "Kindle", "Kindle 5", "600x800", "panel view, manga"),
    ("KPW1", "Kindle", "Kindle Paperwhite 1", "758x1024", "panel view, manga"),
    ("K4", "Kindle", "Kindle 4", "600x800", "panel view, manga"),
    ("KT", "Kindle", "Kindle Touch", "600x800", "panel view, manga"),
    ("K3", "Kindle", "Kindle Keyboard", "600x800", "panel view, manga"),
    ("K2", "Kindle", "Kindle 2", "600x800", "panel view, manga"),
    ("KDX", "Kindle", "Kindle DX/DXG", "824x1200", "panel view, manga"),
    ("K1", "Kindle", "Kindle 1", "600x800", "panel view, manga"),
    ("KoCBW", "Kobo", "Kobo Clara BW", "1072x1448", "manga"),
    ("KoCC", "Kobo", "Kobo Clara Colour", "1072x1448", "color, manga"),
    ("KoLC", "Kobo", "Kobo Libra Colour", "1264x1680", "color, manga"),
    ("KoE2", "Kobo", "Kobo Elipsa 2E", "1404x1872", "manga"),
    ("KoC2E", "Kobo", "Kobo Clara 2E", "1072x1448", "manga"),
    ("KoE", "Kobo", "Kobo Elipsa", "1404x1872", "manga"),
    ("KoS", "Kobo", "Kobo Sage", "1440x1920", "manga"),
    ("KoL2", "Kobo", "Kobo Libra 2", "1264x1680", "manga"),
    ("KoN", "Kobo", "Kobo Nia", "758x1024", "manga"),
    ("KoLH2O", "Kobo", "Kobo Libra H2O", "1264x1680", "manga"),
    ("KoCHD", "Kobo", "Kobo Clara HD", "1072x1448", "manga"),
    ("KoF", "Kobo", "Kobo Forma", "1440x1920", "manga"),
    ("KoAH2O2", "Kobo", "Kobo Aura H2O Edition 2", "1080x1430", "manga"),
    ("KoAO", "Kobo", "Kobo Aura One", "1404x1872", "manga"),
    ("KoA2", "Kobo", "Kobo Aura Edition 2", "758x1024", "manga"),
    ("KoGHD", "Kobo", "Kobo Glo HD", "1072x1448", "manga"),
    ("KoT2", "Kobo", "Kobo Touch 2.0", "600x800", "manga"),
    ("KoAH2O", "Kobo", "Kobo Aura H2O", "1080x1430", "manga"),
    ("KoA", "Kobo", "Kobo Aura", "758x1024", "manga"),
    ("KoAHD", "Kobo", "Kobo Aura HD", "1080x1440", "manga"),
    ("KoM", "Kobo", "Kobo Mini", "600x800", "manga"),
    ("KoG", "Kobo", "Kobo Glo", "758x1024", "manga"),
    ("KoT", "Kobo", "Kobo Touch", "600x800", "manga"),
    ("KoR", "Kobo", "Kobo eReader", "600x800", "manga"),
    ("RMPU", "reMarkable", "reMarkable Paper Pure", "1404x1872", ""),
    ("RMPM", "reMarkable", "reMarkable Paper Pro Move", "954x1696", "color"),
    ("RMP", "reMarkable", "reMarkable Paper Pro", "1620x2160", "color"),
    ("RM2", "reMarkable", "reMarkable 2", "1404x1872", ""),
    ("RM1", "reMarkable", "reMarkable 1", "1404x1872", ""),
    ("AB", "Apple", "Apple Books Standard Resolution", "1640x2360", "color, manga, jxl"),
    ("ABD", "Apple", "Apple Books on iPhone Duo", "1920x2713", "color, manga, jxl"),
    ("ABP11", "Apple", 'Apple Books on iPad Pro 11"', "1668x2420", "color, manga, jxl"),
    ("ABP13", "Apple", 'Apple Books on iPad Pro 13"', "2064x2752", "color, manga, jxl"),
    ("ABI", "Apple", "Apple Books on iPhone", "1320x2868", "color, manga, jxl"),
    ("ABM", "Apple", "Apple Books on iPad mini", "1488x2266", "color, manga, jxl"),
]
PROFILE_LABELS = [f"{c} - {d} ({r})" for c, _, d, r, _ in PROFILES]
PROFILE_FEATURES = {c: f for c, _, _, _, f in PROFILES}

# Choice options: flag -> list of (value, label)
CHOICES = {
    "mode": [(0, "Comic (left to right)"), (1, "Manga (right to left)"), (2, "Webtoon (vertical strip)")],
    "grayscale-mode": [(0, "Normal"), (1, "Average"), (2, "Luminance")],
    "doublepagemode": [(0, "Split"), (1, "Split + rotate"), (2, "Rotate")],
    "sort": [(0, "Alpha (path and file)"), (1, "Alphanumeric path, alpha file"), (2, "Alphanumeric (path and file)")],
    "titlepage": [(0, "Never"), (1, "Always"), (2, "Only if the EPUB is split")],
    "format": [("jpeg", "JPEG (lossy)"), ("png", "PNG (lossless)"), ("jxl", "JPEG XL (Apple Books only)"), ("copy", "Copy (no processing)")],
    "theme": [("system", "Same as Windows"), ("light", "Light"), ("dark", "Dark")],
}

# Built-in defaults of go-comic-converter. Only the values that differ are passed on the command line.
DEFAULTS = {
    "profile": "SR",
    "quality": 85,
    "jxl-effort": 4,
    "format": "jpeg",
    "grayscale": True,
    "grayscale-mode": 0,
    "crop": True,
    "crop-ratio-left": 1,
    "crop-ratio-up": 1,
    "crop-ratio-right": 1,
    "crop-ratio-bottom": 3,
    "crop-limit": 0,
    "crop-skip-if-limit-reached": False,
    "brightness": 0,
    "contrast": 0,
    "autocontrast": False,
    "doublepagemode": 0,
    "keepsplitdoublepageaspect": True,
    "combinesplitdoublepage": False,
    "noblankimage": True,
    "mode": 0,
    "landscape": False,
    "limitmb": 200,
    "strip": False,
    "sort": 1,
    "foreground-color": "000000",
    "background-color": "FFFFFF",
    "resize": True,
    "zoom": 0.0,
    "aspect-ratio": 0.0,
    "titlepage": 1,
    "covercaption": True,
    "font": "",
    "author": "GO Comic Converter",
    "workers": os.cpu_count() or 4,
}

# Settings of the GUI itself, not passed to the tool as flags.
GUI_DEFAULTS = {
    "exe": "",
    "output_dir": "",
    "title": "",
    "use_saved_config": False,
    "extra_args": "",
    "open_folder_when_done": False,
    "theme": "system",
}

# Starting values of the GUI that differ from the defaults of the tool, so they are passed as flags.
# The tool sorts the file names as text by default (page1, page10, page2): sort the numbers by value.
PREFERRED = {"sort": 2}

# Version of the settings file. 2: "sort" defaults to 2 (version 1 files have the tool's default, 1).
SETTINGS_VERSION = 2


def natural_key(path):
    """Sort key putting "Vol 2" before "Vol 10": the numbers are compared by value."""
    return [(0, int(part), "") if part.isdigit() else (1, 0, part.lower())
            for part in re.split(r"(\d+)", os.path.basename(os.path.normpath(path))) if part]


def bundled_exe():
    """The go-comic-converter packed inside this EXE, or None."""
    if BUNDLE_DIR and (Path(BUNDLE_DIR) / EXE_NAME).is_file():
        return str(Path(BUNDLE_DIR) / EXE_NAME)
    return None


def find_exe(configured):
    """Return the path of go-comic-converter, or None."""
    candidates = [configured] if configured else []
    candidates.append(bundled_exe())
    app_dir = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve().parent
    candidates.append(str(app_dir / EXE_NAME))
    found = shutil.which("go-comic-converter")
    if found:
        candidates.append(found)
    gopath = os.environ.get("GOPATH") or str(Path.home() / "go")
    candidates.append(str(Path(gopath) / "bin" / EXE_NAME))
    for c in candidates:
        if c and Path(c).is_file():
            return c
    return None


def popen_kwargs():
    # Keep a console window from flashing up for each conversion on Windows.
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NO_WINDOW}
    return {}


class FileDrop:
    """Accepts files dropped from Explorer on a Tk window, with the Win32 WM_DROPFILES message.

    The window procedure of the toplevel is replaced by one that catches WM_DROPFILES and
    passes everything else to the original one. Drops on any child widget reach the toplevel.
    The callback runs inside the window procedure, where calling Tk crashes the interpreter:
    it must only hand the paths over (e.g. to a queue).
    """

    WM_DROPFILES = 0x0233
    GWLP_WNDPROC = -4

    def __init__(self, window, callback):
        import ctypes
        from ctypes import wintypes

        self.callback = callback
        user32, shell32 = ctypes.windll.user32, ctypes.windll.shell32
        LRESULT, WPARAM, LPARAM = ctypes.c_ssize_t, ctypes.c_size_t, ctypes.c_ssize_t
        WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, WPARAM, LPARAM)

        user32.GetParent.argtypes = [wintypes.HWND]
        user32.GetParent.restype = wintypes.HWND
        user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
        user32.SetWindowLongPtrW.restype = ctypes.c_void_p
        user32.CallWindowProcW.argtypes = [ctypes.c_void_p, wintypes.HWND, wintypes.UINT, WPARAM, LPARAM]
        user32.CallWindowProcW.restype = LRESULT
        shell32.DragAcceptFiles.argtypes = [wintypes.HWND, wintypes.BOOL]
        shell32.DragQueryFileW.argtypes = [ctypes.c_void_p, wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]
        shell32.DragQueryFileW.restype = wintypes.UINT
        shell32.DragFinish.argtypes = [ctypes.c_void_p]

        def wndproc(hwnd, msg, wparam, lparam):
            if msg == self.WM_DROPFILES:
                count = shell32.DragQueryFileW(wparam, 0xFFFFFFFF, None, 0)
                paths = []
                for i in range(count):
                    size = shell32.DragQueryFileW(wparam, i, None, 0) + 1
                    buf = ctypes.create_unicode_buffer(size)
                    shell32.DragQueryFileW(wparam, i, buf, size)
                    paths.append(buf.value)
                shell32.DragFinish(wparam)
                self.callback(paths)
                return 0
            return user32.CallWindowProcW(self.old_proc, hwnd, msg, wparam, lparam)

        window.update_idletasks()
        hwnd = user32.GetParent(window.winfo_id()) or window.winfo_id()
        self.proc = WNDPROC(wndproc)  # keep a reference: Windows calls it for the life of the window
        self.old_proc = user32.SetWindowLongPtrW(hwnd, self.GWLP_WNDPROC, ctypes.cast(self.proc, ctypes.c_void_p))
        shell32.DragAcceptFiles(hwnd, True)


class Tooltip:
    def __init__(self, widget, text):
        self.widget, self.text, self.tip = widget, text, None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _):
        if self.tip:
            return
        x = self.widget.winfo_rootx() + 16
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        p = Theme.current
        self.tip.configure(background=p["tip_border"])
        tk.Label(self.tip, text=self.text, justify="left", background=p["tip_bg"], foreground=p["tip_fg"],
                 wraplength=360, padx=8, pady=5).pack(padx=1, pady=1)

    def hide(self, _):
        if self.tip:
            self.tip.destroy()
            self.tip = None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1020x880")
        self.minsize(900, 760)

        self.vars = {}
        self.events = queue.Queue()
        self.worker = None
        self.proc = None
        self.stop_requested = False
        self.comboboxes = []
        self.theme = Theme(self)
        self.theme.apply(self._saved_theme_is_dark())  # draws the images the widgets are built with

        self._build()
        self._load_settings()
        self._on_profile_change()
        self._apply_theme()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._poll_events)
        self.after(200, self._check_exe)
        if os.name == "nt":
            try:
                self.file_drop = FileDrop(self, lambda paths: self.events.put(("drop", paths)))
            except (AttributeError, OSError) as e:
                self._log(f"Drag and drop is not available: {e}\n", "err")

    # ---------- layout ----------

    def _build(self):
        self._build_header()

        root = ttk.Frame(self, padding=(12, 10, 12, 12), style="Backdrop.TFrame")
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)

        self._build_queue(root).grid(row=0, column=0, sticky="nsew")

        paned = ttk.PanedWindow(root, orient="vertical")
        paned.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        nb = self.notebook = ttk.Notebook(paned)
        nb.add(self._tab_general(nb), text="General")
        nb.add(self._tab_image(nb), text="Image")
        nb.add(self._tab_crop(nb), text="Crop")
        nb.add(self._tab_pages(nb), text="Pages & Layout")
        nb.add(self._tab_advanced(nb), text="Advanced")
        paned.add(nb, weight=3)
        paned.add(self._build_log(paned), weight=2)

        self._build_actions(root).grid(row=2, column=0, sticky="ew", pady=(10, 0))

    def _build_header(self):
        """Brushed metal bar with the embossed title and the dark mode switch."""
        h = self.theme.photos["header"].height()
        self.header = tk.Canvas(self, height=h, highlightthickness=0, borderwidth=0)
        self.header.pack(fill="x")
        self.header_img = tk.PhotoImage(master=self, width=self.winfo_screenwidth(), height=h)
        c = self.header
        c.create_image(0, 0, image=self.header_img, anchor="nw")
        title_font, sub_font = ("Segoe UI Semibold", 17), ("Segoe UI", 9)
        y = h // 2
        c.create_text(18, y - 8 + 1, text=APP_NAME, font=title_font, anchor="w", tags=("emboss", "title_shadow"))
        c.create_text(18, y - 8, text=APP_NAME, font=title_font, anchor="w", tags="title")
        c.create_text(19, y + 15, text="Comics and manga to EPUB, for your e-reader", font=sub_font, anchor="w",
                      tags="subtitle")
        c.create_text(0, y, text="☀", font=("Segoe UI Symbol", 13), anchor="e", tags=("right", "sun"))
        c.create_image(0, y, image=self.theme.photos["switch_off"], anchor="e", tags=("right", "switch"))
        c.create_text(0, y, text="☾", font=("Segoe UI Symbol", 13), anchor="e", tags=("right", "moon"))
        c.tag_bind("switch", "<Button-1>", lambda e: self._toggle_dark())
        c.tag_bind("switch", "<Enter>", lambda e: c.configure(cursor="hand2"))
        c.tag_bind("switch", "<Leave>", lambda e: c.configure(cursor=""))
        c.bind("<Configure>", lambda e: self._place_header())

    def _place_header(self):
        c, w = self.header, self.header.winfo_width()
        y = self.header.winfo_height() // 2
        sw = self.theme.photos["switch_on"].width()
        c.coords("moon", w - 16, y - 1)
        c.coords("switch", w - 38, y)
        c.coords("sun", w - 44 - sw, y - 1)

    def _redraw_header(self):
        p = self.theme.p
        tile = self.theme.photos["header"]
        self.header_img.blank()
        self.header_img.tk.call(self.header_img, "copy", tile, "-to", 0, 0,
                                self.header_img.width(), self.header_img.height())
        c = self.header
        c.configure(background=p["header"][1])
        dy = p["emboss_dy"]
        x, y = c.coords("title")
        c.coords("title_shadow", x, y + dy)
        c.itemconfigure("title_shadow", fill=p["emboss"])
        c.itemconfigure("title", fill=p["title"])
        c.itemconfigure("subtitle", fill=p["subtitle"])
        c.itemconfigure("sun", fill=p["title"] if not p["dark"] else p["subtitle"])
        c.itemconfigure("moon", fill=p["title"] if p["dark"] else p["subtitle"])
        c.itemconfigure("switch", image=self.theme.photos["switch_on" if p["dark"] else "switch_off"])
        self._place_header()

    def _card(self, parent, title=None, hint=None):
        """A raised card, optionally with a title. Returns the card and the frame for its content."""
        card = ttk.Frame(parent, style="Card.TFrame", padding=self.theme.padding("Card.TFrame"))
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)
        if title:
            head = ttk.Frame(card)
            head.grid(row=0, column=0, sticky="ew", pady=(0, 8))
            ttk.Label(head, text=title, style="CardTitle.TLabel").pack(side="left")
            if hint:
                ttk.Label(head, text=hint, style="Muted.TLabel").pack(side="left", padx=(10, 0))
        body = ttk.Frame(card)
        body.grid(row=1, column=0, sticky="nsew")
        return card, body

    @staticmethod
    def _saved_theme_is_dark():
        """The theme of the saved settings, read before the widgets exist."""
        try:
            mode = json.loads(SETTINGS_FILE.read_text(encoding="utf-8")).get("theme", "system")
        except (OSError, json.JSONDecodeError, AttributeError):
            mode = "system"
        return mode == "dark" or (mode == "system" and windows_dark_mode())

    def _apply_theme(self):
        mode = self._get_choice("theme")
        dark = mode == "dark" or (mode == "system" and windows_dark_mode())
        self.theme.apply(dark)
        p = self.theme.p
        self.log.configure(background=p["field"], foreground=p["text"], insertbackground=p["text"],
                           selectbackground=p["select"], selectforeground=p["select_text"])
        self.log.tag_configure("err", foreground=p["log_err"])
        self.log.tag_configure("ok", foreground=p["log_ok"])
        self.log.tag_configure("cmd", foreground=p["log_cmd"])
        self.tree.tag_configure("odd", background=p["row_odd"])
        self.tree.tag_configure("even", background=p["row_even"])
        for cb in self.comboboxes:
            self.theme.recolor_combobox(cb)
        self._redraw_header()
        set_title_bar_dark(self, dark)

    def _toggle_dark(self):
        self._set_choice("theme", "light" if self.theme.p["dark"] else "dark")
        self._apply_theme()

    def _build_queue(self, parent):
        card, box = self._card(parent, "Comics to convert",
                               "Drag and drop folders, CBZ, ZIP, CBR, RAR or PDF files anywhere on this window")
        box.columnconfigure(0, weight=1)

        cols = ("input", "status")
        self.tree = ttk.Treeview(box, columns=cols, show="headings", height=5, selectmode="extended")
        self.tree.heading("input", text="Input")
        self.tree.heading("status", text="Status")
        self.tree.column("input", width=700)
        self.tree.column("status", width=160, anchor="center")
        self.tree.grid(row=0, column=0, rowspan=5, sticky="nsew")
        sb = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
        sb.grid(row=0, column=1, rowspan=5, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<Delete>", lambda e: self._remove_selected())

        btns = [("Add files…", self._add_files), ("Add folder…", self._add_folder),
                ("Remove", self._remove_selected), ("Clear", self._clear_queue)]
        for i, (txt, cmd) in enumerate(btns):
            ttk.Button(box, text=txt, command=cmd, width=14).grid(row=i, column=2, padx=(10, 0), pady=2, sticky="ew")

        out = ttk.Frame(box)
        out.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        out.columnconfigure(1, weight=1)
        ttk.Label(out, text="Output folder:").grid(row=0, column=0, sticky="w")
        self.vars["output_dir"] = tk.StringVar()
        ttk.Entry(out, textvariable=self.vars["output_dir"]).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(out, text="Browse…", command=self._pick_output).grid(row=0, column=2)
        ttk.Label(out, text="(empty = next to each input)", style="Muted.TLabel").grid(row=0, column=3, padx=(8, 0))
        return card

    def _build_log(self, parent):
        card, box = self._card(parent, "Log")
        box.columnconfigure(0, weight=1)
        box.rowconfigure(0, weight=1)
        inset = ttk.Frame(box, style="Inset.TFrame", padding=self.theme.padding("Inset.TFrame"))
        inset.grid(row=0, column=0, sticky="nsew")
        inset.columnconfigure(0, weight=1)
        inset.rowconfigure(0, weight=1)
        self.log = tk.Text(inset, height=6, wrap="word", font=("Consolas", 9), state="disabled",
                           relief="flat", borderwidth=0, highlightthickness=0, padx=6, pady=4)
        self.log.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(box, orient="vertical", command=self.log.yview)
        sb.grid(row=0, column=1, sticky="ns", padx=(4, 0))
        self.log.configure(yscrollcommand=sb.set)
        return card

    def _build_actions(self, parent):
        card, bar = self._card(parent)
        bar.columnconfigure(0, weight=1)
        # Status display, in the style of an LCD.
        lcd = ttk.Frame(bar, style="LCD.TFrame", padding=self.theme.padding("LCD.TFrame"))
        lcd.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        lcd.columnconfigure(0, weight=1)
        self.status = tk.StringVar(value="Ready")
        ttk.Label(lcd, textvariable=self.status, style="LCD.TLabel").grid(row=0, column=0, sticky="w")
        self.progress = ttk.Progressbar(lcd, mode="determinate", maximum=100)
        self.progress.grid(row=1, column=0, sticky="ew", pady=(3, 0))
        self.btn_cmd = ttk.Button(bar, text="Show command", command=self._show_command)
        self.btn_cmd.grid(row=0, column=1, padx=3)
        self.btn_dry = ttk.Button(bar, text="Dry run", command=lambda: self._start(dry=True))
        self.btn_dry.grid(row=0, column=2, padx=3)
        self.btn_stop = ttk.Button(bar, text="Stop", command=self._stop, state="disabled")
        self.btn_stop.grid(row=0, column=3, padx=3)
        self.btn_go = ttk.Button(bar, text="Convert", style="Accent.TButton", command=lambda: self._start(dry=False))
        self.btn_go.grid(row=0, column=4, padx=(3, 0), ipadx=14, ipady=3)
        return card

    # ---------- widget helpers ----------

    def _tab(self, nb):
        f = ttk.Frame(nb, padding=12)
        f.columnconfigure(1, weight=1)
        f.columnconfigure(4, weight=1)
        f._row = [0, 0]  # next free row for the left and right columns
        return f

    def _place(self, tab, side, label, widget, tip=None, label_widget=True):
        row = tab._row[side]
        col = side * 3
        if label_widget:
            lbl = ttk.Label(tab, text=label)
            lbl.grid(row=row, column=col, sticky="w", pady=3, padx=(0, 8))
            if tip:
                Tooltip(lbl, tip)
        widget.grid(row=row, column=col + 1, sticky="w", pady=3)
        if tip:
            Tooltip(widget, tip)
        if side == 0:
            ttk.Frame(tab, width=24).grid(row=row, column=2)
        tab._row[side] += 1
        return widget

    def _check(self, tab, side, key, label, tip=None, command=None):
        v = self.vars[key] = tk.BooleanVar(value=DEFAULTS.get(key, False))
        cb = ttk.Checkbutton(tab, text=label, variable=v, command=command)
        return self._place(tab, side, label, cb, tip, label_widget=False)

    def _spin(self, tab, side, key, label, lo, hi, inc=1, tip=None, is_float=False):
        v = self.vars[key] = (tk.DoubleVar if is_float else tk.IntVar)(value=DEFAULTS[key])
        sp = ttk.Spinbox(tab, from_=lo, to=hi, increment=inc, textvariable=v, width=8)
        return self._place(tab, side, label, sp, tip)

    def _scale(self, tab, side, key, label, lo, hi, tip=None):
        v = self.vars[key] = tk.IntVar(value=DEFAULTS[key])
        f = ttk.Frame(tab)
        ttk.Scale(f, from_=lo, to=hi, variable=v, length=180,
                  command=lambda x: v.set(round(float(x)))).pack(side="left")
        ttk.Spinbox(f, from_=lo, to=hi, textvariable=v, width=5).pack(side="left", padx=(6, 0))
        return self._place(tab, side, label, f, tip)

    def _choice(self, tab, side, key, label, tip=None, command=None, width=30):
        options = CHOICES[key]
        self.vars[key] = tk.StringVar()
        cb = ttk.Combobox(tab, state="readonly", width=width, values=[l for _, l in options],
                          textvariable=self.vars[key])
        self.comboboxes.append(cb)
        self._set_choice(key, DEFAULTS.get(key, GUI_DEFAULTS.get(key)))
        if command:
            cb.bind("<<ComboboxSelected>>", lambda e: command())
        return self._place(tab, side, label, cb, tip)

    def _set_choice(self, key, value):
        for val, lbl in CHOICES[key]:
            if val == value:
                self.vars[key].set(lbl)
                return

    def _get_choice(self, key):
        lbl = self.vars[key].get()
        for val, l in CHOICES[key]:
            if l == lbl:
                return val
        return DEFAULTS.get(key, GUI_DEFAULTS.get(key))

    def _color(self, tab, side, key, label, tip=None):
        v = self.vars[key] = tk.StringVar(value=DEFAULTS[key])
        f = ttk.Frame(tab)
        swatch = tk.Label(f, width=3, relief="solid", borderwidth=1)
        ttk.Entry(f, textvariable=v, width=9).pack(side="left")
        swatch.pack(side="left", padx=6)

        def refresh(*_):
            val = v.get().strip().lstrip("#")
            if len(val) == 6 and all(c in "0123456789abcdefABCDEF" for c in val):
                swatch.configure(background="#" + val)

        def pick():
            rgb = colorchooser.askcolor(color="#" + v.get().lstrip("#"), parent=self)[1]
            if rgb:
                v.set(rgb.lstrip("#").upper())

        v.trace_add("write", refresh)
        refresh()
        ttk.Button(f, text="Pick…", command=pick, width=7).pack(side="left")
        return self._place(tab, side, label, f, tip)

    def _entry(self, tab, side, key, label, tip=None, width=34, browse=None):
        default = DEFAULTS.get(key, GUI_DEFAULTS.get(key, ""))
        v = self.vars[key] = tk.StringVar(value=default)
        f = ttk.Frame(tab)
        ttk.Entry(f, textvariable=v, width=width).pack(side="left")
        if browse:
            ttk.Button(f, text="…", width=3, command=browse).pack(side="left", padx=(4, 0))
        return self._place(tab, side, label, f, tip)

    # ---------- tabs ----------

    def _tab_general(self, nb):
        t = self._tab(nb)
        self.vars["profile"] = tk.StringVar()
        self.profile_cb = ttk.Combobox(t, state="readonly", width=46, values=PROFILE_LABELS,
                                       textvariable=self.vars["profile"], height=20)
        self.comboboxes.append(self.profile_cb)
        self.profile_cb.bind("<<ComboboxSelected>>", lambda e: self._on_profile_change())
        self._place(t, 0, "Device profile:", self.profile_cb, "The e-reader you will read the comic on.")
        self.profile_info = ttk.Label(t, style="Muted.TLabel")
        self._place(t, 0, "Features:", self.profile_info)
        self._choice(t, 0, "mode", "Reading mode:", "Manga reads right to left. Webtoon joins the images of each "
                     "folder and cuts them into pages, in the gaps between the panels.", command=self._on_mode_change)
        self._choice(t, 0, "format", "Image format:", "JPEG XL is only supported by the Apple Books profiles. "
                     "Copy keeps the source images untouched.")
        self._scale(t, 0, "quality", "Quality:", 1, 100, "Image quality (JPEG / JPEG XL). 100 = lossless for JPEG XL.")
        self._spin(t, 0, "limitmb", "Split EPUB every (MB):", 0, 10000, 10,
                   "Maximum size of each EPUB. 0 = no limit, minimum 20. "
                   "Send to Kindle: 200 MB on the website, 50 MB by email or app.")

        self._entry(t, 1, "title", "Title:", "Title of the EPUB. Empty = the name of the input. "
                    "Only used when there is one comic in the queue.", width=30)
        self._entry(t, 1, "author", "Author:", width=30)
        self._check(t, 1, "grayscale", "Grayscale (ideal for eInk)",
                    "It can only be turned off with a color profile.")
        self._choice(t, 1, "grayscale-mode", "Grayscale mode:", width=20)
        self._check(t, 1, "autocontrast", "Auto contrast")
        self._check(t, 1, "noblankimage", "Remove blank images")

        presets = ttk.Frame(t)
        for txt, fn in [("Good", "good"), ("Great", "great"), ("Best", "best"), ("Max", "max"), ("No filter", "nofilter")]:
            ttk.Button(presets, text=txt, width=9, command=lambda p=fn: self._apply_preset(p)).pack(side="left", padx=(0, 4))
        t._row[0] = max(t._row) + 1
        self._place(t, 0, "Quality presets:", presets,
                    "Good: grayscale JPEG q90 · Great: + no resize · Best: color JPEG q100, no resize · "
                    "Max: color PNG, no resize · No filter: turn off all filters")
        return t

    def _tab_image(self, nb):
        t = self._tab(nb)
        self._scale(t, 0, "brightness", "Brightness:", -100, 100, "> 0 lighter, < 0 darker")
        self._scale(t, 0, "contrast", "Contrast:", -100, 100, "> 0 more contrast, < 0 less contrast")
        self._check(t, 0, "resize", "Reduce images larger than the device")
        self._spin(t, 0, "zoom", "Zoom:", 0, 3, 0.1, "Stores the images bigger than the device for a better quality "
                   "when zooming. 0 = profile default (1.5 Apple Books, 1 others). Between 1 and 3 otherwise. "
                   "The size grows with the square of the zoom.", is_float=True)
        self._spin(t, 0, "aspect-ratio", "Aspect ratio:", -1, 3, 0.1, "Height / width of the output, between 0.5 and 3. "
                   "-1 = same as device, 0 = same as source (not for webtoon), 1.6 = Amazon advice for Kindle.",
                   is_float=True)
        self._spin(t, 0, "jxl-effort", "JPEG XL effort:", 1, 7, 1, "1 = fast, 7 = smaller files")

        self._color(t, 1, "foreground-color", "Foreground color:", "Hex RGB. Black = 000000")
        self._color(t, 1, "background-color", "Background color:",
                    "Hex RGB. White = FFFFFF, Light gray = DDDDDD, Dark gray = 777777")
        return t

    def _tab_crop(self, nb):
        t = self._tab(nb)
        self._check(t, 0, "crop", "Crop the margins", command=self._on_crop_change)
        tip = "Ratio of pixels allowed to be non-blank while cutting on this side."
        self.crop_widgets = [
            self._spin(t, 0, "crop-ratio-left", "Ratio left:", 0, 100, 1, tip),
            self._spin(t, 0, "crop-ratio-up", "Ratio top:", 0, 100, 1, tip),
            self._spin(t, 0, "crop-ratio-right", "Ratio right:", 0, 100, 1, tip),
            self._spin(t, 0, "crop-ratio-bottom", "Ratio bottom:", 0, 100, 1, tip),
            self._spin(t, 1, "crop-limit", "Limit (%):", 0, 100, 1, "Maximum cropping in percent. 0 = unlimited."),
            self._check(t, 1, "crop-skip-if-limit-reached", "Skip cropping if the limit is reached"),
        ]
        return t

    def _tab_pages(self, nb):
        t = self._tab(nb)
        self._choice(t, 0, "doublepagemode", "Double pages:", "What to do with the pages wider than tall.")
        self._check(t, 0, "keepsplitdoublepageaspect", "Keep the aspect of split double pages",
                    "Best for landscape rendering")
        self._check(t, 0, "combinesplitdoublepage", "Combine double pages split in 2 files",
                    "Detects a double page split in 2 consecutive pages and joins them (the facing edges must match).")
        self.landscape_cb = self._check(t, 0, "landscape", "Landscape only (Kindle Scribe)",
                                        "The pages are spread left and right. Kindle Scribe profiles only.")
        self._check(t, 0, "strip", "Strip the first folder from the table of contents if there is only one")

        self._choice(t, 1, "titlepage", "Title page:", width=24)
        self._check(t, 1, "covercaption", "Show \"Part X of Y\" on the cover when split")
        self._choice(t, 1, "sort", "Sort files:", width=28)
        self._entry(t, 1, "font", "Font (.ttf):", "TrueType font for the title page and the cover caption. "
                    "Empty = embedded Literata.", width=24, browse=self._pick_font)
        return t

    def _tab_advanced(self, nb):
        t = self._tab(nb)
        self._entry(t, 0, "exe", "go-comic-converter:", "Path of the go-comic-converter executable.",
                    width=52, browse=self._pick_exe)
        self._spin(t, 0, "workers", "Workers:", 1, 256, 1, "Number of images processed in parallel.")
        self._entry(t, 0, "extra_args", "Extra arguments:", "Passed as is to the tool, e.g. -crop-limit=10", width=52)
        self._check(t, 0, "use_saved_config", "Use the tool's saved config (~/.go-comic-converter.yaml) as the base",
                    "Off: the options of this window are the only ones that count (-ignore-config).")
        self._check(t, 0, "open_folder_when_done", "Open the output folder when the queue is done")
        self._choice(t, 0, "theme", "Appearance:", "Also switched with the switch at the top right.",
                     command=self._apply_theme, width=20)

        f = ttk.Frame(t)
        ttk.Button(f, text="Check version", command=lambda: self._run_simple(["-version"])).pack(side="left")
        ttk.Button(f, text="Show saved config", command=lambda: self._run_simple(["-show"])).pack(side="left", padx=4)
        ttk.Button(f, text="Reset this window", command=self._reset_options).pack(side="left")
        t._row[0] += 1
        self._place(t, 0, "", f)
        return t

    # ---------- reactions ----------

    def _profile_code(self):
        return self.vars["profile"].get().split(" - ", 1)[0] or DEFAULTS["profile"]

    def _on_profile_change(self):
        code = self._profile_code()
        if not self.vars["profile"].get():
            self.vars["profile"].set(PROFILE_LABELS[[p[0] for p in PROFILES].index(code)])
        feats = PROFILE_FEATURES.get(code, "")
        self.profile_info.configure(text=feats or "eInk, no special features")
        if "landscape" not in feats:
            self.vars["landscape"].set(False)
            self.landscape_cb.state(["disabled"])
        else:
            self.landscape_cb.state(["!disabled"])
        if "color" not in feats:
            self.vars["grayscale"].set(True)

    def _on_mode_change(self):
        if self._get_choice("mode") == 2 and float(self.vars["aspect-ratio"].get() or 0) == 0:
            self.vars["aspect-ratio"].set(-1.0)
            self._log("Webtoon mode needs an aspect ratio: set to -1 (same as device).\n")

    def _on_crop_change(self):
        state = ["!disabled"] if self.vars["crop"].get() else ["disabled"]
        for w in self.crop_widgets:
            w.state(state)

    def _apply_preset(self, name):
        if name in ("good", "great"):
            self.vars["grayscale"].set(True)
            self._set_choice("format", "jpeg")
            self.vars["quality"].set(90)
            self.vars["resize"].set(name == "good")
        elif name in ("best", "max"):
            if "color" not in PROFILE_FEATURES.get(self._profile_code(), ""):
                messagebox.showwarning(APP_NAME, "Color output needs a color profile. Grayscale was kept.")
            else:
                self.vars["grayscale"].set(False)
            self._set_choice("format", "png" if name == "max" else "jpeg")
            self.vars["quality"].set(100)
            self.vars["resize"].set(False)
        elif name == "nofilter":
            for k in ("crop", "autocontrast", "noblankimage", "combinesplitdoublepage"):
                self.vars[k].set(False)
            self.vars["brightness"].set(0)
            self.vars["contrast"].set(0)
            self._on_crop_change()
        self._log(f"Preset applied: {name}\n")

    # ---------- queue ----------

    def _add_inputs(self, paths):
        existing = {self.tree.set(i, "input") for i in self.tree.get_children()}
        for p in sorted(paths, key=natural_key):
            p = os.path.normpath(p)
            if p not in existing:
                self.tree.insert("", "end", values=(p, "Pending"))
                existing.add(p)
        self._restripe()

    def _restripe(self):
        """Alternate the colors of the rows of the queue."""
        for n, i in enumerate(self.tree.get_children()):
            self.tree.item(i, tags=("odd" if n % 2 else "even",))

    def _add_files(self):
        self._add_inputs(filedialog.askopenfilenames(parent=self, title="Add comics", filetypes=INPUT_TYPES))

    def _add_folder(self):
        d = filedialog.askdirectory(parent=self, title="Add a folder of images")
        if d:
            self._add_folder_path(d)

    def _add_folder_path(self, d):
        archives = [e for e in Path(d).iterdir() if e.is_file() and e.suffix.lower() in ARCHIVE_EXTS]
        if archives and messagebox.askyesno(
                APP_NAME, f"{Path(d).name} contains {len(archives)} comic archive(s).\n\n"
                          "Yes: add each archive separately\nNo: convert the folder itself as one comic"):
            self._add_inputs(map(str, archives))
            return
        self._add_inputs([d])

    def _on_drop(self, paths):
        if self.worker:
            self._log("Wait for the conversion to finish before adding comics.\n", "err")
            return
        skipped = []
        for p in sorted(paths, key=natural_key):
            if os.path.isdir(p):
                self._add_folder_path(p)
            elif Path(p).suffix.lower() in ARCHIVE_EXTS:
                self._add_inputs([p])
            else:
                skipped.append(Path(p).name)
        if skipped:
            self._log("Not a comic, skipped: " + ", ".join(skipped) + "\n", "err")

    def _remove_selected(self):
        if self.worker:
            return
        for i in self.tree.selection():
            self.tree.delete(i)
        self._restripe()

    def _clear_queue(self):
        if not self.worker:
            self.tree.delete(*self.tree.get_children())

    def _pick_output(self):
        d = filedialog.askdirectory(parent=self, title="Output folder")
        if d:
            self.vars["output_dir"].set(os.path.normpath(d))

    def _pick_font(self):
        f = filedialog.askopenfilename(parent=self, filetypes=[("TrueType font", "*.ttf"), ("All files", "*.*")])
        if f:
            self.vars["font"].set(os.path.normpath(f))

    def _pick_exe(self):
        f = filedialog.askopenfilename(parent=self, title="Locate go-comic-converter",
                                       filetypes=[("Executable", "*.exe"), ("All files", "*.*")])
        if f:
            self.vars["exe"].set(os.path.normpath(f))

    # ---------- command line ----------

    def _value(self, key):
        if key == "profile":
            return self._profile_code()
        if key in CHOICES:
            return self._get_choice(key)
        v = self.vars[key].get()
        if isinstance(DEFAULTS.get(key), str):
            v = v.strip().lstrip("#") if key.endswith("color") else v.strip()
        return v

    def _build_args(self, item, dry=False, json_out=False):
        args = []
        if not self.vars["use_saved_config"].get():
            args.append("-ignore-config")
        args.append(f"-input={item}")
        out = self.vars["output_dir"].get().strip()
        if out:
            args.append(f"-output={out}")
        title = self.vars["title"].get().strip()
        if title and len(self.tree.get_children()) <= 1:
            args.append(f"-title={title}")
        for key, default in DEFAULTS.items():
            try:
                v = self._value(key)
            except (tk.TclError, ValueError):
                raise ValueError(f"Invalid value for {key}")
            if isinstance(default, bool):
                if v != default:
                    args.append(f"-{key}={int(v)}")
            elif isinstance(default, float):
                if float(v) != default:
                    args.append(f"-{key}={float(v):g}")
            elif v != default and not (key == "font" and not v):
                args.append(f"-{key}={v}")
        extra = self.vars["extra_args"].get().strip()
        if extra:
            import shlex
            args.extend(shlex.split(extra, posix=False))
        if dry:
            args.append("-dry")
        if json_out:
            args.append("-json")
        return args

    def _validate(self):
        errs = []
        for key in ("foreground-color", "background-color"):
            v = self._value(key)
            if len(v) != 6 or any(c not in "0123456789abcdefABCDEF" for c in v):
                errs.append(f"{key}: must be 6 hex digits, like FFFFFF")
        lim = self.vars["limitmb"].get()
        if 0 < lim < 20:
            errs.append("Split size: 0 (no limit) or at least 20 MB")
        z = float(self.vars["zoom"].get())
        if z != 0 and not 1 <= z <= 3:
            errs.append("Zoom: 0, or between 1 and 3")
        ar = float(self.vars["aspect-ratio"].get())
        if ar not in (-1, 0) and not 0.5 <= ar <= 3:
            errs.append("Aspect ratio: -1, 0, or between 0.5 and 3")
        if self._get_choice("mode") == 2 and ar == 0:
            errs.append("Webtoon mode needs an aspect ratio other than 0")
        if not self.vars["grayscale"].get() and "color" not in PROFILE_FEATURES.get(self._profile_code(), ""):
            errs.append("Grayscale can only be turned off with a color profile")
        if self._get_choice("format") == "jxl" and "jxl" not in PROFILE_FEATURES.get(self._profile_code(), ""):
            errs.append("JPEG XL output is only supported by the Apple Books profiles")
        return errs

    def _show_command(self):
        items = [self.tree.set(i, "input") for i in self.tree.get_children()] or ["<input>"]
        try:
            args = self._build_args(items[0])
        except ValueError as e:
            messagebox.showerror(APP_NAME, str(e))
            return
        cmd = subprocess.list2cmdline(["go-comic-converter"] + args)
        self._log(cmd + "\n", "cmd")
        self.clipboard_clear()
        self.clipboard_append(cmd)
        self.status.set("Command copied to the clipboard")

    # ---------- running ----------

    def _exe(self):
        exe = find_exe(self.vars["exe"].get().strip())
        # The bundled copy is unpacked to a new temp folder on each run: don't save its path.
        if exe and exe != bundled_exe() and not self.vars["exe"].get().strip():
            self.vars["exe"].set(exe)
        return exe

    def _check_exe(self):
        if self._exe():
            return
        go = shutil.which("go")
        msg = ("go-comic-converter was not found.\n\n"
               "Set its path in the Advanced tab, or put it next to this program.\n\n")
        if go:
            if messagebox.askyesno(APP_NAME, msg + "Go is installed: install go-comic-converter now with\n"
                                   "go install github.com/celogeek/go-comic-converter/v3@latest ?"):
                self._install_with_go(go)
        else:
            messagebox.showwarning(APP_NAME, msg + "To install it: install Go from https://go.dev/dl/ then run\n"
                                   "go install github.com/celogeek/go-comic-converter/v3@latest")

    def _install_with_go(self, go):
        self._log("Installing go-comic-converter with go install…\n", "cmd")
        self.status.set("Installing go-comic-converter…")

        def run():
            try:
                p = subprocess.run([go, "install", "github.com/celogeek/go-comic-converter/v3@latest"],
                                   capture_output=True, text=True, **popen_kwargs())
                self.events.put(("log", p.stdout + p.stderr, "err" if p.returncode else None))
                self.events.put(("installed", p.returncode == 0))
            except OSError as e:
                self.events.put(("log", f"{e}\n", "err"))

        threading.Thread(target=run, daemon=True).start()

    def _run_simple(self, args):
        exe = self._exe()
        if not exe:
            self._check_exe()
            return

        def run():
            try:
                p = subprocess.run([exe] + args, capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", **popen_kwargs())
                self.events.put(("log", p.stdout + p.stderr, None))
            except OSError as e:
                self.events.put(("log", f"{e}\n", "err"))

        threading.Thread(target=run, daemon=True).start()

    def _start(self, dry):
        if self.worker:
            return
        exe = self._exe()
        if not exe:
            self._check_exe()
            return
        items = list(self.tree.get_children())
        if not items:
            messagebox.showinfo(APP_NAME, "Add a comic to convert first.")
            return
        try:
            errs = self._validate()
        except (tk.TclError, ValueError):
            errs = ["A number field contains an invalid value"]
        if errs:
            messagebox.showerror(APP_NAME, "Please fix:\n\n• " + "\n• ".join(errs))
            return
        try:
            jobs = [(i, self._build_args(self.tree.set(i, "input"), dry=dry, json_out=not dry)) for i in items]
        except ValueError as e:
            messagebox.showerror(APP_NAME, str(e))
            return
        self._save_settings()
        for i in items:
            self.tree.set(i, "status", "Pending")
        self.stop_requested = False
        self._set_running(True)
        self.worker = threading.Thread(target=self._work, args=(exe, jobs, dry), daemon=True)
        self.worker.start()

    def _work(self, exe, jobs, dry):
        ok = 0
        outputs = []
        for n, (item, args) in enumerate(jobs, 1):
            if self.stop_requested:
                self.events.put(("item", item, "Cancelled"))
                continue
            self.events.put(("item", item, "Running…"))
            self.events.put(("job", n, len(jobs)))
            self.events.put(("log", subprocess.list2cmdline(["go-comic-converter"] + args) + "\n", "cmd"))
            try:
                self.proc = subprocess.Popen([exe] + args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                             text=True, encoding="utf-8", errors="replace", bufsize=1,
                                             **popen_kwargs())
            except OSError as e:
                self.events.put(("log", f"Cannot start the converter: {e}\n", "err"))
                self.events.put(("item", item, "Error"))
                continue
            for line in self.proc.stdout:
                self._handle_line(line, outputs)
            code = self.proc.wait()
            self.proc = None
            if self.stop_requested:
                self.events.put(("item", item, "Cancelled"))
            elif code == 0:
                ok += 1
                self.events.put(("item", item, "Checked" if dry else "Done ✓"))
            else:
                self.events.put(("item", item, f"Error ({code})"))
        self.events.put(("finished", ok, len(jobs), dry, outputs))

    def _handle_line(self, line, outputs):
        s = line.strip()
        if s.startswith("{"):
            try:
                msg = json.loads(s)
            except json.JSONDecodeError:
                msg = None
            if isinstance(msg, dict):
                kind, data = msg.get("type"), msg.get("data") or {}
                if kind == "epubprogress":
                    self.events.put(("progress", data))
                elif kind == "options":
                    out = data.get("output")
                    if out:
                        outputs.append(out)
                    self.events.put(("log", f"Output: {out}\n", None))
                elif kind == "stats":
                    secs = data.get("elapse_ms", 0) / 1000
                    self.events.put(("log", f"Completed in {secs:.1f}s, memory {data.get('memory_usage_mb')} MB\n", "ok"))
                else:
                    self.events.put(("log", s + "\n", None))
                return
        if s:
            tag = "err" if "error" in s.lower() else None
            self.events.put(("log", line if line.endswith("\n") else line + "\n", tag))

    def _stop(self):
        self.stop_requested = True
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
        self.status.set("Stopping…")

    def _set_running(self, running):
        for b in (self.btn_go, self.btn_dry, self.btn_cmd):
            b.state(["disabled"] if running else ["!disabled"])
        self.btn_stop.state(["!disabled"] if running else ["disabled"])
        if not running:
            self.worker = None

    def _poll_events(self):
        try:
            while True:
                ev = self.events.get_nowait()
                kind = ev[0]
                if kind == "log":
                    self._log(ev[1], ev[2])
                elif kind == "item":
                    if self.tree.exists(ev[1]):
                        self.tree.set(ev[1], "status", ev[2])
                elif kind == "job":
                    self.job = (ev[1], ev[2])
                    self.progress["value"] = 0
                    self.status.set(f"Comic {ev[1]}/{ev[2]}: starting…")
                elif kind == "progress":
                    self._on_progress(ev[1])
                elif kind == "finished":
                    self._on_finished(*ev[1:])
                elif kind == "drop":
                    self._on_drop(ev[1])
                elif kind == "installed":
                    self.status.set("Installed" if ev[1] else "Install failed")
                    if ev[1]:
                        self._exe()
                        self._log(f"Installed: {self.vars['exe'].get()}\n", "ok")
        except queue.Empty:
            pass
        self.after(80, self._poll_events)

    def _on_progress(self, data):
        p = data.get("epubprogress", {})
        st = data.get("steps", {})
        cur, tot = p.get("current", 0), max(p.get("total", 1), 1)
        step, steps = st.get("current", 1), max(st.get("total", 1), 1)
        # Spread the steps (processing, writing) over the bar.
        self.progress["value"] = ((step - 1) + cur / tot) / steps * 100
        n, total = getattr(self, "job", (1, 1))
        self.status.set(f"Comic {n}/{total}: {data.get('description', '')} {cur}/{tot}")

    def _on_finished(self, ok, total, dry, outputs):
        self._set_running(False)
        self.progress["value"] = 100 if ok else 0
        word = "checked" if dry else "converted"
        self.status.set(f"{ok}/{total} {word}")
        self._log(f"--- {ok} of {total} comic(s) {word} ---\n", "ok" if ok == total else "err")
        if not dry and ok and self.vars["open_folder_when_done"].get() and os.name == "nt":
            folder = self.vars["output_dir"].get().strip()
            if not folder and outputs:
                folder = os.path.dirname(outputs[-1])
            if folder and os.path.isdir(folder):
                os.startfile(folder)

    def _log(self, text, tag=None):
        self.log.configure(state="normal")
        self.log.insert("end", text, tag or ())
        self.log.see("end")
        self.log.configure(state="disabled")

    # ---------- settings ----------

    def _collect_settings(self):
        data = {}
        for key in list(DEFAULTS) + list(GUI_DEFAULTS):
            try:
                data[key] = self._value(key)
            except (tk.TclError, ValueError):
                pass
        return data

    def _apply_settings(self, data):
        for key, default in {**DEFAULTS, **GUI_DEFAULTS}.items():
            if key not in data or key not in self.vars:
                continue
            v = data[key]
            try:
                if key == "profile":
                    codes = [p[0] for p in PROFILES]
                    if v in codes:
                        self.vars["profile"].set(PROFILE_LABELS[codes.index(v)])
                elif key in CHOICES:
                    self._set_choice(key, v)
                else:
                    self.vars[key].set(v)
            except tk.TclError:
                self.vars[key].set(default)
        self._on_profile_change()
        self._on_crop_change()

    def _load_settings(self):
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        if isinstance(data, dict) and data.get("settings_version", 1) < 2 and data.get("sort") == 1:
            # Saved before the GUI had its own default: the files were sorted as text.
            data["sort"] = PREFERRED["sort"]
        self._apply_settings({**DEFAULTS, **PREFERRED, **GUI_DEFAULTS, **data})

    def _save_settings(self):
        try:
            data = {**self._collect_settings(), "settings_version": SETTINGS_VERSION}
            SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _reset_options(self):
        if messagebox.askyesno(APP_NAME, "Reset every option to the go-comic-converter defaults?"):
            keep = {k: self._value(k) for k in ("exe", "output_dir", "theme")}
            self._apply_settings({**DEFAULTS, **PREFERRED, **GUI_DEFAULTS, **keep})

    def _on_close(self):
        if self.worker and not messagebox.askyesno(APP_NAME, "A conversion is running. Stop it and quit?"):
            return
        self._stop()
        self._save_settings()
        self.destroy()


if __name__ == "__main__":
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    App().mainloop()
