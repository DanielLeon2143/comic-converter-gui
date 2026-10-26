"""Skeuomorphic light and dark themes for the ttk widgets of the GUI.

The look (bevels, gloss, inset fields, shadows) comes from images drawn here pixel by pixel and
used as ttk image elements. ttk tiles the middle of an image element to fit the widget, so the
gradients are kept in the borders of the images and their middle is a flat color.
Switching theme redraws the images in place: every widget using them follows.
"""

import base64
import math
import random
import struct
import zlib
import tkinter as tk
from tkinter import ttk

LIGHT = {
    "dark": False,
    "bg": "#cdd1d7",
    "text": "#1f2328", "muted": "#646c76",
    "card": "#eef0f3", "card_top": "#f7f8fa", "card_border": "#9ca2aa", "card_hl": ("#ffffff", 0.95),
    "card_shadow": ("#000000", 0.20),
    "btn": ("#ffffff", "#eceef1", "#d0d4da"), "btn_hover": ("#ffffff", "#f4f6f9", "#dde1e6"),
    "btn_pressed": ("#bfc5cc", "#ccd0d6", "#d8dbe0"), "btn_dis": ("#f4f5f7", "#eceef0", "#e3e5e8"),
    "btn_border": "#878e97", "btn_border_dis": "#b8bdc4", "btn_hl": ("#ffffff", 0.95), "btn_shadow": ("#000000", 0.16),
    # gloss top, gloss bottom, body, bottom glow
    "accent": ("#cfe6ff", "#8cc2f7", "#3a8bef", "#62adff"),
    "accent_hover": ("#dcedff", "#9dcdfb", "#4c98f5", "#74b8ff"),
    "accent_pressed": ("#8fb8e6", "#5f9ae0", "#2a72d3", "#3f8be8"),
    "accent_dis": ("#e6eef7", "#ccdcee", "#a9c3e2", "#b8d0ec"),
    "accent_border": "#1d5cb3", "accent_text": "#ffffff",
    "field": "#ffffff", "field_dis": "#f0f1f3", "field_border": "#959ca6",
    "field_shadow": ("#000000", 0.18), "field_hl": ("#ffffff", 0.85), "glow": ("#3d8cff", 0.55),
    "tab": ("#e2e5e9", "#d6dadf", "#c6cbd2"), "tab_hover": ("#eef0f3", "#e3e6ea", "#d5d9de"),
    "lcd": "#d3ddbf", "lcd_top": "#bfcca6", "lcd_text": "#25321a", "lcd_border": "#7f8b6e",
    "trough": "#c3c8cf",
    "header": ("#f4f5f7", "#c3c7cd"), "header_border": "#868c95", "streak": 7,
    "title": "#2f343a", "emboss": "#ffffff", "emboss_dy": 1, "subtitle": "#5b626b",
    "row_odd": "#f1f4f8", "row_even": "#ffffff", "select": "#3a8bef", "select_text": "#ffffff",
    "log_err": "#c0392b", "log_ok": "#1e7b45", "log_cmd": "#2160a8",
    "tip_bg": "#fffbe3", "tip_fg": "#1f2328", "tip_border": "#a8a27c",
    "switch_off": ("#b9bec5", "#dde0e5"), "knob": ("#ffffff", "#eceef1", "#cfd3d9"),
    "scroll_thumb": "#d7dade", "scroll_trough": "#e6e8eb",
}

DARK = {
    "dark": True,
    "bg": "#1b1d21",
    "text": "#e6e8eb", "muted": "#99a0a9",
    "card": "#2b2e33", "card_top": "#33363c", "card_border": "#101113", "card_hl": ("#ffffff", 0.09),
    "card_shadow": ("#000000", 0.55),
    "btn": ("#60656d", "#4a4e55", "#3a3d43"), "btn_hover": ("#6b7078", "#545860", "#43464d"),
    "btn_pressed": ("#2a2c30", "#323439", "#393c41"), "btn_dis": ("#3c3f44", "#36393e", "#313338"),
    "btn_border": "#121315", "btn_border_dis": "#222428", "btn_hl": ("#ffffff", 0.20), "btn_shadow": ("#000000", 0.45),
    "accent": ("#8cc0ff", "#4f92ec", "#1f64c8", "#2f7be0"),
    "accent_hover": ("#9fcbff", "#61a0f2", "#2a70d4", "#3b88ea"),
    "accent_pressed": ("#4a7fc6", "#2f68bf", "#174f9f", "#2262b8"),
    "accent_dis": ("#4d5866", "#424c59", "#36404c", "#3c4653"),
    "accent_border": "#0a2552", "accent_text": "#ffffff",
    "field": "#17181b", "field_dis": "#222428", "field_border": "#0b0c0d",
    "field_shadow": ("#000000", 0.60), "field_hl": ("#ffffff", 0.08), "glow": ("#4d9bff", 0.60),
    "tab": ("#3c3f45", "#33363b", "#2a2c31"), "tab_hover": ("#474a51", "#3d4046", "#33363b"),
    "lcd": "#132219", "lcd_top": "#0b150f", "lcd_text": "#86f0a4", "lcd_border": "#050806",
    "trough": "#141518",
    "header": ("#43474d", "#24262a"), "header_border": "#0b0c0d", "streak": 5,
    "title": "#dfe2e6", "emboss": "#000000", "emboss_dy": -1, "subtitle": "#9aa1aa",
    "row_odd": "#212327", "row_even": "#1a1b1e", "select": "#2a6fd6", "select_text": "#ffffff",
    "log_err": "#ff7b6b", "log_ok": "#6fdc93", "log_cmd": "#74b2ff",
    "tip_bg": "#2f3237", "tip_fg": "#e6e8eb", "tip_border": "#0e0f11",
    "switch_off": ("#16171a", "#2a2c30"), "knob": ("#7a7f87", "#5c6068", "#4a4e55"),
    "scroll_thumb": "#4a4e55", "scroll_trough": "#1f2125",
}


# ---------- drawing ----------

def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    t = min(max(t, 0.0), 1.0)
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def cov(d):
    """Coverage of a pixel at signed distance d from an edge (anti-aliasing)."""
    return min(max(0.5 - d, 0.0), 1.0)


class Bitmap:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [[0.0, 0.0, 0.0, 0.0] for _ in range(w * h)]

    def blend(self, x, y, color, a):
        if a <= 0.001:
            return
        p = self.px[y * self.w + x]
        da = p[3]
        oa = a + da * (1 - a)
        for i in range(3):
            p[i] = (color[i] * a + p[i] * da * (1 - a)) / oa
        p[3] = oa

    def png(self):
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)
            for p in self.px[y * self.w:(y + 1) * self.w]:
                raw += bytes((round(p[0]), round(p[1]), round(p[2]), round(p[3] * 255)))

        def chunk(t, d):
            return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))

        data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b""))
        return base64.b64encode(data).decode("ascii")


def rrect(bmp, box, r, fill=None, border=None, bw=1.0, top_hl=None, inner_shadow=None,
          under=None, glow=None):
    """Draws a rounded rectangle with its decorations, all anti-aliased.

    fill: color, or function of the y inside the shape giving a color.
    border: (color, alpha). top_hl: (color, alpha) 1px line inside the top border.
    inner_shadow: (color, alpha, depth) shadow inside, from the top (inset look).
    under: (color, alpha, dy, blur) copy of the shape drawn below it: drop shadow, or a light
           line under an inset field (engraved look).
    glow: (color, alpha, spread) halo around the shape (focus ring).
    """
    x0, y0, x1, y1 = box
    cx, cy, hx, hy = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    r = min(r, hx, hy)

    def sd(px, py):
        qx, qy = abs(px - cx) - (hx - r), abs(py - cy) - (hy - r)
        return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - r

    hl_row = int(y0 + bw)
    for y in range(bmp.h):
        py = y + 0.5
        for x in range(bmp.w):
            px = x + 0.5
            d = sd(px, py)
            if glow and d > 0:
                bmp.blend(x, y, rgb(glow[0]), glow[1] * max(0.0, 1 - d / glow[2]))
            if under:
                du = sd(px, py - under[2])
                a = cov(du) if under[3] <= 0 else min(max(0.5 - du / under[3], 0.0), 1.0)
                bmp.blend(x, y, rgb(under[0]), under[1] * a)
            c = cov(d)
            if c <= 0:
                continue
            if fill:
                bmp.blend(x, y, fill(py - y0) if callable(fill) else rgb(fill), c)
            inner = cov(d + bw)
            if inner_shadow and inner > 0:
                t = (py - y0 - bw) / inner_shadow[2]
                if t < 1:
                    bmp.blend(x, y, rgb(inner_shadow[0]), inner_shadow[1] * (1 - max(t, 0)) ** 1.5 * inner)
            if top_hl and y == hl_row and inner > 0:
                bmp.blend(x, y, rgb(top_hl[0]), top_hl[1] * inner)
            if border:
                bmp.blend(x, y, rgb(border[0]), border[1] * max(c - inner, 0))


def bands(colors, band, height):
    """Vertical gradient kept in the top and bottom bands, flat in between.

    colors: (top, middle, bottom), or (gloss top, gloss bottom, middle, bottom) for a glossy look.
    """
    if len(colors) == 3:
        top, mid, bot = map(rgb, colors)
        top2 = mid
    else:
        top, top2, mid, bot = map(rgb, colors)

    def f(y):
        if y < band:
            return mix(top, top2, y / band)
        if y > height - band:
            return mix(mid, bot, (y - (height - band)) / band)
        return mid

    return f


def polygon_cov(points, x, y, ss=4):
    """Coverage of the pixel (x, y) by a polygon, by supersampling."""
    n = 0
    for i in range(ss):
        for j in range(ss):
            px, py = x + (i + 0.5) / ss, y + (j + 0.5) / ss
            inside = False
            for k in range(len(points)):
                (ax, ay), (bx, by) = points[k], points[k - 1]
                if (ay > py) != (by > py) and px < (bx - ax) * (py - ay) / (by - ay) + ax:
                    inside = not inside
            n += inside
    return n / (ss * ss)


def seg_dist(px, py, a, b):
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


# ---------- the pieces ----------

class Pieces:
    """Draws all the images of a palette at a scale. Their geometry only depends on the scale."""

    # Size of the flat middle of the stretchable images. ttk fills a widget by repeating it:
    # a tiny one means thousands of copies for a big widget, and redraws of several seconds.
    CENTER = 64

    def __init__(self, p, s):
        self.p, self.s = p, s
        self.images = {}   # name -> PNG as base64
        self.borders = {}  # name -> ttk image border (left, top, right, bottom)
        self.sizes = {}

    def u(self, v):
        return max(1, round(v * self.s))

    def add(self, name, bmp, border=None):
        self.images[name] = bmp.png()
        self.sizes[name] = (bmp.w, bmp.h)
        if border:
            self.borders[name] = border

    def plate(self, name, r, pad, **kw):
        """A rounded plate of the smallest size that tiles: borders hold the corners and bands."""
        pl, pt, pr, pb = pad
        b = r + 2
        w, h = pl + pr + 2 * b + self.CENTER, pt + pb + 2 * b + self.CENTER
        bmp = Bitmap(w, h)
        if isinstance(kw.get("fill"), tuple):
            kw["fill"] = bands(kw["fill"], b, h - pt - pb)
        rrect(bmp, (pl, pt, w - pr, h - pb), r, **kw)
        self.add(name, bmp, (pl + b, pt + b, pr + b, pb + b))

    def build(self):
        p, u = self.p, self.u
        R = u(5)

        # Buttons: raised, beveled, with a soft shadow.
        bpad = (1, 0, 1, 2)
        for state in ("btn", "btn_hover", "btn_pressed", "btn_dis"):
            border = p["btn_border_dis"] if state == "btn_dis" else p["btn_border"]
            self.plate(state, R, bpad, fill=p[state], border=(border, 1),
                       top_hl=None if state in ("btn_pressed", "btn_dis") else p["btn_hl"],
                       inner_shadow=("#000000", 0.25, u(4)) if state == "btn_pressed" else None,
                       under=(p["btn_shadow"][0], p["btn_shadow"][1], 1, u(2)))
        for state in ("accent", "accent_hover", "accent_pressed", "accent_dis"):
            self.plate(state, R, bpad, fill=p[state], border=(p["accent_border"], 0.5 if state == "accent_dis" else 1),
                       top_hl=("#ffffff", 0.35) if state != "accent_pressed" else None,
                       under=(p["btn_shadow"][0], p["btn_shadow"][1], 1, u(2)))

        # Text fields: inset, with an inner shadow, a light line under them, and a glow on focus.
        g = u(3)
        fpad = (g, g, g, g)
        base = dict(border=(p["field_border"], 1), inner_shadow=(p["field_shadow"][0], p["field_shadow"][1], u(4)),
                    under=(p["field_hl"][0], p["field_hl"][1], 1, 0))
        self.plate("field", u(4), fpad, fill=p["field"], **base)
        self.plate("field_focus", u(4), fpad, fill=p["field"], glow=(p["glow"][0], p["glow"][1], g + 0.5), **base)
        self.plate("field_dis", u(4), fpad, fill=p["field_dis"], **base)
        self.plate("lcd", u(4), (0, 0, 0, 1), fill=(p["lcd_top"], p["lcd"], p["lcd"]), border=(p["lcd_border"], 1),
                   inner_shadow=("#000000", 0.35, u(5)), under=(p["field_hl"][0], p["field_hl"][1], 1, 0))

        # Cards: raised plates with a drop shadow.
        self.plate("card", u(8), (2, 1, 2, u(3)), fill=(p["card_top"], p["card"], p["card"]),
                   border=(p["card_border"], 1), top_hl=p["card_hl"],
                   under=(p["card_shadow"][0], p["card_shadow"][1], u(1), u(3)))

        # Notebook tabs: rounded on top, open at the bottom to join the card.
        tr = u(6)
        for state in ("tab", "tab_hover", "tab_sel"):
            w, h = 2 * tr + 4 + self.CENTER, tr + 4 + self.CENTER // 2
            bmp = Bitmap(w, h)
            if state == "tab_sel":
                fill = bands((p["card_top"], p["card_top"], p["card_top"]), tr + 2, h)
                hl = p["card_hl"]
            else:
                fill = bands(p[state], tr + 2, h + tr)
                hl = p["btn_hl"] if not p["dark"] else ("#ffffff", 0.10)
            rrect(bmp, (1, 0, w - 1, h + tr + 2), tr, fill=fill, border=(p["card_border"], 1), top_hl=hl)
            self.add(state, bmp, (tr + 2, tr + 2, tr + 2, 2))

        # Treeview heading: square gradient cell with a separator.
        hb = u(6)
        w, h = 3 + self.CENTER, 2 * hb + self.CENTER // 2
        bmp = Bitmap(w, h)
        f = bands(p["btn"], hb, h)
        for y in range(h):
            for x in range(w):
                bmp.blend(x, y, f(y + 0.5), 1)
        for x in range(w):
            bmp.blend(x, h - 1, rgb(p["field_border"]), 1)
            bmp.blend(x, 0, rgb(p["btn_hl"][0]), p["btn_hl"][1] * 0.6)
        for y in range(2, h - 2):
            bmp.blend(w - 1, y, rgb(p["field_border"]), 0.5)
        self.add("heading", bmp, (1, hb, 2, hb))

        # Checkboxes: inset box, glossy blue with a check mark when on.
        cs = u(16)
        gap = u(6)
        for state in ("check_off", "check_on", "check_off_dis", "check_on_dis"):
            bmp = Bitmap(cs + 2 + gap, cs + 2)
            box = (1, 0, cs + 1, cs)
            on, dis = "_on" in state, state.endswith("_dis")
            if on:
                rrect(bmp, box, u(4), fill=bands(p["accent_dis" if dis else "accent"], cs // 2, cs),
                      border=(p["accent_border"], 0.6 if dis else 1), top_hl=("#ffffff", 0.35),
                      under=(p["field_hl"][0], p["field_hl"][1], 1, 0))
                pts = [(0.25, 0.52), (0.43, 0.70), (0.76, 0.30)]
                pts = [(1 + cs * x, cs * y) for x, y in pts]
                th = max(1.6, 2.1 * self.s)
                for y in range(bmp.h):
                    for x in range(bmp.w):
                        d = min(seg_dist(x + 0.5, y + 0.5, pts[0], pts[1]),
                                seg_dist(x + 0.5, y + 0.5, pts[1], pts[2])) - th / 2
                        sh = min(seg_dist(x + 0.5, y - 0.5, pts[0], pts[1]),
                                 seg_dist(x + 0.5, y - 0.5, pts[1], pts[2])) - th / 2
                        bmp.blend(x, y, (0, 0, 0), 0.25 * cov(sh))
                        bmp.blend(x, y, (255, 255, 255), (0.7 if dis else 1) * cov(d))
            else:
                rrect(bmp, box, u(4), fill=p["field_dis" if dis else "field"], border=(p["field_border"], 1),
                      inner_shadow=(p["field_shadow"][0], p["field_shadow"][1], u(5)),
                      under=(p["field_hl"][0], p["field_hl"][1], 1, 0))
            self.add(state, bmp)

        # Arrows of the spinboxes and the combobox.
        aw, ah = u(14), u(9)
        for name, up in (("arrow_up", True), ("arrow_down", False)):
            bmp = Bitmap(aw, ah)
            cx, tw, th = aw / 2, u(7), u(4)
            top, bot = (ah - th) / 2 + (0.5 if up else 0), (ah + th) / 2
            pts = [(cx - tw / 2, bot), (cx + tw / 2, bot), (cx, top)] if up else \
                [(cx - tw / 2, top), (cx + tw / 2, top), (cx, bot)]
            for y in range(ah):
                for x in range(aw):
                    bmp.blend(x, y, rgb(p["text"]), 0.8 * polygon_cov(pts, x, y))
            self.add(name, bmp)
        cw, ch = u(18), u(16)
        bmp = Bitmap(cw, ch)
        cx, tw, th = cw / 2 + 1, u(7), u(4)
        tris = [[(cx - tw / 2, ch / 2 - 1.5), (cx + tw / 2, ch / 2 - 1.5), (cx, ch / 2 - 1.5 - th)],
                [(cx - tw / 2, ch / 2 + 1.5), (cx + tw / 2, ch / 2 + 1.5), (cx, ch / 2 + 1.5 + th)]]
        for y in range(ch):
            for x in range(cw):
                if x == 0 and 2 < y < ch - 2:
                    bmp.blend(x, y, rgb(p["btn_border"]), 0.45)
                for t in tris:
                    bmp.blend(x, y, rgb(p["text"]), 0.8 * polygon_cov(t, x, y))
        self.add("chevron", bmp)

        # Progress bar: inset trough, glossy pill.
        th = u(14)
        pr = u(5)
        bmp = Bitmap(2 * pr + 4 + self.CENTER, th + 1)
        rrect(bmp, (0, 0, bmp.w, th), pr, fill=p["trough"], border=(p["field_border"], 1),
              inner_shadow=("#000000", 0.35 if p["dark"] else 0.20, u(5)), under=(p["field_hl"][0], p["field_hl"][1], 1, 0))
        self.add("ptrough", bmp, (pr + 2, th // 2, pr + 2, th - th // 2))
        ph = th - 4
        bmp = Bitmap(2 * pr + 2 + self.CENTER, ph)
        rrect(bmp, (0, 0, bmp.w, ph), pr - 1, fill=bands(p["accent"], ph // 2, ph), border=(p["accent_border"], 0.7),
              top_hl=("#ffffff", 0.4))
        self.add("pbar", bmp, (pr + 1, ph // 2, pr + 1, ph - ph // 2 - 1))

        # Slider: thin inset groove and a glossy round knob.
        ks = u(18)
        gh = u(6)
        gw = 2 * u(3) + 4 + self.CENTER
        bmp = Bitmap(gw, ks + 3)
        gy = (ks - gh) / 2
        rrect(bmp, (0, gy, gw, gy + gh), u(3), fill=p["trough"], border=(p["field_border"], 1),
              inner_shadow=("#000000", 0.3, u(3)), under=(p["field_hl"][0], p["field_hl"][1], 1, 0))
        self.add("strough", bmp, (u(3) + 2, (ks + 3) // 2, u(3) + 2, (ks + 3) - (ks + 3) // 2 - 1))
        for name, colors in (("knob", p["btn"]), ("knob_active", p["btn_hover"]), ("knob_pressed", p["btn_pressed"])):
            bmp = Bitmap(ks + 2, ks + 3)
            rrect(bmp, (1, 0, ks + 1, ks), ks / 2, fill=bands(colors, ks / 2, ks), border=(p["btn_border"], 1),
                  top_hl=p["btn_hl"], under=(p["btn_shadow"][0], p["btn_shadow"][1] * 1.3, 1, u(2)))
            self.add(name, bmp)

        # Dark mode switch: pill track, glossy knob.
        sw, sh = u(50), u(26)
        for name, on in (("switch_off", False), ("switch_on", True)):
            bmp = Bitmap(sw + 2, sh + 3)
            track = (1, 0, sw + 1, sh)
            if on:
                rrect(bmp, track, sh / 2, fill=bands(p["accent"], sh / 2, sh), border=(p["accent_border"], 1),
                      inner_shadow=("#000000", 0.30, u(6)), under=(p["field_hl"][0], p["field_hl"][1], 1, 0))
            else:
                rrect(bmp, track, sh / 2, fill=bands((p["switch_off"][0], p["switch_off"][1], p["switch_off"][1]),
                                                     sh / 2, sh),
                      border=(p["field_border"], 1), inner_shadow=("#000000", 0.30, u(6)),
                      under=(p["field_hl"][0], p["field_hl"][1], 1, 0))
            k = sh - 4
            kx = sw + 1 - 2 - k if on else 3
            rrect(bmp, (kx, 2, kx + k, 2 + k), k / 2, fill=bands(p["knob"], k / 2, k), border=(p["btn_border"], 1),
                  top_hl=p["btn_hl"], under=("#000000", 0.35, 1, u(2)))
            self.add(name, bmp)

        # Header: brushed metal, tiled horizontally.
        hh = u(64)
        tw = 256
        bmp = Bitmap(tw, hh)
        rnd = random.Random(7)
        top, bot = rgb(p["header"][0]), rgb(p["header"][1])
        for y in range(hh):
            base = mix(top, bot, y / (hh - 1))
            noise = [rnd.uniform(-1, 1) for _ in range(tw)]
            # Smear the noise along the row: long thin streaks.
            streak = [sum(noise[(x + k) % tw] for k in range(-12, 13)) / 5 for x in range(tw)]
            for x in range(tw):
                v = streak[x] * p["streak"] / 2 + rnd.uniform(-1, 1) * 1.5
                bmp.blend(x, y, tuple(min(255, max(0, c + v)) for c in base), 1)
        for x in range(tw):
            bmp.blend(x, 0, (255, 255, 255), 0.5 if not p["dark"] else 0.12)
            bmp.blend(x, hh - 1, rgb(p["header_border"]), 1)
        self.add("header", bmp)
        return self


# ---------- the ttk theme ----------

def layout(*nodes):
    return list(nodes)


def node(name, children=None, **opts):
    if children:
        opts["children"] = children
    opts.setdefault("sticky", "nswe")
    return (name, opts)


class Theme:
    current = LIGHT

    def __init__(self, root):
        self.root = root
        self.s = max(1.0, root.winfo_fpixels("1i") / 96)
        self.style = ttk.Style(root)
        self.style.theme_use("clam")
        self.photos = {}
        self.created = False
        self.p = LIGHT

    def u(self, v):
        return max(1, round(v * self.s))

    def apply(self, dark):
        if self.created and self.p["dark"] == dark:
            return
        self.p = Theme.current = DARK if dark else LIGHT
        pieces = Pieces(self.p, self.s).build()
        for name, data in pieces.images.items():
            if name in self.photos:
                # Without blank(), the new image is laid over the old one, which shows through.
                self.photos[name].blank()
                self.photos[name].configure(data=data)
            else:
                self.photos[name] = tk.PhotoImage(master=self.root, name=f"skeuo_{name}", data=data)
        if not self.created:
            self._create(pieces)
            self.created = True
        self._configure()

    def _create(self, pc):
        st, u, img = self.style, self.u, lambda n: f"skeuo_{n}"

        def element(name, base, states=(), border=None, padding=None, sticky="nswe", fixed_height=False):
            kw = {"sticky": sticky}
            if border is not None:
                kw["border"] = border
                # A stretchable image must not impose its size: the content and padding decide it.
                kw["width"] = 1
                if not fixed_height:
                    kw["height"] = 1
            if padding is not None:
                kw["padding"] = padding
            st.element_create(name, "image", img(base), *[(*s, img(i)) for s, i in states], **kw)

        # The paddings start at the edge of the images, shadow and glow areas included.
        btn_pad = (u(10) + 1, u(4), u(10) + 1, u(4) + 2)
        element("Skeuo.button", "btn", [(("disabled",), "btn_dis"), (("pressed",), "btn_pressed"),
                                         (("active",), "btn_hover")], pc.borders["btn"], btn_pad)
        element("Skeuo.accent", "accent", [(("disabled",), "accent_dis"), (("pressed",), "accent_pressed"),
                                           (("active",), "accent_hover")], pc.borders["accent"], btn_pad)
        combo_pad = (u(8) + 1, u(4), 1, u(4) + 2)
        element("Skeuo.combo", "btn", [(("disabled",), "btn_dis"), (("pressed",), "btn_pressed"),
                                        (("active",), "btn_hover")], pc.borders["btn"], combo_pad)
        g = u(3)
        field_pad = (g + u(6), g + u(3), g + u(2), g + u(3))
        element("Skeuo.field", "field", [(("disabled",), "field_dis"), (("focus",), "field_focus")],
                pc.borders["field"], field_pad)
        element("Skeuo.tfield", "field", [(("disabled",), "field_dis")], pc.borders["field"], (g + 1,) * 4)
        element("Skeuo.inset", "field", [], pc.borders["field"], (g + 2,) * 4)
        element("Skeuo.lcd", "lcd", [], pc.borders["lcd"], (u(10), u(5), u(10), u(6)))
        element("Skeuo.card", "card", [], pc.borders["card"], (u(12), u(10), u(12), u(12)))
        element("Skeuo.client", "card", [], pc.borders["card"], (u(4), u(4), u(4), u(6)))
        element("Skeuo.tab", "tab", [(("selected",), "tab_sel"), (("active",), "tab_hover")],
                pc.borders["tab"], (u(14), u(6), u(14), u(5)))
        element("Skeuo.heading", "heading", [], pc.borders["heading"], (u(8), u(4), u(8), u(4)))
        element("Skeuo.check", "check_off", [(("disabled", "selected"), "check_on_dis"), (("disabled",), "check_off_dis"),
                                              (("selected",), "check_on")], sticky="")
        element("Skeuo.uparrow", "arrow_up", sticky="")
        element("Skeuo.downarrow", "arrow_down", sticky="")
        element("Skeuo.chevron", "chevron", sticky="")
        element("Skeuo.ptrough", "ptrough", [], pc.borders["ptrough"], (2, 2, 2, 3), fixed_height=True)
        element("Skeuo.pbar", "pbar", [], pc.borders["pbar"], (0, 0, 0, 0), fixed_height=True)
        element("Skeuo.strough", "strough", [], pc.borders["strough"], (0, 0, 0, 0), fixed_height=True)
        element("Skeuo.slider", "knob", [(("pressed",), "knob_pressed"), (("active",), "knob_active")], sticky="")

        st.layout("TButton", [node("Skeuo.button", [node("Button.padding", [node("Button.label")])])])
        st.layout("Accent.TButton", [node("Skeuo.accent", [node("Button.padding", [node("Button.label")])])])
        st.layout("TEntry", [node("Skeuo.field", [node("Entry.padding", [node("Entry.textarea")])])])
        st.layout("TSpinbox", [node("Skeuo.field", [
            node("null", [node("Skeuo.uparrow", side="top", sticky="e"),
                          node("Skeuo.downarrow", side="bottom", sticky="e")], side="right", sticky="ns"),
            node("Spinbox.padding", [node("Spinbox.textarea")])])])
        st.layout("TCombobox", [node("Skeuo.combo", [
            node("Skeuo.chevron", side="right", sticky=""),
            node("Combobox.padding", [node("Combobox.textarea")])])])
        st.layout("TCheckbutton", [node("Checkbutton.padding", [
            node("Skeuo.check", side="left", sticky=""), node("Checkbutton.label", side="left")])])
        st.layout("TNotebook", [node("Skeuo.client")])
        st.layout("TNotebook.Tab", [node("Skeuo.tab", [node("Notebook.padding", [node("Notebook.label")])])])
        st.layout("Treeview", [node("Skeuo.tfield", [node("Treeview.padding", [node("Treeview.treearea")])])])
        st.layout("Heading", [node("Skeuo.heading", [node("Treeheading.padding", [
            node("Treeheading.image", side="right", sticky=""), node("Treeheading.text", sticky="we")])])])
        st.layout("Horizontal.TProgressbar", [node("Skeuo.ptrough", [node("Skeuo.pbar", side="left", sticky="ns")])])
        st.layout("Horizontal.TScale", [node("Skeuo.strough", [node("Skeuo.slider", side="left", sticky="")])])
        # A frame places its content by its own padding option, which the style can't set: see padding().
        st.layout("Card.TFrame", [node("Skeuo.card")])
        st.layout("LCD.TFrame", [node("Skeuo.lcd")])
        st.layout("Inset.TFrame", [node("Skeuo.inset")])

    def padding(self, style):
        """The padding option to give to a frame of the style, to keep its content off the borders."""
        u = self.u
        return {"Card.TFrame": (u(12), u(10), u(12), u(12)),
                "LCD.TFrame": (u(10), u(5), u(10), u(6)),
                "Inset.TFrame": (u(3) + 2,) * 4}[style]

    def _configure(self):
        p, st, u = self.p, self.style, self.u
        st.configure(".", background=p["card"], foreground=p["text"], troughcolor=p["scroll_trough"],
                     selectbackground=p["select"], selectforeground=p["select_text"], fieldbackground=p["field"],
                     insertcolor=p["text"], bordercolor=p["field_border"], lightcolor=p["card"],
                     darkcolor=p["card"], focuscolor=p["glow"][0])
        # clam gives the disabled, hovered and pressed widgets a light background: it would show in
        # the transparent corners of the images.
        same_bg = [("disabled", p["card"]), ("pressed", p["card"]), ("active", p["card"])]
        st.map(".", background=same_bg, foreground=[("disabled", p["muted"])])
        for w in ("TButton", "Accent.TButton", "TCombobox", "TSpinbox", "TEntry", "TCheckbutton", "TLabel",
                  "Horizontal.TScale", "Heading"):
            st.map(w, background=same_bg)
        st.configure("TFrame", background=p["card"])
        st.configure("Backdrop.TFrame", background=p["bg"])
        st.configure("Card.TFrame", background=p["bg"])
        st.configure("TLabel", background=p["card"], foreground=p["text"])
        st.configure("Muted.TLabel", foreground=p["muted"])
        st.configure("Backdrop.TLabel", background=p["bg"], foreground=p["muted"])
        st.map("Backdrop.TLabel", background=[("disabled", p["bg"]), ("active", p["bg"])])
        st.configure("CardTitle.TLabel", font=("Segoe UI Semibold", 10), foreground=p["text"])
        st.configure("LCD.TFrame", background=p["card"])
        st.configure("LCD.TLabel", background=p["lcd"], foreground=p["lcd_text"], font=("Consolas", 10, "bold"))
        st.configure("TButton", foreground=p["text"], background=p["card"], anchor="center")
        st.map("TButton", foreground=[("disabled", p["muted"])], background=same_bg)
        st.configure("Accent.TButton", foreground=p["accent_text"], font=("Segoe UI Semibold", 10))
        st.map("Accent.TButton", foreground=[("disabled", p["muted"])], background=same_bg)
        st.configure("TCheckbutton", background=p["card"], foreground=p["text"])
        st.map("TCheckbutton", foreground=[("disabled", p["muted"])], background=same_bg)
        for w in ("TEntry", "TSpinbox"):
            st.configure(w, foreground=p["text"], insertcolor=p["text"], background=p["card"])
            st.map(w, foreground=[("disabled", p["muted"])])
        st.configure("TCombobox", foreground=p["text"], background=p["card"])
        # A readonly combobox looks like a pop-up button: no selection highlight of its text.
        st.map("TCombobox", foreground=[("disabled", p["muted"])],
               selectbackground=[("readonly", "")], selectforeground=[("readonly", p["text"])],
               fieldbackground=[("readonly", "")])
        st.configure("TNotebook", background=p["bg"], tabmargins=(u(10), u(4), u(10), 0))
        st.configure("TNotebook.Tab", foreground=p["muted"], background=p["bg"])
        st.map("TNotebook.Tab", foreground=[("selected", p["text"])], expand=[("selected", (0, 0, 0, 2))],
               background=[("selected", p["bg"]), ("active", p["bg"])])
        st.configure("Treeview", background=p["field"], fieldbackground=p["field"], foreground=p["text"],
                     rowheight=u(24))
        st.map("Treeview", background=[("selected", p["select"])], foreground=[("selected", p["select_text"])])
        st.configure("Heading", foreground=p["text"], background=p["card"], font=("Segoe UI Semibold", 9))
        st.configure("Horizontal.TProgressbar", background=p["card"])
        st.configure("Horizontal.TScale", background=p["card"])
        st.configure("TScrollbar", background=p["scroll_thumb"], troughcolor=p["scroll_trough"],
                     bordercolor=p["field_border"], lightcolor=p["scroll_thumb"], darkcolor=p["scroll_thumb"],
                     arrowcolor=p["text"], gripcount=0)
        st.map("TScrollbar", background=[("active", p["btn_hover"][1])])
        st.configure("TPanedwindow", background=p["bg"])
        st.configure("Sash", background=p["bg"], lightcolor=p["bg"], darkcolor=p["bg"], bordercolor=p["bg"],
                     sashthickness=u(10), gripcount=0)
        self.root.configure(background=p["bg"])
        self.root.option_add("*TCombobox*Listbox.background", p["field"])
        self.root.option_add("*TCombobox*Listbox.foreground", p["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", p["select"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", p["select_text"])

    def recolor_combobox(self, cb):
        """The drop-down list of a combobox is a classic Tk widget: color it by hand."""
        p = self.p
        popdown = self.root.tk.eval(f"ttk::combobox::PopdownWindow {cb}")
        self.root.tk.call(f"{popdown}.f.l", "configure", "-background", p["field"], "-foreground", p["text"],
                          "-selectbackground", p["select"], "-selectforeground", p["select_text"],
                          "-borderwidth", 0, "-highlightthickness", 0)


def windows_dark_mode():
    """True when Windows apps are set to the dark mode."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as k:
            return winreg.QueryValueEx(k, "AppsUseLightTheme")[0] == 0
    except (OSError, ImportError):
        return False


def set_title_bar_dark(window, dark):
    """Dark title bar on Windows 10 (20H1) and 11."""
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        user32.GetParent.argtypes = [wintypes.HWND]
        user32.GetParent.restype = wintypes.HWND
        window.update_idletasks()  # creates the Windows frame of the window, when it's not shown yet
        hwnd = user32.GetParent(window.winfo_id()) or window.winfo_id()
        value = ctypes.c_int(1 if dark else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(wintypes.HWND(hwnd), 20, ctypes.byref(value), ctypes.sizeof(value))
        # Redraw the frame: SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
        user32.SetWindowPos(wintypes.HWND(hwnd), None, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0004 | 0x0020)
    except (AttributeError, OSError):
        pass
