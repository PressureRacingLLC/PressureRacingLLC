"""The Lot: visitors pull up and park in a top-down meet lot. .github/workflows/pull-up.yml calls this
when someone opens a "pull-up" issue from the README.

    python scripts/lot.py <github-login>   # park them, redraw assets/live/lot.svg
    python scripts/lot.py                  # just redraw

State lives in data/lot.json. Only the login GitHub reports is used; issue text is never read.
"""
import datetime as dt
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from svgkit import (CAUTION, CHALK, CHALK_DIM, CHALK_FAINT, COOLANT, FLARE, PLATE, PLATE_HI,  # noqa: E402
                    REDUCED_MOTION, panel, seven_seg, svg_doc, text, text_width)

DATA = os.path.join(ROOT, "data", "lot.json")
OUT = os.path.join(ROOT, "assets", "live", "lot.svg")
STALLS = 12
COOLDOWN = dt.timedelta(seconds=60)
SEG_OFF = "#15171f"
PAINT = [CHALK, FLARE, COOLANT, CAUTION, "#4d8dff", "#ff6a3d", "#8b93a8", "#c77dff"]


def load():
    if os.path.exists(DATA):
        with open(DATA, encoding="utf-8") as f:
            return json.load(f)
    return {"total": 0, "parked": [], "visits": {}}


def save(state):
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    with open(DATA, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def pull_up(state, login):
    login = re.sub(r"[^A-Za-z0-9-]", "", login)[:39]
    if not login:
        return False
    now = dt.datetime.now(dt.timezone.utc)
    mine = [p for p in state["parked"] if p["login"] == login]
    if mine and now - dt.datetime.fromisoformat(mine[0]["at"]) < COOLDOWN:
        return False
    state["total"] += 1
    state["visits"][login] = state["visits"].get(login, 0) + 1
    # pulling up again moves your car to the front spot instead of parking a second one
    rest = [p for p in state["parked"] if p["login"] != login]
    state["parked"] = ([{"login": login, "at": now.isoformat(timespec="seconds")}] + rest)[:STALLS]
    return True


def paint_for(login):
    return PAINT[int(hashlib.sha1(login.lower().encode()).hexdigest(), 16) % len(PAINT)]


def car(cx, cy, paint, nose_up, lights):
    """Top-down coupe, drawn nose-up around (0, 0) then placed. Original shape."""
    glass = "#0d1018"
    trim = "#07080b"
    parts = [
        # tyres
        *[f'<rect x="{x}" y="{y}" width="9" height="22" rx="3" fill="{trim}"/>' for x in (-33, 24) for y in (-42, 22)],
        # body and shoulder line
        f'<path d="M-26,-50 Q-30,-56 -20,-60 L20,-60 Q30,-56 26,-50 L29,-20 L30,40 Q30,58 18,60 L-18,60 Q-30,58 -30,40 L-29,-20 Z" fill="{paint}"/>',
        f'<path d="M-22,-48 L22,-48 M-25,44 L25,44" stroke="{trim}" stroke-opacity=".35" stroke-width="1.5"/>',
        # windshield, roof, rear glass
        f'<path d="M-21,-24 Q0,-32 21,-24 L18,-6 L-18,-6 Z" fill="{glass}"/>',
        f'<rect x="-18" y="-6" width="36" height="26" rx="4" fill="{paint}" stroke="{trim}" stroke-opacity=".25"/>',
        f'<path d="M-18,20 L18,20 L20,32 Q0,37 -20,32 Z" fill="{glass}"/>',
        # mirrors
        '<path d="M-30,-20 l-6,2 l1,5 l5,-1 Z M30,-20 l6,2 l-1,5 l-5,-1 Z" fill="%s"/>' % paint,
        # headlights and taillights
        f'<rect x="-24" y="-60" width="12" height="4" rx="2" fill="{CHALK if lights else "#c9c6bf"}"/>',
        f'<rect x="12" y="-60" width="12" height="4" rx="2" fill="{CHALK if lights else "#c9c6bf"}"/>',
        f'<rect class="{"tail" if lights else ""}" x="-26" y="56" width="14" height="4" rx="2" fill="{FLARE}"/>',
        f'<rect class="{"tail" if lights else ""}" x="12" y="56" width="14" height="4" rx="2" fill="{FLARE}"/>',
    ]
    if lights:  # headlight beams
        parts.insert(0, '<defs><linearGradient id="beam" x1="0" y1="1" x2="0" y2="0">'
                        f'<stop offset="0" stop-color="{CHALK}" stop-opacity=".45"/><stop offset="1" stop-color="{CHALK}" stop-opacity="0"/>'
                        '</linearGradient></defs>'
                        '<path d="M-24,-60 L-44,-110 L-2,-110 L-12,-60 Z M12,-60 L2,-110 L44,-110 L24,-60 Z" fill="url(#beam)"/>')
    rot = 0 if nose_up else 180
    return f'<g transform="translate({cx},{cy}) rotate({rot}) scale(.82)">{"".join(parts)}</g>'


def render(state):
    w, h = 980, 440
    body = [panel(w, h)]
    style = [REDUCED_MOTION,
             "@keyframes park{from{transform:translateY(var(--d))}}",
             "@keyframes tail{50%{opacity:.25}}.tail{animation:tail 1.1s ease-in-out 6}"]
    # header: title, count, regulars
    body.append(text("THE LOT", 44, 58, "display", 26, CHALK, 2))
    body.append(text("NEWEST ARRIVAL TAKES SPOT 01", 44, 80, "mono", 9.5, CHALK_FAINT, 1.2))
    body.append(text("PULLED UP", w - 44, 46, "mono", 9.5, CHALK_FAINT, 1.2, "end"))
    segs, _ = seven_seg(f"{state['total']:>5}"[-5:], w - 44, 54, 34, FLARE, SEG_OFF, "end", gap=6)
    body.append(segs)
    # asphalt
    lx, ly, lw, lh = 30, 104, w - 60, 316
    body.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" rx="8" fill="#0b0c11" stroke="{PLATE}" stroke-width="1"/>')
    cols = STALLS // 2
    sw = lw / cols
    row_h = 128
    top_y, bot_y = ly + 8, ly + lh - 8 - row_h
    # stall lines and drive-lane arrows
    for r, y0 in ((0, top_y), (1, bot_y)):
        for c in range(cols + 1):
            x = lx + c * sw
            body.append(f'<line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y0 + row_h}" stroke="{CHALK_DIM}" stroke-opacity=".55" stroke-width="2"/>')
        edge = y0 + row_h if r == 0 else y0
        body.append(f'<line x1="{lx}" y1="{edge}" x2="{lx + lw}" y2="{edge}" stroke="{CHALK_DIM}" stroke-opacity=".18" stroke-width="1" stroke-dasharray="10 8"/>')
    lane_y = (top_y + row_h + bot_y) / 2
    for k in range(5):
        ax = lx + 90 + k * 190
        body.append(f'<path d="M{ax},{lane_y - 6} l22,6 l-22,6 z" fill="{PLATE_HI}"/>')
    parked = state["parked"]
    for i in range(STALLS):
        r, c = (0, i) if i < cols else (1, i - cols)
        cx = lx + c * sw + sw / 2
        y0 = top_y if r == 0 else bot_y
        stall_no = f"{i + 1:02d}"
        # stall number at the lane end, name painted at the curb end
        ny = y0 + row_h - 8 if r == 0 else y0 + 17
        body.append(text(stall_no, lx + c * sw + 10, ny, "mono-bold", 9, CHALK_FAINT, 1))
        if i < len(parked):
            p = parked[i]
            newest = i == 0
            cy = y0 + row_h / 2 + (8 if r == 0 else -8)
            c_svg = car(cx, cy, paint_for(p["login"]), nose_up=(r == 1), lights=newest)
            if newest:  # drives in from the lane
                c_svg = f'<g class="arrive" style="--d:{60 if r == 0 else -60}px">{c_svg}</g>'
                style.append(".arrive{animation:park 1.4s cubic-bezier(.2,.8,.2,1) .3s both}")
            body.append(c_svg)
            name = "@" + p["login"]
            size = 10.5
            while text_width(name, "mono", size) > sw - 14 and size > 8:
                size -= 0.5
            while text_width(name, "mono", size) > sw - 14:
                name = name[:-4] + "..."
            ty = y0 + 14 if r == 0 else y0 + row_h - 5
            body.append(text(name, cx, ty, "mono-bold" if newest else "mono", size, COOLANT if newest else CHALK_DIM, 0, "middle"))
        else:
            body.append(text("OPEN", cx, y0 + row_h / 2 + 4, "mono", 10, PLATE_HI, 3, "middle"))
    title = f"The Lot: {state['total']} pulled up" + (f", newest @{parked[0]['login']}" if parked else "")
    return svg_doc(w, h, "".join(body), title, "".join(style))


def main():
    state = load()
    if len(sys.argv) > 1:
        print("parked" if pull_up(state, sys.argv[1]) else "cooldown, not counted")
    save(state)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(render(state))


if __name__ == "__main__":
    main()
