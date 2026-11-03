"""Shared pieces for the profile's SVGs: brand palette, text outlined in the brand fonts, seven-segment digits.

Text is converted to <path> outlines (Archivo / Martian Mono, SIL OFL, in tools/fonts) so every SVG
renders the same everywhere: GitHub serves README images through a proxy that can't load web fonts.
Needs: pip install fonttools brotli
"""
import functools
import os

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

# pressureracing.com tokens
INK = "#0a0b0f"
INK_SOFT = "#14161e"
GROUND = "#161923"
RAISED = "#1e2230"
PLATE = "#2a2f3e"
PLATE_HI = "#3a4152"
CHALK = "#f2f0ec"
CHALK_DIM = "#a8afc4"
CHALK_FAINT = "#6f778c"
FLARE = "#f800e0"
FLARE_LIFT = "#ff4dec"
FLARE_DEEP = "#a8009a"
COOLANT = "#00e5d0"
CAUTION = "#ffb300"
FAULT = "#ff3b30"

# named cuts: (file, axis settings)
CUTS = {
    "display": ("archivo.woff2", {"wght": 900, "wdth": 125}),   # extra-wide black, the motorsport cut
    "heading": ("archivo.woff2", {"wght": 800, "wdth": 112}),
    "label": ("archivo.woff2", {"wght": 700, "wdth": 100}),
    "mono": ("martian-mono.woff2", {"wght": 500, "wdth": 100}),
    "mono-bold": ("martian-mono.woff2", {"wght": 750, "wdth": 112.5}),
}


@functools.lru_cache(maxsize=None)
def _font(cut):
    file, axes = CUTS[cut]
    f = TTFont(os.path.join(FONTS, file))
    f = instantiateVariableFont(f, axes)
    return f, f.getGlyphSet(), f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm


def _num(v):
    """0.1px precision keeps outlined text crisp and the SVGs small."""
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def text_width(text, cut, size, tracking=0.0):
    f, gs, cmap, hmtx, upm = _font(cut)
    adv = sum(hmtx[cmap.get(ord(c), ".notdef")][0] for c in text)
    return adv * size / upm + tracking * max(0, len(text) - 1)


def text_path(text, x, y, cut, size, tracking=0.0, anchor="start"):
    """SVG path data for `text` with its baseline at y. anchor: start | middle | end."""
    f, gs, cmap, hmtx, upm = _font(cut)
    w = text_width(text, cut, size, tracking)
    if anchor == "middle":
        x -= w / 2
    elif anchor == "end":
        x -= w
    s = size / upm
    pen = SVGPathPen(gs, ntos=_num)
    cx = x
    for c in text:
        g = cmap.get(ord(c), ".notdef")
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, cx, y)))
        cx += hmtx[g][0] * s + tracking
    return pen.getCommands()


def text(t, x, y, cut, size, fill, tracking=0.0, anchor="start", extra=""):
    d = text_path(t, x, y, cut, size, tracking, anchor)
    return f'<path d="{d}" fill="{fill}" {extra}/>'


# --- seven-segment digits (OLED style; unlit segments glow faintly) ---------------------
#  aaa
# f   b
#  ggg
# e   c
#  ddd
SEGS = {
    "0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc",
    "7": "abc", "8": "abcdefg", "9": "abcfgd", "-": "g", " ": "",
}


def _seg_poly(seg, x, y, w, h, t):
    """Hexagonal segment polygon inside a w*h cell at (x, y), thickness t, with a slight italic slant."""
    hh = h / 2
    k = t / 2
    sl = 0.12 * h  # slant: top shifted right

    def P(px, py):
        return (x + px + sl * (1 - py / h), y + py)

    if seg in "adg":
        yy = {"a": k, "g": hh, "d": h - k}[seg]
        pts = [P(k + 1, yy), P(2 * k + 1, yy - k), P(w - 2 * k - 1, yy - k), P(w - k - 1, yy), P(w - 2 * k - 1, yy + k), P(2 * k + 1, yy + k)]
    else:
        xx = k if seg in "ef" else w - k
        y0, y1 = (k + 1, hh - 1) if seg in "fb" else (hh + 1, h - k - 1)
        pts = [P(xx, y0), P(xx + k, y0 + k), P(xx + k, y1 - k), P(xx, y1), P(xx - k, y1 - k), P(xx - k, y0 + k)]
    return " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)


def seven_seg(value, x, y, h, on, off, anchor="start", gap=None):
    """Seven-segment readout. Returns (svg, width)."""
    w = h * 0.52
    t = max(2.0, h * 0.11)
    gap = gap if gap is not None else h * 0.16
    total = len(value) * w + (len(value) - 1) * gap
    if anchor == "middle":
        x -= total / 2
    elif anchor == "end":
        x -= total
    out = []
    for i, ch in enumerate(value):
        cx = x + i * (w + gap)
        lit = SEGS.get(ch, "")
        for seg in "abcdefg":
            fill = on if seg in lit else off
            out.append(f'<polygon points="{_seg_poly(seg, cx, y, w, h, t)}" fill="{fill}"/>')
    return "".join(out), total


def panel(w, h, r=18):
    """Dash-panel screen: plate bezel, OLED-black glass, faint scanlines."""
    return (f'<defs><pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
            f'<rect width="4" height="1" fill="#ffffff" opacity=".025"/></pattern>'
            f'<radialGradient id="glass" cx=".5" cy=".35" r=".8"><stop offset="0" stop-color="#101219"/>'
            f'<stop offset="1" stop-color="#050608"/></radialGradient></defs>'
            f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="{r}" fill="{RAISED}" stroke="{PLATE_HI}" stroke-width="2"/>'
            f'<rect x="10" y="10" width="{w - 20}" height="{h - 20}" rx="{r - 8}" fill="url(#glass)"/>'
            f'<rect x="10" y="10" width="{w - 20}" height="{h - 20}" rx="{r - 8}" fill="url(#scan)"/>')


def svg_doc(w, h, body, title, style=""):
    style_tag = f"<style>{style}</style>" if style else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{title}"><title>{title}</title>{style_tag}{body}</svg>')


REDUCED_MOTION = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"
