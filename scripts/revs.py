"""Community rev counter: visitors open a "rev|throttle" issue, .github/workflows/rev.yml calls this.

    python scripts/revs.py <github-login>   # count a rev, redraw assets/live/revs.svg
    python scripts/revs.py                  # just redraw

State lives in data/revs.json. Only the login GitHub reports is used; issue text is never read.
"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from svgkit import (CAUTION, CHALK, CHALK_DIM, CHALK_FAINT, COOLANT, FLARE, PLATE,  # noqa: E402
                    REDUCED_MOTION, panel, seven_seg, svg_doc, text, text_width)

DATA = os.path.join(ROOT, "data", "revs.json")
OUT = os.path.join(ROOT, "assets", "live", "revs.svg")
COOLDOWN = dt.timedelta(seconds=60)  # one counted rev per person per minute
SEG_OFF = "#15171f"


def load():
    if os.path.exists(DATA):
        with open(DATA, encoding="utf-8") as f:
            return json.load(f)
    return {"total": 0, "recent": [], "drivers": {}}


def save(state):
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    with open(DATA, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def rev(state, login):
    login = re.sub(r"[^A-Za-z0-9-]", "", login)[:39]
    if not login:
        return False
    now = dt.datetime.now(dt.timezone.utc)
    for r in state["recent"]:
        if r["login"] == login and now - dt.datetime.fromisoformat(r["at"]) < COOLDOWN:
            return False
    state["total"] += 1
    state["drivers"][login] = state["drivers"].get(login, 0) + 1
    state["recent"] = ([{"login": login, "at": now.isoformat(timespec="seconds")}] + state["recent"])[:5]
    return True


def render(state):
    w, h = 980, 230
    body = [panel(w, h)]
    style = [REDUCED_MOTION]
    # left: total revs
    body.append(text("COMMUNITY REVS", 44, 56, "heading", 13, CHALK, 2.4))
    segs, _ = seven_seg(f"{state['total']:>6}"[-6:], 44, 74, 70, FLARE, SEG_OFF, gap=10)
    body.append(segs)
    body.append(text("PRESS REV IT BELOW // EVERY VISIT COUNTS", 44, 182, "mono", 9.5, CHALK_FAINT, 1.2))
    # middle: LED tach bar that blips to the limiter on a loop
    n, bx, by, bw, bh = 20, 352, 84, 13, 52
    cols = [COOLANT] * 8 + [CAUTION] * 6 + [FLARE] * 6
    body.append(text("RPM x1000", bx, 66, "mono", 9.5, CHALK_FAINT, 1.2))
    for i in range(n):
        x = bx + i * (bw + 4)
        body.append(f'<rect x="{x}" y="{by}" width="{bw}" height="{bh}" rx="2" fill="{SEG_OFF}" stroke="{PLATE}" stroke-width="1"/>')
        body.append(f'<rect class="b{i}" x="{x + 2}" y="{by + 2}" width="{bw - 4}" height="{bh - 4}" rx="1" fill="{cols[i]}" '
                    f'opacity="{1 if i < 5 else 0}"/>')
        on = 10 + i * 2.2
        style.append(f".b{i}{{animation:b{i} 3.6s infinite}}@keyframes b{i}{{0%,{on:.1f}%{{opacity:{1 if i < 5 else 0}}}"
                     f"{on + 0.5:.1f}%,58%{{opacity:1}}70%,100%{{opacity:{1 if i < 5 else 0}}}}}")
        if i % 4 == 0:
            body.append(text(str(i // 2), x + bw / 2, by + bh + 18, "mono", 9.5, CHALK_DIM, 0, "middle"))
    body.append(text("LIMITER", bx + n * (bw + 4) - 4, 66, "mono-bold", 9.5, FLARE, 1, "end"))
    # right: who's been on the throttle
    rx = 724
    body.append(text("LAST ON THE THROTTLE", rx, 56, "heading", 11, CHALK, 2))
    recent = state["recent"][:4] or [{"login": "your-name-here"}]
    for i, r in enumerate(recent):
        name = "@" + r["login"]
        size = 13
        while text_width(name, "mono", size) > w - rx - 50 and size > 8:
            size -= 0.5
        body.append(f'<circle cx="{rx + 4}" cy="{80 + i * 26 - 4}" r="3" fill="{COOLANT if i == 0 else PLATE}"/>')
        body.append(text(name, rx + 16, 80 + i * 26, "mono", size, CHALK if i == 0 else CHALK_DIM))
    if state["drivers"]:
        top, count = max(state["drivers"].items(), key=lambda kv: (kv[1], kv[0]))
        body.append(text(f"TOP DRIVER @{top} x{count}", rx, 196, "mono-bold", 9.5, FLARE, 0.8))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg_doc(w, h, "".join(body), f"Community rev counter: {state['total']} revs", "".join(style)))


def main():
    state = load()
    if len(sys.argv) > 1:
        counted = rev(state, sys.argv[1])
        print("counted" if counted else "cooldown, not counted")
    save(state)
    render(state)


if __name__ == "__main__":
    main()
