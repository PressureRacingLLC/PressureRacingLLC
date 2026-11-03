"""Render the profile's GitHub stats as an OLED gauge cluster (dash.svg), from the GitHub GraphQL API.

Runs in .github/workflows/profile-assets.yml. Needs: pip install fonttools brotli
    GH_TOKEN=... python scripts/stats.py <login> <out_dir>

With the default Actions token only public data is counted. A classic PAT in the
METRICS_TOKEN secret (scopes: read:user, repo) adds private-repo languages.
"""
import datetime as dt
import json
import math
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from svgkit import (CAUTION, CHALK, CHALK_DIM, CHALK_FAINT, COOLANT, FLARE, PLATE, PLATE_HI,  # noqa: E402
                    REDUCED_MOTION, panel, seven_seg, svg_doc, text)

API = "https://api.github.com/graphql"
SEG_OFF = "#15171f"  # unlit OLED segment


def gql(query, **variables):
    req = urllib.request.Request(
        API, data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {os.environ['GH_TOKEN']}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        body = json.load(r)
    if body.get("errors"):
        raise SystemExit(f"GraphQL error: {body['errors']}")
    return body["data"]


PROFILE = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection { contributionYears }
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]) { totalCount }
    repositories(first: 100, isFork: false, ownerAffiliations: [OWNER, ORGANIZATION_MEMBER]) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
      }
    }
  }
}"""

YEAR = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
  }
}"""


def collect(login):
    u = gql(PROFILE, login=login)["user"]
    days, commits = {}, 0
    now = dt.datetime.now(dt.timezone.utc)
    # Commits count by their author date, which can predate the account, so ask GitHub
    # which years have contributions instead of starting at createdAt.
    for year in sorted(u["contributionsCollection"]["contributionYears"]):
        frm = dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc)
        to = min(now, dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc))
        c = gql(YEAR, login=login, **{"from": frm.isoformat(), "to": to.isoformat()})["user"]["contributionsCollection"]
        commits += c["totalCommitContributions"] + c["restrictedContributionsCount"]
        for w in c["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = d["contributionCount"]
    langs = {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            n = e["node"]["name"]
            size, color = langs.get(n, (0, e["node"]["color"]))
            langs[n] = (size + e["size"], color or CHALK_DIM)
    return dict(
        stars=sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        commits=commits,
        prs=u["pullRequests"]["totalCount"],
        issues=u["issues"]["totalCount"],
        contributed=u["repositoriesContributedTo"]["totalCount"],
        repos=u["repositories"]["totalCount"],
        followers=u["followers"]["totalCount"],
        days=dict(sorted(days.items())),
        langs=sorted(langs.items(), key=lambda kv: -kv[1][0]),
        today=now.date(),
    )


def streaks(days, today):
    dates = [dt.date.fromisoformat(d) for d, c in days.items() if c > 0]
    longest = run = 0
    prev = None
    for d in dates:
        run = run + 1 if prev and (d - prev).days == 1 else 1
        longest = max(longest, run)
        prev = d
    have = set(dates)
    cur = 0
    d = today if today in have else today - dt.timedelta(days=1)  # today may still be empty
    while d in have:
        cur += 1
        d -= dt.timedelta(days=1)
    return cur, longest


# --- gauge cluster ------------------------------------------------------------------------

def nice_max(v, floor):
    """Smallest 'nice' full-scale value with headroom above v."""
    target = max(floor, v * 1.3)
    mag = 10 ** math.floor(math.log10(target))
    for m in (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if m * mag >= target:
            return int(m * mag)
    return int(10 * mag)


def polar(cx, cy, r, t):
    a = math.radians(135 + 270 * t)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def arc(cx, cy, r, t0, t1):
    x0, y0 = polar(cx, cy, r, t0)
    x1, y1 = polar(cx, cy, r, t1)
    large = 1 if (t1 - t0) * 270 > 180 else 0
    return f"M{x0:.1f},{y0:.1f} A{r},{r} 0 {large} 1 {x1:.1f},{y1:.1f}"


def gauge(cx, cy, r, value, vmax, label, sub):
    t = min(value / vmax, 1.0)
    out = [
        f'<circle cx="{cx}" cy="{cy}" r="{r + 14}" fill="#07080b" stroke="{PLATE}" stroke-width="2"/>',
        f'<path d="{arc(cx, cy, r, 0, 1)}" fill="none" stroke="{PLATE}" stroke-width="6"/>',
        f'<path d="{arc(cx, cy, r, 0.82, 1)}" fill="none" stroke="{FLARE}" stroke-width="6"/>',  # redline
        f'<path d="{arc(cx, cy, r - 1, 0, max(t, 0.001))}" fill="none" stroke="{COOLANT}" stroke-width="3" opacity=".9"/>',
    ]
    for i in range(41):
        tt = i / 40
        major = i % 4 == 0
        x0, y0 = polar(cx, cy, r - 6, tt)
        x1, y1 = polar(cx, cy, r - (20 if major else 12), tt)
        col = FLARE if tt >= 0.82 else (CHALK if major else CHALK_FAINT)
        out.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{col}" stroke-width="{2.4 if major else 1.2}"/>')
        if major:
            lx, ly = polar(cx, cy, r - 36, tt)
            num = vmax * tt
            out.append(text(f"{num:g}" if num < 1000 else f"{num / 1000:g}K", lx, ly + 4, "mono", 10.5, CHALK_DIM, 0, "middle"))
    # digital readout and labels
    segs, _ = seven_seg(f"{value}", cx, cy + r * 0.28, r * 0.24, CHALK, SEG_OFF, "middle")
    out.append(segs)
    out.append(text(label, cx, cy + r * 0.72, "heading", 13, CHALK, 2.2, "middle"))
    out.append(text(sub, cx, cy + r * 0.72 + 18, "mono", 9.5, CHALK_FAINT, 1.2, "middle"))
    # needle: sweeps to the stop on load, then settles on the value
    a_rest, a_val = 135, 135 + 270 * t
    needle = (f'<g><polygon points="{cx - 14},{cy - 3.5} {cx + r - 12},{cy - 1} {cx + r - 12},{cy + 1} {cx - 14},{cy + 3.5}" fill="{FLARE}"/>'
              f'<animateTransform attributeName="transform" type="rotate" dur="2.4s" begin="0s" fill="freeze" '
              f'calcMode="spline" keyTimes="0;0.45;1" keySplines=".3 0 .2 1;.4 0 .2 1" '
              f'values="{a_rest} {cx} {cy};{135 + 270 * 0.97:.1f} {cx} {cy};{a_val:.1f} {cx} {cy}"/>'
              f'</g>')
    # resting pose (no-SMIL viewers): the transform attribute already points at the value
    needle = needle.replace("<g>", f'<g transform="rotate({a_val:.1f} {cx} {cy})">', 1)
    out.append(needle)
    out.append(f'<circle cx="{cx}" cy="{cy}" r="11" fill="#1a1d27" stroke="{PLATE_HI}" stroke-width="2"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="{FLARE}"/>')
    return "".join(out)


def shift_lights(cx, y, lit_frac):
    n = 12
    cols = [COOLANT] * 4 + [CAUTION] * 4 + [FLARE] * 4
    lit = max(1, round(n * lit_frac))
    out, style = [], []
    for i in range(n):
        x = cx + (i - (n - 1) / 2) * 26
        on = i < lit
        out.append(f'<circle cx="{x:.1f}" cy="{y}" r="6.5" fill="{SEG_OFF}" stroke="{PLATE}" stroke-width="1"/>')
        # every light flashes during the sweep; the first `lit` stay on afterwards
        out.append(f'<circle class="sl{i}" cx="{x:.1f}" cy="{y}" r="5" fill="{cols[i]}" opacity="{1 if on else 0}"/>')
        style.append(f".sl{i}{{animation:sl{i} 2.4s .4s both}}"
                     f"@keyframes sl{i}{{0%{{opacity:0}}{8 + i * 3}%{{opacity:1}}55%{{opacity:1}}100%{{opacity:{1 if on else 0}}}}}")
    return "".join(out), "".join(style)


def dyno(x, y, w, h, s, span=31):
    pts_d = [s["today"] - dt.timedelta(days=span - 1 - i) for i in range(span)]
    vals = [s["days"].get(d.isoformat(), 0) for d in pts_d]
    peak = max(max(vals), 4)
    sx = w / (span - 1)
    xy = [(x + i * sx, y + h - h * v / peak) for i, v in enumerate(vals)]
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#07080b" stroke="{PLATE}" stroke-width="1"/>']
    for k in range(1, 4):
        gy = y + h * k / 4
        out.append(f'<line x1="{x}" y1="{gy:.1f}" x2="{x + w}" y2="{gy:.1f}" stroke="{PLATE}" stroke-width=".6" stroke-dasharray="2 4"/>')
    line = " ".join(f"{a:.1f},{b:.1f}" for a, b in xy)
    out.append('<defs><linearGradient id="dy" x1="0" y1="0" x2="0" y2="1">'
               f'<stop offset="0" stop-color="{FLARE}" stop-opacity=".5"/><stop offset="1" stop-color="{FLARE}" stop-opacity="0"/>'
               '</linearGradient><clipPath id="dyc">'
               f'<rect class="dyw" x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath></defs>')
    out.append(f'<g clip-path="url(#dyc)"><polygon points="{x},{y + h} {line} {x + w},{y + h}" fill="url(#dy)"/>'
               f'<polyline points="{line}" fill="none" stroke="{FLARE}" stroke-width="2" stroke-linejoin="round"/></g>')
    out.append(text("DYNO // LAST 31 DAYS", x, y - 10, "heading", 11, CHALK, 2))
    out.append(text(f"PEAK {max(vals)}", x + w, y - 10, "mono", 10, COOLANT, 1, "end"))
    style = (f".dyw{{transform-box:fill-box;transform-origin:left;animation:dyw 1.6s 1.2s cubic-bezier(.3,0,.2,1) both}}"
             f"@keyframes dyw{{from{{transform:scaleX(0)}}}}")
    return "".join(out), style


def fuel_mix(x, y, w, s):
    langs = s["langs"][:5]
    total = sum(v[0] for _, v in langs) or 1
    out = [text("FUEL MIX // LANGUAGES", x, y - 10, "heading", 11, CHALK, 2),
           f'<rect x="{x}" y="{y}" width="{w}" height="14" rx="3" fill="#07080b" stroke="{PLATE}" stroke-width="1"/>']
    if not langs:
        out.append(text("NO PUBLIC CODE YET", x, y + 38, "mono", 10, CHALK_FAINT, 1))
        return "".join(out)
    cx = x + 2
    for name, (size, color) in langs:
        seg = max(3, (w - 4) * size / total)
        out.append(f'<rect x="{cx:.1f}" y="{y + 2}" width="{seg:.1f}" height="10" fill="{color}"/>')
        cx += seg
    for i, (name, (size, color)) in enumerate(langs[:4]):
        lx = x + (i % 2) * (w / 2)
        ly = y + 38 + (i // 2) * 22
        out.append(f'<rect x="{lx}" y="{ly - 9}" width="10" height="10" rx="2" fill="{color}"/>')
        out.append(text(name.upper(), lx + 16, ly, "label", 11, CHALK, 0.8))
        out.append(text(f"{100 * size / total:.0f}%", lx + w / 2 - 14, ly, "mono", 10, CHALK_FAINT, 0, "end"))
    return "".join(out)


def readouts(x, y, s):
    items = [("STARS", s["stars"]), ("PULL REQ", s["prs"]), ("ISSUES", s["issues"]), ("REPOS", s["repos"])]
    out = [text("ODOMETER", x, y - 10, "heading", 11, CHALK, 2)]
    for i, (lab, val) in enumerate(items):
        ix = x + (i % 2) * 110
        iy = y + (i // 2) * 46
        segs, _ = seven_seg(f"{val:>3}"[-3:], ix, iy + 2, 20, COOLANT, SEG_OFF)
        out.append(segs)
        out.append(text(lab, ix, iy + 36, "mono", 9, CHALK_FAINT, 1.2))
    return "".join(out)


def dash(s):
    w, h = 980, 520
    cur, longest = streaks(s["days"], s["today"])
    year_total = sum(v for d, v in s["days"].items() if dt.date.fromisoformat(d) > s["today"] - dt.timedelta(days=365))
    body = [panel(w, h)]
    lights, light_style = shift_lights(w / 2, 32, min(1.0, cur / max(longest, 1)) if longest else 0.1)
    body.append(lights)
    body.append(gauge(190, 212, 128, year_total, nice_max(year_total, 50), "CONTRIBUTIONS", "LAST 365 DAYS"))
    body.append(gauge(490, 208, 142, cur, nice_max(longest, 10), "STREAK", f"DAYS // PEAK {longest}"))
    body.append(gauge(790, 212, 128, s["commits"], nice_max(s["commits"], 50), "COMMITS", "ALL TIME"))
    dy, dy_style = dyno(352, 412, 276, 76, s)
    body.append(dy)
    body.append(fuel_mix(48, 412, 250, s))
    body.append(readouts(704, 408, s))
    body.append(text(f"UPDATED {s['today'].isoformat()}", w - 36, 37, "mono", 8.5, CHALK_FAINT, 1, "end"))
    style = REDUCED_MOTION + light_style + dy_style
    title = (f"GitHub telemetry: {year_total} contributions in the last year, {cur}-day streak "
             f"(best {longest}), {s['commits']} commits")
    return svg_doc(w, h, "".join(body), title, style)


def main():
    login, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    s = collect(login)
    with open(os.path.join(out, "dash.svg"), "w", encoding="utf-8", newline="\n") as f:
        f.write(dash(s))
    print(f"{login}: {s['commits']} commits, {sum(s['days'].values())} contributions, {len(s['langs'])} languages")


if __name__ == "__main__":
    main()
