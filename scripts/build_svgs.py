"""Static animated SVGs for the README: ECU boot screen, section plates, switch-panel buttons.

All text is outlined in the brand fonts (tools/svgkit.py). Animations are CSS inside the SVG, which
GitHub plays in README images; every element's resting state is fully visible, so nothing is lost
when motion is off.
    py scripts/build_svgs.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from svgkit import (CHALK, CHALK_DIM, CHALK_FAINT, COOLANT, FLARE, FLARE_DEEP, GROUND, INK, PLATE,  # noqa: E402
                    PLATE_HI, RAISED, REDUCED_MOTION, panel, svg_doc, text, text_width)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "svg")


def save(name, svg):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print(f"{name:24s} {os.path.getsize(path) / 1024:.1f} KB")


# --- ECU boot screen ---------------------------------------------------------------------

def ecu_boot():
    w, h = 980, 250
    lines = [
        ("PR-ECU 2.6 // KEY ON", "", CHALK_DIM),
        ("FUEL PUMP ...... ", "OK", COOLANT),
        ("BOOST CTRL ..... ", "ARMED", FLARE),
        ("LAUNCH CTRL .... ", "SET", COOLANT),
    ]
    size, x0, y0, lh = 14, 44, 56, 27
    char_w = text_width("0", "mono", size)
    body = [panel(w, h)]
    # the shutter rests invisible; it is only drawn while it slides
    style = [REDUCED_MOTION,
             "@keyframes type{from{transform:translateX(0);opacity:1}to{opacity:1}}",
             "@keyframes blink{50%{opacity:0}}",
             "@keyframes rise{from{opacity:0;transform:translateY(8px)}}",
             ".cur{animation:blink 1s steps(1) infinite}"]
    t = 0.25
    for i, (a, b, col) in enumerate(lines):
        y = y0 + i * lh
        full = a + b
        body.append(text(a, x0, y, "mono", size, CHALK_DIM))
        if b:
            bx = x0 + text_width(a, "mono", size)
            body.append(text(b, bx, y, "mono-bold", size, col))
        n = len(full)
        dur = n * 0.022
        # an ink shutter slides off the line one character at a time; at rest it sits off to the right
        body.append(f'<rect class="s{i}" x="{x0 - 2}" y="{y - size}" width="{n * char_w + 30}" height="{size + 8}" '
                    f'fill="#08090d" style="transform:translateX({n * char_w + 40}px);opacity:0"/>')
        style.append(f".s{i}{{animation:type {dur:.2f}s steps({n}) {t:.2f}s backwards}}")
        t += dur + 0.18
    # brand lockup on the right of the screen
    rx = w - 48
    room = rx - (x0 + max(len(a + b) for a, b, _ in lines) * char_w + 70)
    bsize = 46
    while text_width("PRESSURE RACING", "display", bsize, 1.0) > room:
        bsize -= 1
    body.append(f'<g class="brand">{text("PRESSURE RACING", rx, 116, "display", bsize, CHALK, 1.0, "end")}'
                f'{text("AUTOMOTIVE RACING BRAND", rx, 150, "mono-bold", 14, FLARE, 4.2, "end")}</g>')
    style.append(f".brand{{animation:rise .6s ease-out {t:.2f}s backwards}}")
    # status strip
    yb = h - 40
    body.append(f'<line x1="44" y1="{yb - 18}" x2="{w - 44}" y2="{yb - 18}" stroke="{PLATE}" stroke-width="1"/>')
    body.append(text("READY", 44, yb, "mono-bold", 13, COOLANT, 3))
    body.append(f'<rect class="cur" x="{44 + text_width("READY", "mono-bold", 13, 3) + 10}" y="{yb - 12}" width="9" height="14" fill="{COOLANT}"/>')
    for k, lab in enumerate(["IGN", "FUEL", "BOOST", "TC"]):
        cx = w - 44 - (3 - k) * 92 - 60
        body.append(f'<circle cx="{cx}" cy="{yb - 5}" r="4.5" fill="{FLARE if lab == "BOOST" else COOLANT}"/>')
        body.append(text(lab, cx + 12, yb, "mono", 11, CHALK_FAINT, 1.5))
    save("ecu-boot.svg", svg_doc(w, h, "".join(body), "Pressure Racing. Automotive Racing Brand.", "".join(style)))


# --- section plates ------------------------------------------------------------------------

def plate(num, title, slug):
    w, h = 980, 64
    body = [
        '<defs><linearGradient id="sweep" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#fff" stop-opacity=".09"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        '<clipPath id="c"><rect x="0" y="0" width="980" height="64" rx="10"/></clipPath></defs>',
        f'<g clip-path="url(#c)"><rect width="{w}" height="{h}" fill="{INK}"/>',
        # number tab, slanted
        f'<polygon points="0,0 96,0 76,{h} 0,{h}" fill="{FLARE}"/>',
        text(num, 40, 42, "display", 26, INK, 0, "middle"),
        # hazard hatching on the right
        "".join(f'<polygon points="{w - 230 + i * 22},{h} {w - 210 + i * 22},0 {w - 200 + i * 22},0 {w - 220 + i * 22},{h}" '
                f'fill="{PLATE}"/>' for i in range(11)),
        f'<rect x="{w - 250}" y="0" width="40" height="{h}" fill="{INK}"/>',
        text(title, 116, 43, "display", 28, CHALK, 2.5),
        f'<rect class="sw" x="-300" y="0" width="300" height="{h}" fill="url(#sweep)"/>',
        f'<rect x="0" y="{h - 4}" width="{w}" height="4" fill="{FLARE}"/></g>',
        f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="10" fill="none" stroke="{PLATE_HI}" stroke-width="2"/>',
    ]
    style = REDUCED_MOTION + "@keyframes sw{to{transform:translateX(1300px)}}.sw{animation:sw 4.5s ease-in-out infinite}"
    save(f"sec-{slug}.svg", svg_doc(w, h, "".join(body), title.title(), style))


# --- switch-panel buttons -----------------------------------------------------------------

def switch(slug, label, sub, accent=FLARE):
    w, h = 188, 70
    lab_size = 17
    while text_width(label, "heading", lab_size, 1.5) > w - 58:
        lab_size -= 1
    sub_size = 10
    while text_width(sub, "mono", sub_size, 0.3) > w - 58:
        sub_size -= 0.5
    body = [
        f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="12" fill="{RAISED}" stroke="{PLATE_HI}" stroke-width="2"/>',
        f'<rect x="7" y="7" width="{w - 14}" height="{h - 14}" rx="8" fill="{INK}"/>',
        # rocker with LED
        f'<rect x="16" y="16" width="22" height="38" rx="5" fill="{GROUND}" stroke="{PLATE}" stroke-width="1.5"/>',
        f'<rect x="19" y="19" width="16" height="16" rx="3" fill="{PLATE_HI}"/>',
        f'<circle class="led" cx="27" cy="45" r="4" fill="{accent}"/>',
        f'<circle class="glow" cx="27" cy="45" r="8" fill="{accent}" opacity=".25"/>',
        text(label, 48, 36, "heading", lab_size, CHALK, 1.5),
        text(sub, 48, 52, "mono", sub_size, CHALK_DIM, 0.3),
    ]
    style = (REDUCED_MOTION + "@keyframes p{50%{opacity:.35}}"
             ".led,.glow{animation:p 2.4s ease-in-out infinite}")
    save(f"btn-{slug}.svg", svg_doc(w, h, "".join(body), f"{label}: {sub}", style))


def rev_button():
    w, h = 360, 92
    body = [
        f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="16" fill="{FLARE_DEEP}" stroke="{FLARE}" stroke-width="2"/>',
        f'<rect class="hot" x="8" y="8" width="{w - 16}" height="{h - 16}" rx="11" fill="{FLARE}"/>',
        text("REV IT", 34, 54, "display", 36, INK, 2),
        text("PRESS TO HIT THE LIMITER", 36, 75, "mono-bold", 10, INK, 1.6),
        # throttle arrows
        "".join(f'<polygon class="a{i}" points="{250 + i * 26},28 {268 + i * 26},46 {250 + i * 26},64 {240 + i * 26},64 {258 + i * 26},46 {240 + i * 26},28" fill="{INK}"/>'
                for i in range(3)),
    ]
    style = (REDUCED_MOTION + "@keyframes hot{50%{fill:#ff4dec}}.hot{animation:hot 1.6s ease-in-out infinite}"
             "@keyframes a{0%,100%{opacity:.25}40%{opacity:1}}"
             + "".join(f".a{i}{{animation:a 1.2s {i * 0.18:.2f}s infinite}}" for i in range(3)))
    save("btn-rev.svg", svg_doc(w, h, "".join(body), "Rev it: press to hit the limiter", style))


if __name__ == "__main__":
    ecu_boot()
    for num, title, slug in [("01", "THE GARAGE", "garage"), ("02", "THE BRAND", "brand"), ("03", "PARTS LIST", "parts"),
                             ("04", "TELEMETRY", "telemetry"), ("05", "REV IT", "rev"), ("06", "ON BOARD", "onboard")]:
        plate(num, title, slug)
    switch("web", "WEBSITE", "pressureracing.com")
    switch("instagram", "INSTAGRAM", "@pressureracinggarage")
    switch("tiktok", "TIKTOK", "@pressureracing")
    switch("youtube", "YOUTUBE", "Pressure Racing")
    switch("github", "GITHUB", "PressureRacingLLC", COOLANT)
    rev_button()
