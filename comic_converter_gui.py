"""Desktop GUI for go-comic-converter (https://github.com/celogeek/go-comic-converter).

Runs the go-comic-converter command line tool with the options picked in the window,
over a queue of comics, and follows its progress through its -json output.
"""

import hashlib
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

import preview
from help_texts import HELP, SETTINGS_TABS, TUTORIAL
from theme import Theme, set_title_bar_dark, windows_dark_mode

APP_NAME = "Comic Converter"
EXE_NAME = "go-comic-converter.exe" if os.name == "nt" else "go-comic-converter"
SETTINGS_FILE = Path.home() / ".go-comic-converter-gui.json"
# Crops drawn page by page: {comic path: {page index: [x0, y0, x1, y1]}}, fractions of the source page.
CROPS_FILE = Path.home() / ".go-comic-converter-gui-crops.json"
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


def ask_folders(parent, title, initial_dir=None):
    """Folder picker in which several folders can be selected. Returns their paths, [] if cancelled.

    Tk's askdirectory can't select several folders: on Windows the folder dialog is opened directly
    (IFileOpenDialog), anywhere else or if that fails it falls back to askdirectory (one folder).
    """
    if os.name == "nt":
        try:
            return _ask_folders_windows(parent, title, initial_dir)
        except (AttributeError, OSError):
            pass
    d = filedialog.askdirectory(parent=parent, title=title, initialdir=initial_dir or None)
    return [d] if d else []


def _ask_folders_windows(parent, title, initial_dir):
    import ctypes
    from ctypes import wintypes

    ole32, shell32, user32 = ctypes.windll.ole32, ctypes.windll.shell32, ctypes.windll.user32
    HRESULT, PVOID = ctypes.c_long, ctypes.c_void_p

    class GUID(ctypes.Structure):
        _fields_ = [("d1", ctypes.c_ulong), ("d2", ctypes.c_ushort), ("d3", ctypes.c_ushort),
                    ("d4", ctypes.c_ubyte * 8)]

    def guid(text):
        g = GUID()
        ole32.CLSIDFromString(ctypes.c_wchar_p(text), ctypes.byref(g))
        return g

    def method(obj, index, *argtypes):
        """Method number index of the vtable of the COM object obj."""
        vtable = ctypes.cast(obj, ctypes.POINTER(ctypes.POINTER(PVOID)))[0]
        fn = ctypes.WINFUNCTYPE(HRESULT, PVOID, *argtypes)(vtable[index])
        return lambda *args: fn(obj, *args)

    def check(hr):
        if hr < 0:
            raise OSError(f"COM error 0x{hr & 0xFFFFFFFF:08X}")

    def release(obj):
        if obj.value:
            method(obj, 2)()

    CLSID_FileOpenDialog = guid("{DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7}")
    IID_IFileOpenDialog = guid("{D57C7288-D4AD-4768-BE02-9D969532D960}")
    IID_IShellItem = guid("{43826D1E-E718-42EE-BC55-A1E261C37BFE}")
    FOS_PICKFOLDERS, FOS_FORCEFILESYSTEM, FOS_ALLOWMULTISELECT = 0x20, 0x40, 0x200
    SIGDN_FILESYSPATH = 0x80058000
    ERROR_CANCELLED = 0x800704C7 - (1 << 32)

    ole32.CoInitializeEx.argtypes = [PVOID, ctypes.c_uint]
    ole32.CoCreateInstance.argtypes = [ctypes.POINTER(GUID), PVOID, ctypes.c_uint, ctypes.POINTER(GUID),
                                       ctypes.POINTER(PVOID)]
    ole32.CoTaskMemFree.argtypes = [PVOID]
    shell32.SHCreateItemFromParsingName.argtypes = [ctypes.c_wchar_p, PVOID, ctypes.POINTER(GUID),
                                                    ctypes.POINTER(PVOID)]
    user32.GetParent.argtypes = [wintypes.HWND]
    user32.GetParent.restype = wintypes.HWND

    # Tk has usually initialized COM already: S_FALSE, or RPC_E_CHANGED_MODE, are fine.
    initialized = ole32.CoInitializeEx(None, 0x2) >= 0  # COINIT_APARTMENTTHREADED
    dialog, results = PVOID(), PVOID()
    try:
        check(ole32.CoCreateInstance(ctypes.byref(CLSID_FileOpenDialog), None, 1,  # CLSCTX_INPROC_SERVER
                                     ctypes.byref(IID_IFileOpenDialog), ctypes.byref(dialog)))
        options = ctypes.c_uint()
        check(method(dialog, 10, ctypes.POINTER(ctypes.c_uint))(ctypes.byref(options)))  # GetOptions
        check(method(dialog, 9, ctypes.c_uint)(
            options.value | FOS_PICKFOLDERS | FOS_FORCEFILESYSTEM | FOS_ALLOWMULTISELECT))  # SetOptions
        method(dialog, 17, ctypes.c_wchar_p)(title)  # SetTitle
        if initial_dir and os.path.isdir(initial_dir):
            folder = PVOID()
            # The shell only parses backslashes.
            if shell32.SHCreateItemFromParsingName(os.path.normpath(initial_dir), None, ctypes.byref(IID_IShellItem),
                                                   ctypes.byref(folder)) >= 0:
                method(dialog, 12, PVOID)(folder)  # SetFolder
                release(folder)
        owner = user32.GetParent(parent.winfo_id()) or parent.winfo_id()
        hr = method(dialog, 3, wintypes.HWND)(owner)  # Show: modal to the window
        if hr == ERROR_CANCELLED:
            return []
        check(hr)
        check(method(dialog, 27, ctypes.POINTER(PVOID))(ctypes.byref(results)))  # GetResults
        count = ctypes.c_uint()
        check(method(results, 7, ctypes.POINTER(ctypes.c_uint))(ctypes.byref(count)))  # GetCount
        paths = []
        for i in range(count.value):
            item, name = PVOID(), PVOID()
            check(method(results, 8, ctypes.c_uint, ctypes.POINTER(PVOID))(i, ctypes.byref(item)))  # GetItemAt
            try:
                check(method(item, 5, ctypes.c_uint, ctypes.POINTER(PVOID))(  # GetDisplayName
                    SIGDN_FILESYSPATH, ctypes.byref(name)))
                paths.append(ctypes.wstring_at(name.value))
                ole32.CoTaskMemFree(name)
            finally:
                release(item)
        return paths
    finally:
        release(results)
        release(dialog)
        if initialized:
            ole32.CoUninitialize()


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
        self.geometry("1240x900")
        self.minsize(1040, 720)

        self.vars = {}
        self.events = queue.Queue()
        self.worker = None
        self.proc = None
        self.stop_requested = False
        self.comboboxes = []
        self.help_icons = []        # the ? icons, recolored with the theme
        self.tutorial = None
        self.tutorial_seen = True   # set from the settings: the tutorial opens once, at the first start
        # Preview: a token per load, so the results of an older load are dropped.
        self.pv_mode = "original"
        self.pv_token = 0
        self.pv_items = []    # queue items, in the order of the comic picker
        self.pv_pages = []    # preview.Page of the comic shown
        self.pv_photos = {}   # index -> PhotoImage of the thumbnail
        self.pv_proc = None   # converter run for the preview
        self.pv_cache = {}    # (input, arguments) -> EPUB written for the preview
        self.pv_tmp = tempfile.mkdtemp(prefix="comic-converter-preview-")
        self.pv_note = ""
        self.pv_whole = False  # the pages shown are the whole source pages: crops can be drawn on them
        self.pv_tiles = {}     # index -> (x, y) of the thumbnail
        self.viewer = None
        self.pending_viewer = None  # source page to open in the viewer once the Original preview is loaded
        self.page_crops = self._load_crops()
        self.crop_support = {}  # converter path -> knows -pagecrops
        self.last_dir = None  # where the folder dialog opens next
        self.theme = Theme(self)
        self.theme.apply(self._saved_theme_is_dark())  # draws the images the widgets are built with

        self._build()
        self._load_settings()
        self._on_profile_change()
        self._apply_theme()
        # The Converted preview follows the options: it's redone a moment after a change.
        self.pv_change_after = None
        for var in self.vars.values():
            var.trace_add("write", lambda *_: self._on_option_change())
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._poll_events)
        self.after(200, self._check_exe)
        if not self.tutorial_seen:  # first start: how to use the app
            self.tutorial_seen = True
            self.after(700, self._show_tutorial)
        if os.name == "nt":
            try:
                self.file_drop = FileDrop(self, lambda paths: self.events.put(("drop", paths)))
            except (AttributeError, OSError) as e:
                self._log(f"Drag and drop is not available: {e}\n", "err")

    # ---------- layout ----------

    def _build(self):
        """Header; a drop zone while the queue is empty, then the workspace: preview and export
        options, the queue with the progress, the log. All the options are in the Settings window."""
        self._build_header()
        self._build_settings_window()  # creates the variables of the options, used by the export panel

        root = ttk.Frame(self, padding=(12, 10, 12, 12), style="Backdrop.TFrame")
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.empty_view = self._build_drop_zone(root)
        self.work_view = ttk.Frame(root, style="Backdrop.TFrame")
        self.work_view.columnconfigure(0, weight=1)
        self.work_view.rowconfigure(0, weight=1)

        paned = self.work_paned = ttk.PanedWindow(self.work_view, orient="vertical")
        paned.grid(row=0, column=0, sticky="nsew")
        self.sashes_placed = False
        paned.bind("<Configure>", lambda e: self.sashes_placed or self.after_idle(self._place_sashes))
        top = ttk.Frame(paned, style="Backdrop.TFrame")
        top.columnconfigure(0, weight=1)
        top.rowconfigure(0, weight=1)
        self._build_preview(top).grid(row=0, column=0, sticky="nsew")
        self._build_export(top).grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        paned.add(top, weight=5)
        paned.add(self._build_queue(paned), weight=3)
        paned.add(self._build_log(paned), weight=1)

        # The preview follows the sort of the files.
        self.pv_after = None
        self.vars["sort"].trace_add("write", lambda *_: self._schedule_preview() if self.pv_mode == "original" else None)
        self._update_view()

    def _build_settings_window(self):
        """All the options, in tabs, in a window of their own opened from the header."""
        w = self.settings_win = tk.Toplevel(self)
        w.withdraw()
        w.title(f"{APP_NAME} - Settings")
        w.geometry("940x560")
        w.minsize(800, 460)
        w.transient(self)
        w.protocol("WM_DELETE_WINDOW", w.withdraw)
        frame = ttk.Frame(w, padding=12, style="Backdrop.TFrame")
        frame.pack(fill="both", expand=True)
        nb = self.notebook = ttk.Notebook(frame)
        nb.pack(fill="both", expand=True)
        nb.add(self._tab_general(nb), text="General")
        nb.add(self._tab_image(nb), text="Image")
        nb.add(self._tab_crop(nb), text="Crop")
        nb.add(self._tab_pages(nb), text="Pages & Layout")
        nb.add(self._tab_advanced(nb), text="Advanced")
        bar = ttk.Frame(frame, style="Backdrop.TFrame")
        bar.pack(fill="x", pady=(10, 0))
        ttk.Label(bar, text="Changes apply right away, and are remembered.",
                  style="Backdrop.TLabel").pack(side="left")
        ttk.Button(bar, text="Done", style="Accent.TButton", command=w.withdraw).pack(side="right", ipadx=10)

    def _show_tutorial(self):
        """How to use the app, with every option explained (the texts of the ? icons)."""
        t = self.tutorial
        if not (t and t.winfo_exists()):
            t = self.tutorial = tk.Toplevel(self)
            t.title(f"{APP_NAME} - Help")
            t.geometry("760x820")
            t.minsize(520, 400)
            frame = ttk.Frame(t, padding=12, style="Backdrop.TFrame")
            frame.pack(fill="both", expand=True)
            card, body = self._card(frame)
            card.pack(fill="both", expand=True)
            body.columnconfigure(0, weight=1)
            body.rowconfigure(0, weight=1)
            t.text = tk.Text(body, wrap="word", relief="flat", borderwidth=0, highlightthickness=0, padx=16, pady=10,
                             font=("Segoe UI", 10), cursor="arrow", spacing1=2, spacing3=4)
            t.text.grid(row=0, column=0, sticky="nsew")
            sb = ttk.Scrollbar(body, orient="vertical", command=t.text.yview)
            sb.grid(row=0, column=1, sticky="ns")
            t.text.configure(yscrollcommand=sb.set)
            bar = ttk.Frame(frame, style="Backdrop.TFrame")
            bar.pack(fill="x", pady=(10, 0))
            ttk.Label(bar, text="Hover or click the ? next to an option to read its explanation.",
                      style="Backdrop.TLabel").pack(side="left")
            ttk.Button(bar, text="Close", style="Accent.TButton", command=t.destroy).pack(side="right", ipadx=10)
            t.bind("<Escape>", lambda e: t.destroy())
            self._fill_tutorial(t.text)
            self._style_tutorial()
        t.deiconify()
        t.lift()
        t.focus_set()
        set_title_bar_dark(t, self.theme.p["dark"])

    def _fill_tutorial(self, text):
        text.insert("end", "How to use Comic Converter\n", "h1")
        for heading, paragraphs in TUTORIAL:
            text.insert("end", heading + "\n", "h2")
            for para in paragraphs:
                if para.startswith("options:"):
                    keys = dict(SETTINGS_TABS)[para.split(":", 1)[1]]
                    for key in keys:
                        title, body = HELP[key]
                        text.insert("end", title, "opt")
                        text.insert("end", f"  {body}\n", "body")
                else:
                    text.insert("end", para + "\n", "body")
        text.configure(state="disabled")

    def _style_tutorial(self):
        p, text = self.theme.p, self.tutorial.text
        text.configure(background=p["card"], foreground=p["text"], selectbackground=p["select"],
                       selectforeground=p["select_text"])
        text.tag_configure("h1", font=("Segoe UI Semibold", 17), spacing3=6, foreground=p["text"])
        text.tag_configure("h2", font=("Segoe UI Semibold", 12), spacing1=14, spacing3=4, foreground=p["select"])
        text.tag_configure("opt", font=("Segoe UI Semibold", 10), foreground=p["text"])
        text.tag_configure("body", foreground=p["text"], lmargin1=0, lmargin2=0)

    def _show_settings(self):
        w = self.settings_win
        w.deiconify()
        w.lift()
        w.focus_set()
        set_title_bar_dark(w, self.theme.p["dark"])

    def _build_drop_zone(self, parent):
        card, body = self._card(parent)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)
        c = self.drop_canvas = tk.Canvas(body, highlightthickness=0, borderwidth=0)
        c.grid(row=0, column=0, sticky="nsew")
        self.drop_buttons = ttk.Frame(c)
        ttk.Button(self.drop_buttons, text="Select Folder", style="Accent.TButton",
                   command=self._add_folder).pack(side="left", ipadx=12, ipady=4)
        ttk.Button(self.drop_buttons, text="Select File", command=self._add_files).pack(side="left", padx=(10, 0),
                                                                                       ipadx=12, ipady=4)
        c.bind("<Configure>", lambda e: self._draw_drop_zone())
        return card

    def _draw_drop_zone(self):
        c, p = self.drop_canvas, self.theme.p
        w, h = c.winfo_width(), c.winfo_height()
        c.delete("all")
        c.configure(background=p["card"])
        m, r = 14, 18
        x0, y0, x1, y1 = m, m, w - m, h - m
        if x1 - x0 < 2 * r or y1 - y0 < 2 * r:
            return
        # Rounded dashed frame.
        pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1, x0 + r, y1,
               x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
        # Filled with the card color: the corners of the buttons show it.
        c.create_polygon(pts, smooth=True, fill=p["card"], outline=p["muted"], dash=(8, 6), width=2)
        cx, cy = w / 2, h / 2
        # Arrow into a tray.
        c.create_polygon(cx - 7, cy - 104, cx + 7, cy - 104, cx + 7, cy - 78, cx + 18, cy - 78, cx, cy - 58,
                         cx - 18, cy - 78, cx - 7, cy - 78, fill=p["muted"], outline="")
        c.create_line(cx - 30, cy - 62, cx - 30, cy - 48, cx + 30, cy - 48, cx + 30, cy - 62, fill=p["muted"],
                      width=4, joinstyle="round", capstyle="round")
        c.create_text(cx, cy - 22, text="Drop comics or folders here", font=("Segoe UI Semibold", 16), fill=p["text"])
        c.create_text(cx, cy + 8, text="Folders of images, CBZ, ZIP, CBR, RAR or PDF files - as many as you like",
                      font=("Segoe UI", 10), fill=p["muted"])
        c.create_window(cx, cy + 58, window=self.drop_buttons)

    def _place_sashes(self):
        """First split of the workspace: preview and options, queue, log. Done on the first resize
        of the pane, once it has its real height."""
        h = self.work_paned.winfo_height()
        if h > 300 and not self.sashes_placed:
            self.work_paned.sashpos(0, int(h * 0.58))
            self.work_paned.sashpos(1, int(h * 0.87))
            self.sashes_placed = True

    def _update_view(self):
        """The drop zone while the queue is empty, the workspace after."""
        if self.tree.get_children():
            self.empty_view.grid_remove()
            self.work_view.grid(row=0, column=0, sticky="nsew")
        else:
            self.work_view.grid_remove()
            self.empty_view.grid(row=0, column=0, sticky="nsew")
        self._refresh_picker()

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
        c.create_text(0, y, text="⚙  Settings", font=("Segoe UI Semibold", 11), anchor="e",
                      tags=("right", "settings", "settings_text"))
        c.create_text(0, y, text="?  Help", font=("Segoe UI Semibold", 11), anchor="e",
                      tags=("right", "help", "help_text"))
        c.tag_bind("switch", "<Button-1>", lambda e: self._toggle_dark())
        c.tag_bind("settings", "<Button-1>", lambda e: self._show_settings())
        c.tag_bind("help", "<Button-1>", lambda e: self._show_tutorial())
        for tag in ("switch", "settings", "help"):
            c.tag_bind(tag, "<Enter>", lambda e: c.configure(cursor="hand2"))
            c.tag_bind(tag, "<Leave>", lambda e: c.configure(cursor=""))
        c.bind("<Configure>", lambda e: self._place_header())

    def _place_header(self):
        c, w = self.header, self.header.winfo_width()
        y = self.header.winfo_height() // 2
        sw = self.theme.photos["switch_on"].width()
        c.coords("moon", w - 16, y - 1)
        c.coords("switch", w - 38, y)
        c.coords("sun", w - 44 - sw, y - 1)
        c.coords("settings_text", w - 44 - sw - 44, y)
        c.coords("help_text", w - 44 - sw - 44 - 120, y)

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
        c.itemconfigure("settings_text", fill=p["title"])
        c.itemconfigure("help_text", fill=p["title"])
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
        self._draw_drop_zone()
        self.pv_canvas.configure(background=p["card"])
        self._layout_thumbs()
        self._style_mode_buttons()
        for icon in self.help_icons:
            icon.configure(background=p["card"])
            icon.itemconfigure("dot", fill=p["select"], outline=p["accent_border"])
        if self.tutorial and self.tutorial.winfo_exists():
            self._style_tutorial()
        for win in (self.settings_win, self.viewer, self.tutorial):
            if win and win.winfo_exists():
                win.configure(background=p["bg"])
                if win.winfo_viewable():
                    set_title_bar_dark(win, dark)
        if self.viewer and self.viewer.winfo_exists():
            self.viewer.canvas.configure(background=p["bg"])
        set_title_bar_dark(self, dark)

    def _toggle_dark(self):
        self._set_choice("theme", "light" if self.theme.p["dark"] else "dark")
        self._apply_theme()

    def _build_queue(self, parent):
        card, box = self._card(parent)
        box.columnconfigure(0, weight=1)
        box.rowconfigure(1, weight=1)

        bar = ttk.Frame(box)
        bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(bar, text="Comics", style="CardTitle.TLabel").pack(side="left", padx=(0, 14))
        for txt, cmd in (("Add folders…", self._add_folder), ("Add files…", self._add_files),
                         ("Remove", self._remove_selected), ("Clear finished", self._clear_finished),
                         ("Clear all", self._clear_queue)):
            ttk.Button(bar, text=txt, command=cmd).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="Open output folder", command=self._open_output).pack(side="right")
        self.queue_count = ttk.Label(bar, style="Muted.TLabel")
        self.queue_count.pack(side="right", padx=(0, 12))

        cols = ("input", "crops", "status", "output")
        self.tree = ttk.Treeview(box, columns=cols, show="headings", height=6, selectmode="extended")
        self.tree.heading("input", text="Comic (folder or file)")
        self.tree.heading("crops", text="✂")
        self.tree.heading("status", text="Status")
        self.tree.heading("output", text="EPUB")
        self.tree.column("input", width=500)
        self.tree.column("crops", width=50, anchor="center", stretch=False)
        self.tree.column("status", width=130, anchor="center", stretch=False)
        self.tree.column("output", width=300)
        self.tree.grid(row=1, column=0, sticky="nsew")
        sb = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
        sb.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<Delete>", lambda e: self._remove_selected())
        self.tree.bind("<Double-1>", lambda e: self._preview_item(self.tree.identify_row(e.y)))
        Tooltip(self.tree, "Double-click a comic to preview it. Drop more comics anywhere on the window. "
                           "Delete removes the selected ones.")

        # Status display, in the style of an LCD, with the progress of the whole queue.
        lcd = ttk.Frame(box, style="LCD.TFrame", padding=self.theme.padding("LCD.TFrame"))
        lcd.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        lcd.columnconfigure(0, weight=1)
        self.status = tk.StringVar(value="Ready")
        ttk.Label(lcd, textvariable=self.status, style="LCD.TLabel").grid(row=0, column=0, sticky="w")
        self.progress = ttk.Progressbar(lcd, mode="determinate", maximum=100)
        self.progress.grid(row=1, column=0, sticky="ew", pady=(3, 0))
        return card

    def _build_log(self, parent):
        card, box = self._card(parent, "Log")
        box.columnconfigure(0, weight=1)
        box.rowconfigure(0, weight=1)
        inset = ttk.Frame(box, style="Inset.TFrame", padding=self.theme.padding("Inset.TFrame"))
        inset.grid(row=0, column=0, sticky="nsew")
        inset.columnconfigure(0, weight=1)
        inset.rowconfigure(0, weight=1)
        self.log = tk.Text(inset, height=3, wrap="word", font=("Consolas", 9), state="disabled",
                           relief="flat", borderwidth=0, highlightthickness=0, padx=6, pady=4)
        self.log.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(box, orient="vertical", command=self.log.yview)
        sb.grid(row=0, column=1, sticky="ns", padx=(4, 0))
        self.log.configure(yscrollcommand=sb.set)
        return card

    def _build_export(self, parent):
        """The options most used, on the right of the preview. They share their variables with the
        Settings window: a change in one shows in the other."""
        card, box = self._card(parent, "Export")
        box.columnconfigure(1, weight=1)
        rows = [0]

        def row(label, widget, key):
            r = rows[0]
            ttk.Label(box, text=label).grid(row=r, column=0, sticky="w", padx=(0, 10), pady=2)
            widget.grid(row=r, column=1, sticky="ew", pady=2)
            self._help_icon(box, key).grid(row=r, column=2, padx=(6, 0))
            rows[0] += 1

        def combo(key, values, command=None):
            cb = ttk.Combobox(box, state="readonly", values=values, textvariable=self.vars[key], width=28)
            self.comboboxes.append(cb)
            if command:
                cb.bind("<<ComboboxSelected>>", lambda e: command())
            return cb

        out = ttk.Frame(box)
        out.columnconfigure(0, weight=1)
        self.vars["output_dir"] = tk.StringVar()
        ttk.Entry(out, textvariable=self.vars["output_dir"], width=10).grid(row=0, column=0, sticky="ew")
        ttk.Button(out, text="…", width=3, command=self._pick_output).grid(row=0, column=1, padx=(4, 0))
        row("Output folder", out, "output_dir")
        row("Device", combo("profile", PROFILE_LABELS, self._on_profile_change), "profile")
        row("Reading mode", combo("mode", [l for _, l in CHOICES["mode"]], self._on_mode_change), "mode")
        row("Image format", combo("format", [l for _, l in CHOICES["format"]]), "format")
        q = ttk.Frame(box)
        ttk.Scale(q, from_=1, to=100, variable=self.vars["quality"],
                  command=lambda x: self.vars["quality"].set(round(float(x)))).pack(side="left", fill="x", expand=True)
        ttk.Spinbox(q, from_=1, to=100, textvariable=self.vars["quality"], width=4).pack(side="left", padx=(6, 0))
        row("Quality", q, "quality")
        row("Split every (MB)", ttk.Spinbox(box, from_=0, to=10000, increment=10, textvariable=self.vars["limitmb"],
                                            width=8), "limitmb")
        row("Title page", combo("titlepage", [l for _, l in CHOICES["titlepage"]]), "titlepage")
        checks = ttk.Frame(box)
        for i, (text, key, cmd) in enumerate((("Grayscale", "grayscale", None), ("Auto contrast", "autocontrast", None),
                                              ("Crop", "crop", self._on_crop_change))):
            ttk.Checkbutton(checks, text=text, variable=self.vars[key], command=cmd).pack(side="left",
                                                                                         padx=(12 if i else 0, 0))
            self._help_icon(checks, key).pack(side="left", padx=(3, 0))
        checks.grid(row=rows[0], column=0, columnspan=3, sticky="w", pady=(6, 0))
        more = ttk.Frame(box)
        more.grid(row=rows[0] + 1, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        ttk.Button(more, text="All settings…", command=self._show_settings).pack(side="left")
        self.btn_cmd = ttk.Button(more, text="Command", command=self._show_command)
        self.btn_cmd.pack(side="right")
        self.btn_dry = ttk.Button(more, text="Dry run", command=lambda: self._start(dry=True))
        self.btn_dry.pack(side="right", padx=6)
        Tooltip(self.btn_dry, "Checks the options for every comic, without converting.")
        Tooltip(self.btn_cmd, "Copies the go-comic-converter command line of these options.")

        box.rowconfigure(100, weight=1)  # pushes the buttons to the bottom
        acts = ttk.Frame(box)
        acts.grid(row=101, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        acts.columnconfigure(0, weight=1)
        self.btn_go = ttk.Button(acts, text="Convert all", style="Accent.TButton",
                                 command=lambda: self._start(dry=False))
        self.btn_go.grid(row=0, column=0, sticky="ew", ipady=5)
        self.btn_stop = ttk.Button(acts, text="Stop", command=self._stop, state="disabled")
        self.btn_stop.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        return card

    # ---------- preview ----------

    THUMB_W, THUMB_H = 120, 170

    def _build_preview(self, parent):
        card, box = self._card(parent)
        box.columnconfigure(0, weight=1)
        box.rowconfigure(1, weight=1)
        bar = ttk.Frame(box)
        bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(bar, text="Preview", style="CardTitle.TLabel").pack(side="left")
        ttk.Button(bar, text="◀", width=3, command=lambda: self._step_preview(-1)).pack(side="left", padx=(14, 4))
        self.pv_var = tk.StringVar()
        self.pv_combo = ttk.Combobox(bar, state="readonly", textvariable=self.pv_var, width=46, height=20)
        self.pv_combo.pack(side="left")
        self.pv_combo.bind("<<ComboboxSelected>>", lambda e: self._load_preview())
        self.comboboxes.append(self.pv_combo)
        ttk.Button(bar, text="▶", width=3, command=lambda: self._step_preview(1)).pack(side="left", padx=4)
        self.pv_btn_conv = ttk.Button(bar, text="Converted", command=lambda: self._set_preview_mode("converted"))
        self.pv_btn_conv.pack(side="right")
        self.pv_btn_orig = ttk.Button(bar, text="Original", command=lambda: self._set_preview_mode("original"))
        self.pv_btn_orig.pack(side="right", padx=(0, 4))
        Tooltip(self.pv_btn_orig, "The pages as they are, in the order of the EPUB.")
        Tooltip(self.pv_btn_conv, "What the e-reader will show, with the current settings: crop, grayscale, "
                                  "split double pages, title page... The comic is converted first.")

        self.pv_canvas = tk.Canvas(box, highlightthickness=0, borderwidth=0)
        self.pv_canvas.grid(row=1, column=0, sticky="nsew")
        sb = ttk.Scrollbar(box, orient="vertical", command=self.pv_canvas.yview)
        sb.grid(row=1, column=1, sticky="ns")
        self.pv_canvas.configure(yscrollcommand=sb.set)
        self.pv_canvas.bind("<Configure>", lambda e: self._layout_thumbs())
        self.pv_canvas.bind("<MouseWheel>", lambda e: self.pv_canvas.yview_scroll(-e.delta // 120, "units"))
        self.pv_info = ttk.Label(box, style="Muted.TLabel")
        self.pv_info.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))
        return card

    def _on_option_change(self):
        """Redoes the Converted preview once the options stop changing (typing, dragging a slider)."""
        if self.pv_mode != "converted":
            return
        if self.pv_change_after:
            self.after_cancel(self.pv_change_after)
        self.pv_change_after = self.after(900, self._refresh_converted)

    def _refresh_converted(self):
        self.pv_change_after = None
        if self.pv_mode == "converted":
            self._load_preview()

    def _schedule_preview(self):
        """Reloads the preview once the current changes are done."""
        if self.pv_after:
            self.after_cancel(self.pv_after)
        self.pv_after = self.after_idle(self._load_preview)

    def destroy(self):
        for name in ("pv_after", "pv_change_after"):
            if getattr(self, name, None):
                self.after_cancel(getattr(self, name))
                setattr(self, name, None)
        super().destroy()

    def _style_mode_buttons(self):
        conv = self.pv_mode == "converted"
        self.pv_btn_conv.configure(style="Accent.TButton" if conv else "TButton")
        self.pv_btn_orig.configure(style="TButton" if conv else "Accent.TButton")

    def _set_preview_mode(self, mode):
        self.pv_mode = mode
        self._style_mode_buttons()
        self._load_preview()

    def _refresh_picker(self):
        """Lists the queue in the comic picker, keeping the comic shown when it's still there."""
        items = list(self.tree.get_children())
        shown = self.pv_items[self.pv_combo.current()] if self.pv_items and self.pv_combo.current() >= 0 else None
        self.pv_items = items
        self.pv_combo.configure(values=[f"{n}. {os.path.basename(self.tree.set(i, 'input'))}"
                                        for n, i in enumerate(items, 1)])
        self.queue_count.configure(text=f"{len(items)} comic{'s' if len(items) != 1 else ''}")
        if not items:
            self.pv_var.set("")
            self._clear_preview()
            return
        if shown in items:
            self.pv_combo.current(items.index(shown))
        else:
            self.pv_combo.current(0)
            self._load_preview()

    def _preview_item(self, item):
        if item in self.pv_items:
            self.pv_combo.current(self.pv_items.index(item))
            self._load_preview()

    def _step_preview(self, step):
        if self.pv_items:
            self.pv_combo.current((self.pv_combo.current() + step) % len(self.pv_items))
            self._load_preview()

    def _clear_preview(self, info=""):
        self.pv_token += 1  # drops the results of a load still running
        if self.pv_proc and self.pv_proc.poll() is None:
            self.pv_proc.terminate()
        self.pv_pages, self.pv_photos = [], {}
        self.pv_canvas.delete("all")
        self.pv_info.configure(text=info)

    def _load_preview(self):
        """Shows the pages of the comic selected in the picker, in a thread."""
        self.pv_after = None
        if not self.pv_items or self.pv_combo.current() < 0:
            return self._clear_preview()
        path = self.tree.set(self.pv_items[self.pv_combo.current()], "input")
        self._clear_preview("Loading…")
        token = self.pv_token
        if not preview.HAVE_PIL:
            return self.pv_info.configure(text="The preview needs Pillow (pip install pillow).")
        exe = self._exe()
        self.pv_whole = False
        if self.pv_mode == "original":
            try:
                pages = preview.source_pages(path, self._get_choice("sort"))
            except (OSError, ValueError) as e:  # unreadable folder or bad zip
                return self.pv_info.configure(text=f"Can't read this comic: {e}")
            if pages is not None:
                self.pv_whole = True
                return self._start_thumbs(token, pages, "")
            # CBR/RAR and PDF: the converter extracts the pages, with no filter.
            args = ["-ignore-config", f"-input={path}", "-profile=HR", "-nofilter", "-grayscale=0",
                    "-titlepage=0", "-covercaption=0", "-format=jpeg", "-quality=85",
                    f"-sort={self._get_choice('sort')}"]
            if exe and self._crops_supported(exe):
                # A crop of the whole page for every page: no page is split, one image per page.
                args.append(f"-pagecrops={self._crops_file({'*': [0, 0, 1, 1]})}")
                self.pv_whole = True
                note = "Extracted by the converter."
            else:
                note = "Extracted by the converter: double pages appear split."
        else:
            try:
                errs = self._validate()
                args = self._build_args(path)
            except (tk.TclError, ValueError):
                errs, args = ["A number field contains an invalid value"], []
            if errs:
                return self.pv_info.configure(text="Can't preview: " + "; ".join(errs))
            note = ("Pages as your e-reader shows them, with the current settings (◧ ◨: side of a split page). "
                    "Updated when you change a setting.")
        if not exe:
            return self.pv_info.configure(text="go-comic-converter was not found: see Settings > Advanced.")
        epub = self.pv_cache.get((path, tuple(args)))
        if epub and os.path.isfile(epub):
            return self._start_thumbs(token, None, note, epub=epub)
        epub = os.path.join(self.pv_tmp, f"{token}.epub")
        # Overrides at the end: the last value of a flag wins. One EPUB, in a format Pillow reads.
        run_args = args + [f"-output={epub}", "-limitmb=0", "-json"]
        if self._get_choice("format") == "jxl" and self.pv_mode == "converted":
            run_args.append("-format=jpeg")
        self._start_thumbs(token, None, note, epub=epub, exe=exe, args=run_args, key=(path, tuple(args)))

    def _start_thumbs(self, token, pages, note, epub=None, exe=None, args=None, key=None):
        threading.Thread(target=self._preview_worker, args=(token, pages, note, epub, exe, args, key),
                         daemon=True).start()

    def _preview_worker(self, token, pages, note, epub, exe, args, key):
        put = lambda *ev: self.events.put(("pv",) + (token,) + ev)
        stale = lambda: token != self.pv_token
        try:
            if args:
                def progress(d):
                    p, st = d.get("epubprogress", {}), d.get("steps", {})
                    put("info", f"Converting for the preview: {d.get('description', '')} "
                                f"{p.get('current', 0)}/{p.get('total', 0)} (step {st.get('current', 1)}/{st.get('total', 2)})")
                put("info", "Converting for the preview…")
                err = preview.run_converter(exe, args, popen_kwargs(), progress, stale,
                                            on_start=lambda proc: setattr(self, "pv_proc", proc))
                if err:
                    return put("info", "" if err == "cancelled" else f"Preview failed: {err}")
                put("cached", key, epub)
            if epub:
                pages = preview.epub_pages(epub)
            if stale():
                return
            put("pages", pages, note)
            for i, page in enumerate(pages):
                if stale():
                    return
                try:
                    png, size = preview.thumbnail(page.load(), self.THUMB_W, self.THUMB_H)
                except Exception:  # a page Pillow can't read (e.g. JPEG XL): left as a blank tile
                    png = None
                put("thumb", i, png)
            put("done")
        except (OSError, ValueError, KeyError, AttributeError) as e:
            put("info", f"Preview failed: {e}")

    def _on_preview_event(self, token, kind, *data):
        if token != self.pv_token:
            return
        if kind == "info":
            self.pv_info.configure(text=data[0])
        elif kind == "cached":
            self.pv_cache[data[0]] = data[1]
        elif kind == "pages":
            self.pv_pages, note = data
            self.pv_note = note
            self.pv_info.configure(text=f"{len(self.pv_pages)} pages - loading…  {note}")
            self._layout_thumbs()
            if self.pending_viewer is not None:  # "Edit the crop" from the Converted view
                sid, self.pending_viewer = self.pending_viewer, None
                for i, page in enumerate(self.pv_pages):
                    if page.source_id == sid:
                        self._open_viewer(i)
                        break
            elif self.viewer and self.viewer.winfo_exists():
                self._show_page(self.viewer.index)  # the pages changed under the viewer
        elif kind == "thumb":
            i, png = data
            if png:
                self.pv_photos[i] = tk.PhotoImage(master=self, data=png)
                self.pv_canvas.itemconfigure(f"img{i}", image=self.pv_photos[i])
                self._draw_crop_mark(i)
        elif kind == "done":
            self.pv_info.configure(text=f"{len(self.pv_pages)} pages. Click a page to see it bigger.  {self.pv_note}")

    def _layout_thumbs(self):
        """Places the thumbnails in a grid as wide as the preview."""
        c, p = self.pv_canvas, self.theme.p
        c.delete("all")
        if not self.pv_pages:
            return
        tw, th, gap, cap = self.THUMB_W, self.THUMB_H, 14, 18
        cols = max(1, (c.winfo_width() - gap) // (tw + gap))
        x_off = max(gap, (c.winfo_width() - cols * (tw + gap) + gap) // 2)
        self.pv_tiles = {}
        for i, page in enumerate(self.pv_pages):
            r, col = divmod(i, cols)
            x, y = x_off + col * (tw + gap), gap + r * (th + cap + gap)
            self.pv_tiles[i] = (x, y)
            tag = f"page{i}"
            c.create_rectangle(x - 1, y - 1, x + tw + 1, y + th + 1, fill=p["field"], outline=p["field_border"],
                               tags=(tag,))
            c.create_image(x + tw / 2, y + th / 2, image=self.pv_photos.get(i, ""), tags=(tag, f"img{i}"))
            c.create_text(x + tw / 2, y + th + 4, text=page.label if len(page.label) < 18 else f"{i + 1}",
                          anchor="n", fill=p["muted"], font=("Segoe UI", 8), tags=(tag,))
            c.tag_bind(tag, "<Button-1>", lambda e, n=i: self._open_viewer(n))
            self._draw_crop_mark(i)
        rows = (len(self.pv_pages) + cols - 1) // cols
        c.configure(scrollregion=(0, 0, c.winfo_width(), gap + rows * (th + cap + gap)))

    def _current_comic(self):
        if self.pv_items and self.pv_combo.current() >= 0:
            return self.tree.set(self.pv_items[self.pv_combo.current()], "input")
        return None

    def _draw_crop_mark(self, i):
        """✂ on a page with a crop; on the original pages, the crop box too."""
        c, p = self.pv_canvas, self.theme.p
        c.delete(f"mark{i}")
        path = self._current_comic()
        if not path or i not in self.pv_tiles or i >= len(self.pv_pages):
            return
        rect = self._crops_of(path).get(self.pv_pages[i].source_id)
        if not rect:
            return
        x, y = self.pv_tiles[i]
        tags = (f"mark{i}", f"page{i}")
        photo = self.pv_photos.get(i)
        if self.pv_whole and photo:
            pw, ph = photo.width(), photo.height()
            ix, iy = x + (self.THUMB_W - pw) / 2, y + (self.THUMB_H - ph) / 2
            c.create_rectangle(ix + rect[0] * pw, iy + rect[1] * ph, ix + rect[2] * pw, iy + rect[3] * ph,
                               outline=p["select"], width=2, tags=tags)
        c.create_text(x + self.THUMB_W - 3, y + 2, text="✂", anchor="ne", fill=p["select"],
                      font=("Segoe UI Symbol", 12, "bold"), tags=tags)

    def _open_viewer(self, index):
        """A window with one page, as big as the window, where its crop box is drawn.
        Arrow keys for the next and previous pages."""
        v = self.viewer
        if not (v and v.winfo_exists()):
            v = self.viewer = tk.Toplevel(self)
            v.geometry("780x1000")
            v.minsize(560, 480)
            v.configure(background=self.theme.p["bg"])
            bar = ttk.Frame(v, style="Backdrop.TFrame", padding=(10, 8, 10, 4))
            bar.pack(fill="x")
            ttk.Button(bar, text="◀", width=3, command=lambda: self._show_page(v.index - 1)).pack(side="left")
            ttk.Button(bar, text="▶", width=3, command=lambda: self._show_page(v.index + 1)).pack(side="left",
                                                                                              padx=(4, 14))
            v.crop_tools = ttk.Frame(bar, style="Backdrop.TFrame")
            ttk.Button(v.crop_tools, text="Left half", command=lambda: self._apply_viewer_crop([0, 0, 0.5, 1])).pack(
                side="left")
            ttk.Button(v.crop_tools, text="Right half", command=lambda: self._apply_viewer_crop([0.5, 0, 1, 1])).pack(
                side="left", padx=4)
            ttk.Button(v.crop_tools, text="Remove crop", command=lambda: self._apply_viewer_crop(None)).pack(
                side="left", padx=(10, 0))
            v.edit_btn = ttk.Button(bar, text="Edit the crop of this page", style="Accent.TButton",
                                    command=self._edit_source_crop)
            v.hint = ttk.Label(v, style="Backdrop.TLabel", padding=(12, 0, 12, 6), wraplength=740)
            v.hint.pack(fill="x")
            v.canvas = tk.Canvas(v, highlightthickness=0, borderwidth=0, background=self.theme.p["bg"])
            v.canvas.pack(fill="both", expand=True)
            v.bind("<Left>", lambda e: self._show_page(v.index - 1))
            v.bind("<Right>", lambda e: self._show_page(v.index + 1))
            v.bind("<Delete>", lambda e: v.editable and self._apply_viewer_crop(None))
            v.bind("<Escape>", lambda e: v.destroy())
            v.canvas.bind("<Configure>", lambda e: self._show_page(v.index))
            v.canvas.bind("<ButtonPress-1>", self._crop_press)
            v.canvas.bind("<B1-Motion>", self._crop_drag)
            v.canvas.bind("<ButtonRelease-1>", self._crop_release)
            v.canvas.bind("<Motion>", self._crop_hover)
            v.index, v.rect, v.drag, v.editable, v.box = index, None, None, False, None
            set_title_bar_dark(v, self.theme.p["dark"])
        self.viewer.lift()
        self.viewer.focus_set()
        self._show_page(index)

    def _show_page(self, index):
        v = self.viewer
        if not self.pv_pages or not (v and v.winfo_exists()):
            return
        v.index = index = max(0, min(index, len(self.pv_pages) - 1))
        page, path = self.pv_pages[index], self._current_comic()
        v.title(f"{self.pv_var.get()} - {page.label} ({index + 1}/{len(self.pv_pages)})   ← →")
        # The crop box is drawn on the source page: the pages of the Original view.
        v.editable = bool(path) and self.pv_whole and page.source_id is not None
        v.rect = self._crops_of(path).get(page.source_id) if v.editable else None
        v.drag = None
        if v.editable:
            v.edit_btn.pack_forget()
            v.crop_tools.pack(side="left")
            exe = self._exe()
            note = "" if exe and self._crops_supported(exe) else (
                "  The converter in use doesn't know page crops: they are kept, but ignored until you use the "
                "converter bundled with the app.")
            v.hint.configure(text="Drag on the page to draw the crop box: the page will be exactly this rectangle, "
                                  "as one page, never split in two. Drag inside the box to move it, its edges to "
                                  "resize it. Delete removes it." + note)
        else:
            v.crop_tools.pack_forget()
            if page.source_id is not None and path:
                v.edit_btn.pack(side="left")
            v.hint.configure(text="This is the page as converted. Crops are drawn on the original page: "
                                  "Edit the crop of this page." if page.source_id is not None else "")
        c = v.canvas
        w, h = max(c.winfo_width(), 100), max(c.winfo_height(), 100)
        c.delete("all")
        try:
            png, _ = preview.thumbnail(page.load(), w - 24, h - 24)
            v.photo = tk.PhotoImage(master=self, data=png)
            pw, ph = v.photo.width(), v.photo.height()
            v.box = ((w - pw) / 2, (h - ph) / 2, pw, ph)
            c.create_image(w / 2, h / 2, image=v.photo)
        except Exception as e:
            v.box = None
            c.create_text(w / 2, h / 2, text=f"Can't show this page: {e}", fill=self.theme.p["text"])
        self._draw_viewer_crop()

    def _draw_viewer_crop(self):
        """The crop box on the page, the rest of the page shaded."""
        v, p = self.viewer, self.theme.p
        c = v.canvas
        c.delete("crop")
        if not v.box or not v.rect:
            return
        ox, oy, pw, ph = v.box
        x0, y0, x1, y1 = ox + v.rect[0] * pw, oy + v.rect[1] * ph, ox + v.rect[2] * pw, oy + v.rect[3] * ph
        for box in ((ox, oy, ox + pw, y0), (ox, y1, ox + pw, oy + ph), (ox, y0, x0, y1), (x1, y0, ox + pw, y1)):
            if box[2] > box[0] and box[3] > box[1]:
                c.create_rectangle(*box, fill="black", stipple="gray50", outline="", tags="crop")
        c.create_rectangle(x0, y0, x1, y1, outline=p["select"], width=2, tags="crop")
        for hx, hy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
            c.create_rectangle(hx - 4, hy - 4, hx + 4, hy + 4, fill=p["select"], outline="white", tags="crop")

    def _crop_frac(self, e):
        ox, oy, pw, ph = self.viewer.box
        return min(max((e.x - ox) / pw, 0.0), 1.0), min(max((e.y - oy) / ph, 0.0), 1.0)

    def _crop_edges(self, e):
        """The edges of the crop box under the mouse: a set of "l", "t", "r", "b"."""
        v = self.viewer
        if not v.rect or not v.box:
            return set()
        ox, oy, pw, ph = v.box
        x0, y0, x1, y1 = ox + v.rect[0] * pw, oy + v.rect[1] * ph, ox + v.rect[2] * pw, oy + v.rect[3] * ph
        near, edges = 7, set()
        if y0 - near <= e.y <= y1 + near:
            if abs(e.x - x0) <= near:
                edges.add("l")
            elif abs(e.x - x1) <= near:
                edges.add("r")
        if x0 - near <= e.x <= x1 + near:
            if abs(e.y - y0) <= near:
                edges.add("t")
            elif abs(e.y - y1) <= near:
                edges.add("b")
        return edges

    def _crop_hover(self, e):
        v = self.viewer
        if not v.editable or not v.box or v.drag:
            return
        edges = self._crop_edges(e)
        cursors = {frozenset("l"): "sb_h_double_arrow", frozenset("r"): "sb_h_double_arrow",
                   frozenset("t"): "sb_v_double_arrow", frozenset("b"): "sb_v_double_arrow",
                   frozenset("lt"): "size_nw_se", frozenset("rb"): "size_nw_se",
                   frozenset("rt"): "size_ne_sw", frozenset("lb"): "size_ne_sw"}
        fx, fy = self._crop_frac(e)
        inside = v.rect and v.rect[0] < fx < v.rect[2] and v.rect[1] < fy < v.rect[3]
        v.canvas.configure(cursor=cursors.get(frozenset(edges)) or ("fleur" if inside else "crosshair"))

    def _crop_press(self, e):
        v = self.viewer
        if not v.editable or not v.box:
            return
        fx, fy = self._crop_frac(e)
        edges = self._crop_edges(e)
        if edges:
            v.drag = ("resize", edges, list(v.rect))
        elif v.rect and v.rect[0] < fx < v.rect[2] and v.rect[1] < fy < v.rect[3]:
            v.drag = ("move", (fx, fy), list(v.rect))
        else:
            v.drag = ("new", (fx, fy), v.rect)

    def _crop_drag(self, e):
        v = self.viewer
        if not v.drag:
            return
        fx, fy = self._crop_frac(e)
        mode, data, start = v.drag
        if mode == "new":
            sx, sy = data
            v.rect = [min(sx, fx), min(sy, fy), max(sx, fx), max(sy, fy)]
        elif mode == "move":
            dx, dy = fx - data[0], fy - data[1]
            w, h = start[2] - start[0], start[3] - start[1]
            x0, y0 = min(max(start[0] + dx, 0.0), 1.0 - w), min(max(start[1] + dy, 0.0), 1.0 - h)
            v.rect = [x0, y0, x0 + w, y0 + h]
        else:
            r = list(start)
            if "l" in data:
                r[0] = min(fx, r[2] - 0.02)
            if "r" in data:
                r[2] = max(fx, r[0] + 0.02)
            if "t" in data:
                r[1] = min(fy, r[3] - 0.02)
            if "b" in data:
                r[3] = max(fy, r[1] + 0.02)
            v.rect = r
        self._draw_viewer_crop()

    def _crop_release(self, e):
        v = self.viewer
        if not v.drag:
            return
        mode, _, start = v.drag
        v.drag = None
        if v.rect and v.rect[2] - v.rect[0] >= 0.02 and v.rect[3] - v.rect[1] >= 0.02:
            self._apply_viewer_crop(v.rect)
        else:  # a click without dragging: keeps the crop there was
            v.rect = start if mode == "new" else v.rect
            self._draw_viewer_crop()

    def _apply_viewer_crop(self, rect):
        """Saves the crop drawn in the viewer (None removes it)."""
        v, path = self.viewer, self._current_comic()
        if not (v and v.editable and path):
            return
        page = self.pv_pages[v.index]
        self._set_crop(path, page.source_id, rect)
        v.rect = self._crops_of(path).get(page.source_id)
        self._draw_viewer_crop()
        what = "removed" if rect is None else "saved: used by Convert and the Converted preview"
        v.hint.configure(text=f"Crop of {page.label} {what}.  Drag to draw another, Delete removes it.")

    def _edit_source_crop(self):
        """From a converted page, opens its source page in the Original view, to draw its crop."""
        v = self.viewer
        if not (v and v.winfo_exists()) or not self.pv_pages:
            return
        self.pending_viewer = self.pv_pages[v.index].source_id
        self._set_preview_mode("original")

    # ---------- widget helpers ----------

    def _tab(self, nb):
        f = ttk.Frame(nb, padding=12)
        # label | widget | ? | gap, for the left and the right column
        f.columnconfigure(3, weight=1)
        f.columnconfigure(7, weight=1)
        f._row = [0, 0]  # next free row for the left and right columns
        return f

    def _help_icon(self, parent, key=None, text=None):
        """A round ? that explains an option: on hover, and on click."""
        title, body = HELP.get(key, (None, text)) if key else (None, text)
        p, s = self.theme.p, 18
        c = tk.Canvas(parent, width=s, height=s, highlightthickness=0, borderwidth=0, background=p["card"],
                      cursor="question_arrow")
        c.create_oval(1, 1, s - 2, s - 2, fill=p["select"], outline=p["accent_border"], tags="dot")
        c.create_text(s / 2 - 0.5, s / 2 - 0.5, text="?", fill="white", font=("Segoe UI", 8, "bold"))
        tip = Tooltip(c, f"{title}\n{body}" if title else body)
        c.bind("<Button-1>", lambda e: tip.hide(e) if tip.tip else tip.show(e))
        self.help_icons.append(c)
        return c

    def _place(self, tab, side, label, widget, tip=None, label_widget=True, key=None):
        row = tab._row[side]
        col = side * 4
        tip = HELP[key][1] if key in HELP else tip
        if label_widget:
            lbl = ttk.Label(tab, text=label)
            lbl.grid(row=row, column=col, sticky="w", pady=3, padx=(0, 8))
            if tip:
                Tooltip(lbl, tip)
        widget.grid(row=row, column=col + 1, sticky="w", pady=3)
        if key in HELP or tip:
            self._help_icon(tab, key, tip).grid(row=row, column=col + 2, sticky="w", padx=(6, 0))
        if side == 0:
            ttk.Frame(tab, width=24).grid(row=row, column=3)
        tab._row[side] += 1
        return widget

    def _check(self, tab, side, key, label, tip=None, command=None):
        v = self.vars[key] = tk.BooleanVar(value=DEFAULTS.get(key, False))
        cb = ttk.Checkbutton(tab, text=label, variable=v, command=command)
        return self._place(tab, side, label, cb, tip, label_widget=False, key=key)

    def _spin(self, tab, side, key, label, lo, hi, inc=1, tip=None, is_float=False):
        v = self.vars[key] = (tk.DoubleVar if is_float else tk.IntVar)(value=DEFAULTS[key])
        sp = ttk.Spinbox(tab, from_=lo, to=hi, increment=inc, textvariable=v, width=8)
        return self._place(tab, side, label, sp, tip, key=key)

    def _scale(self, tab, side, key, label, lo, hi, tip=None):
        v = self.vars[key] = tk.IntVar(value=DEFAULTS[key])
        f = ttk.Frame(tab)
        ttk.Scale(f, from_=lo, to=hi, variable=v, length=180,
                  command=lambda x: v.set(round(float(x)))).pack(side="left")
        ttk.Spinbox(f, from_=lo, to=hi, textvariable=v, width=5).pack(side="left", padx=(6, 0))
        return self._place(tab, side, label, f, tip, key=key)

    def _choice(self, tab, side, key, label, tip=None, command=None, width=30):
        options = CHOICES[key]
        self.vars[key] = tk.StringVar()
        cb = ttk.Combobox(tab, state="readonly", width=width, values=[l for _, l in options],
                          textvariable=self.vars[key])
        self.comboboxes.append(cb)
        self._set_choice(key, DEFAULTS.get(key, GUI_DEFAULTS.get(key)))
        if command:
            cb.bind("<<ComboboxSelected>>", lambda e: command())
        return self._place(tab, side, label, cb, tip, key=key)

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
        return self._place(tab, side, label, f, tip, key=key)

    def _entry(self, tab, side, key, label, tip=None, width=34, browse=None):
        default = DEFAULTS.get(key, GUI_DEFAULTS.get(key, ""))
        v = self.vars[key] = tk.StringVar(value=default)
        f = ttk.Frame(tab)
        ttk.Entry(f, textvariable=v, width=width).pack(side="left")
        if browse:
            ttk.Button(f, text="…", width=3, command=browse).pack(side="left", padx=(4, 0))
        return self._place(tab, side, label, f, tip, key=key)

    # ---------- tabs ----------

    def _tab_general(self, nb):
        t = self._tab(nb)
        self.vars["profile"] = tk.StringVar()
        self.profile_cb = ttk.Combobox(t, state="readonly", width=46, values=PROFILE_LABELS,
                                       textvariable=self.vars["profile"], height=20)
        self.comboboxes.append(self.profile_cb)
        self.profile_cb.bind("<<ComboboxSelected>>", lambda e: self._on_profile_change())
        self._place(t, 0, "Device profile:", self.profile_cb, key="profile")
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
        self._place(t, 0, "Quality presets:", presets, key="presets")
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
                self.tree.insert("", "end", values=(p, "", "Pending", ""))
                existing.add(p)
        self._restripe()
        self._update_view()
        self._refresh_crop_marks()

    def _restripe(self):
        """Alternate the colors of the rows of the queue."""
        for n, i in enumerate(self.tree.get_children()):
            self.tree.item(i, tags=("odd" if n % 2 else "even",))

    def _add_files(self):
        self._add_inputs(filedialog.askopenfilenames(parent=self, title="Add comics", filetypes=INPUT_TYPES))

    def _add_folder(self):
        dirs = ask_folders(self, "Add folders (Ctrl or Shift + click to select several)", self.last_dir)
        if dirs:
            self.last_dir = os.path.dirname(os.path.normpath(dirs[0]))
            self._add_folders(dirs)

    def _add_folders(self, dirs):
        """Queues folders: each one as a comic, or the comic archives they contain (asked once for all)."""
        archives = {}
        for d in dirs:
            found = [str(e) for e in Path(d).iterdir() if e.is_file() and e.suffix.lower() in ARCHIVE_EXTS]
            if found:
                archives[d] = found
        if archives:
            n = sum(map(len, archives.values()))
            where = (f"{Path(next(iter(archives))).name} contains" if len(archives) == 1
                     else f"{len(archives)} of the folders contain")
            if messagebox.askyesno(APP_NAME, f"{where} {n} comic archive(s).\n\n"
                                             "Yes: add each archive separately\n"
                                             "No: convert each folder as one comic"):
                self._add_inputs([d for d in dirs if d not in archives] + [a for f in archives.values() for a in f])
                return
        self._add_inputs(dirs)

    def _on_drop(self, paths):
        if self.worker:
            self._log("Wait for the conversion to finish before adding comics.\n", "err")
            return
        skipped, dirs, files = [], [], []
        for p in paths:
            if os.path.isdir(p):
                dirs.append(p)
            elif Path(p).suffix.lower() in ARCHIVE_EXTS:
                files.append(p)
            else:
                skipped.append(Path(p).name)
        if dirs:
            self._add_folders(dirs)
        self._add_inputs(files)
        if skipped:
            self._log("Not a comic, skipped: " + ", ".join(skipped) + "\n", "err")

    def _remove_selected(self):
        if self.worker:
            return
        for i in self.tree.selection():
            self.tree.delete(i)
        self._restripe()
        self._update_view()

    def _clear_queue(self):
        if not self.worker:
            self.tree.delete(*self.tree.get_children())
            self._update_view()

    def _clear_finished(self):
        """Removes the comics converted: what's left is what still needs work."""
        if not self.worker:
            self.tree.delete(*[i for i in self.tree.get_children() if self.tree.set(i, "status").startswith("Done")])
            self._restripe()
            self._update_view()

    def _open_output(self):
        """Opens the output folder, or the folder of the EPUB of the selected comic."""
        folder = self.vars["output_dir"].get().strip()
        if not folder:
            sel = self.tree.selection() or self.tree.get_children()
            if sel:
                out = self.tree.set(sel[0], "output")
                folder = os.path.dirname(out) if out else os.path.dirname(os.path.normpath(self.tree.set(sel[0], "input")))
        if folder and os.path.isdir(folder) and os.name == "nt":
            os.startfile(folder)

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
        crops = self._crops_of(item)
        if crops:
            exe = self._exe()
            if exe and self._crops_supported(exe):
                args.append(f"-pagecrops={self._crops_file({str(k): v for k, v in crops.items()})}")
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

    # ---------- page crops ----------

    @staticmethod
    def _comic_key(path):
        return os.path.normcase(os.path.abspath(path))

    def _load_crops(self):
        try:
            data = json.loads(CROPS_FILE.read_text(encoding="utf-8"))
            return {k: {int(i): [float(x) for x in r] for i, r in v.items()} for k, v in data.items()}
        except (OSError, ValueError, TypeError, AttributeError):
            return {}

    def _save_crops(self):
        data = {k: {str(i): r for i, r in sorted(v.items())} for k, v in self.page_crops.items() if v}
        try:
            CROPS_FILE.write_text(json.dumps(data, indent=1), encoding="utf-8")
        except OSError:
            pass

    def _crops_of(self, path):
        return self.page_crops.get(self._comic_key(path), {})

    def _set_crop(self, path, page, rect):
        """Saves the crop of a page of a comic, or removes it (rect None)."""
        crops = self.page_crops.setdefault(self._comic_key(path), {})
        if rect:
            crops[page] = [round(min(max(v, 0.0), 1.0), 5) for v in rect]
        else:
            crops.pop(page, None)
        self._save_crops()
        self._refresh_crop_marks()
        self._on_option_change()

    def _crops_supported(self, exe):
        """Tells if the converter knows -pagecrops: the bundled one does, a stock one doesn't."""
        if exe not in self.crop_support:
            try:
                out = subprocess.run([exe, "-help", "-ignore-config"], capture_output=True, text=True,
                                     stdin=subprocess.DEVNULL, timeout=20, **popen_kwargs())
                self.crop_support[exe] = "-pagecrops" in out.stdout + out.stderr
            except (OSError, subprocess.TimeoutExpired):
                self.crop_support[exe] = False
        return self.crop_support[exe]

    def _crops_file(self, crops):
        """The crops in a JSON file named after its content: another crop gives another command line."""
        text = json.dumps(crops, sort_keys=True)
        path = os.path.join(self.pv_tmp, f"crops-{hashlib.sha1(text.encode()).hexdigest()[:12]}.json")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        return path

    def _refresh_crop_marks(self):
        """The number of cropped pages in the queue, and the marks on the thumbnails."""
        for i in self.tree.get_children():
            n = len(self._crops_of(self.tree.set(i, "input")))
            self.tree.set(i, "crops", f"✂ {n}" if n else "")
        for i in range(len(self.pv_pages)):
            self._draw_crop_mark(i)

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
            self.tree.set(i, "output", "")
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
                self._handle_line(line, outputs, item)
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

    def _handle_line(self, line, outputs, item=None):
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
                        self.events.put(("output", item, out))
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
        # A time budget per pass: the thumbnails of a long comic arrive faster than Tk shows them.
        deadline = time.perf_counter() + 0.025
        try:
            while time.perf_counter() < deadline:
                ev = self.events.get_nowait()
                kind = ev[0]
                if kind == "log":
                    self._log(ev[1], ev[2])
                elif kind == "item":
                    if self.tree.exists(ev[1]):
                        self.tree.set(ev[1], "status", ev[2])
                elif kind == "job":
                    self.job = (ev[1], ev[2])
                    self.progress["value"] = (ev[1] - 1) / ev[2] * 100
                    self.status.set(f"Comic {ev[1]}/{ev[2]}: starting…")
                elif kind == "progress":
                    self._on_progress(ev[1])
                elif kind == "finished":
                    self._on_finished(*ev[1:])
                elif kind == "drop":
                    self._on_drop(ev[1])
                elif kind == "pv":
                    self._on_preview_event(*ev[1:])
                elif kind == "output":
                    if ev[1] and self.tree.exists(ev[1]):
                        self.tree.set(ev[1], "output", ev[2])
                elif kind == "installed":
                    self.status.set("Installed" if ev[1] else "Install failed")
                    if ev[1]:
                        self._exe()
                        self._log(f"Installed: {self.vars['exe'].get()}\n", "ok")
        except queue.Empty:
            pass
        self.after(80 if self.events.empty() else 1, self._poll_events)

    def _on_progress(self, data):
        p = data.get("epubprogress", {})
        st = data.get("steps", {})
        cur, tot = p.get("current", 0), max(p.get("total", 1), 1)
        step, steps = st.get("current", 1), max(st.get("total", 1), 1)
        n, total = getattr(self, "job", (1, 1))
        # The bar shows the whole queue; each comic is spread over its steps (processing, writing).
        done_in_comic = ((step - 1) + cur / tot) / steps
        self.progress["value"] = ((n - 1) + done_in_comic) / total * 100
        self.status.set(f"Comic {n}/{total} ({round(self.progress['value'])}% of the queue): "
                        f"{data.get('description', '')} {cur}/{tot}")

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
        self.tutorial_seen = bool(data.get("tutorial_seen")) if isinstance(data, dict) else False
        self._apply_settings({**DEFAULTS, **PREFERRED, **GUI_DEFAULTS, **data})

    def _save_settings(self):
        try:
            data = {**self._collect_settings(), "settings_version": SETTINGS_VERSION,
                    "tutorial_seen": self.tutorial_seen}
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
        self._clear_preview()
        self._save_settings()
        self.destroy()
        shutil.rmtree(self.pv_tmp, ignore_errors=True)


if __name__ == "__main__":
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    App().mainloop()
