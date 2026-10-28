"""Render the profile's stat cards as SVG (dark + light), from the GitHub GraphQL API.

Runs in .github/workflows/profile-assets.yml. Standard library only.
    GH_TOKEN=... python scripts/stats.py <login> <out_dir>

With the default Actions token only public data is counted. A classic PAT in the
METRICS_TOKEN secret (scopes: read:user, repo) adds private-repo languages.
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from html import escape

API = "https://api.github.com/graphql"

THEMES = {
    "dark": dict(bg="#0a0b0f", panel="#161923", border="#2a2f3e", text="#f2f0ec",
                 dim="#a8afc4", faint="#6f778c", accent="#f800e0", accent2="#00e5d0", grid="#1e2230"),
    "light": dict(bg="#f7f5f0", panel="#ece9e2", border="#d6d2c8", text="#0a0b0f",
                  dim="#3a4152", faint="#6f778c", accent="#c000ae", accent2="#009e8f", grid="#e2ded5"),
}
SANS = "'Archivo','Segoe UI',Ubuntu,'Helvetica Neue',Arial,sans-serif"
MONO = "'Martian Mono','SFMono-Regular',Consolas,'Liberation Mono',monospace"


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
            langs[n] = (size + e["size"], color or "#a8afc4")
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


def frame(w, h, t, title, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10" fill="{t['bg']}" stroke="{t['border']}"/>
<rect x="0.5" y="0.5" width="6" height="{h - 1}" rx="3" fill="{t['accent']}"/>
<text x="26" y="36" font-family="{SANS}" font-size="15" font-weight="800" letter-spacing="2.4" fill="{t['text']}">{escape(title.upper())}</text>
<path d="M{w - 40} 22 l3 8 8 3 -8 3 -3 8 -3 -8 -8 -3 8 -3z" fill="{t['accent']}"/>
{body}
</svg>"""


def stats_card(s, t):
    rows = [("Total stars", s["stars"]), ("Commits", s["commits"]), ("Pull requests", s["prs"]),
            ("Issues", s["issues"]), ("Contributed to", s["contributed"]), ("Repositories", s["repos"])]
    body = []
    for i, (label, val) in enumerate(rows):
        col, row = i % 2, i // 2
        x, y = 26 + col * 230, 78 + row * 42
        body.append(f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="11" letter-spacing="1" fill="{t["dim"]}">{label.upper()}</text>')
        body.append(f'<text x="{x}" y="{y + 22}" font-family="{SANS}" font-size="20" font-weight="800" fill="{t["text"]}">{val:,}</text>')
    return frame(480, 210, t, "GitHub stats", "\n".join(body))


def langs_card(s, t):
    langs = s["langs"][:6]
    total = sum(v[0] for _, v in langs) or 1
    body = []
    if not langs:
        body.append(f'<text x="26" y="110" font-family="{MONO}" font-size="12" fill="{t["dim"]}">NO PUBLIC CODE YET</text>')
    x = 26
    bar_w = 300 - 52
    for name, (size, color) in langs:
        w = max(2, bar_w * size / total)
        body.append(f'<rect x="{x:.1f}" y="58" width="{w:.1f}" height="10" fill="{color}"/>')
        x += w
    for i, (name, (size, color)) in enumerate(langs):
        col, row = i % 2, i // 2
        cx, cy = 30 + col * 128, 98 + row * 34
        body.append(f'<circle cx="{cx}" cy="{cy - 4}" r="5" fill="{color}"/>')
        body.append(f'<text x="{cx + 12}" y="{cy}" font-family="{SANS}" font-size="12" font-weight="700" fill="{t["text"]}">{escape(name)}</text>')
        body.append(f'<text x="{cx + 12}" y="{cy + 14}" font-family="{MONO}" font-size="10" fill="{t["dim"]}">{100 * size / total:.1f}%</text>')
    return frame(300, 210, t, "Top languages", "\n".join(body))


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


def streak_card(s, t):
    cur, longest = streaks(s["days"], s["today"])
    total = sum(s["days"].values())
    cols = [("Total contributions", total, 26), ("Current streak", cur, 300), ("Longest streak", longest, 560)]
    body = []
    for label, val, x in cols:
        big = label == "Current streak"
        if big:
            body.append(f'<circle cx="{x + 60}" cy="118" r="44" fill="none" stroke="{t["accent"]}" stroke-width="5"/>')
            body.append(f'<text x="{x + 60}" y="128" text-anchor="middle" font-family="{SANS}" font-size="30" font-weight="800" fill="{t["text"]}">{val}</text>')
            body.append(f'<text x="{x + 60}" y="188" text-anchor="middle" font-family="{MONO}" font-size="11" letter-spacing="1" fill="{t["accent"]}">{label.upper()}</text>')
        else:
            body.append(f'<text x="{x + 90}" y="128" text-anchor="middle" font-family="{SANS}" font-size="30" font-weight="800" fill="{t["text"]}">{val:,}</text>')
            body.append(f'<text x="{x + 90}" y="160" text-anchor="middle" font-family="{MONO}" font-size="11" letter-spacing="1" fill="{t["dim"]}">{label.upper()}</text>')
    body.append(f'<line x1="250" y1="78" x2="250" y2="190" stroke="{t["border"]}"/>')
    body.append(f'<line x1="500" y1="78" x2="500" y2="190" stroke="{t["border"]}"/>')
    return frame(780, 210, t, "Streak", "\n".join(body))


def activity_card(s, t, span=31):
    today = s["today"]
    pts = [(today - dt.timedelta(days=span - 1 - i)) for i in range(span)]
    vals = [s["days"].get(d.isoformat(), 0) for d in pts]
    w, h = 780, 260
    left, right, top, bottom = 56, 24, 60, 210
    peak = max(max(vals), 4)
    sx = (w - left - right) / (span - 1)
    xy = [(left + i * sx, bottom - (bottom - top) * v / peak) for i, v in enumerate(vals)]
    body = []
    for k in range(5):
        y = bottom - (bottom - top) * k / 4
        body.append(f'<line x1="{left}" y1="{y:.1f}" x2="{w - right}" y2="{y:.1f}" stroke="{t["grid"]}"/>')
        body.append(f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end" font-family="{MONO}" font-size="10" fill="{t["faint"]}">{round(peak * k / 4)}</text>')
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in xy)
    body.append(f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["accent"]}" stop-opacity=".45"/><stop offset="1" stop-color="{t["accent"]}" stop-opacity="0"/></linearGradient></defs>')
    body.append(f'<polygon points="{left},{bottom} {line} {w - right},{bottom}" fill="url(#g)"/>')
    body.append(f'<polyline points="{line}" fill="none" stroke="{t["accent"]}" stroke-width="2.5" stroke-linejoin="round"/>')
    for (x, y), v in zip(xy, vals):
        if v:
            body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{t["bg"]}" stroke="{t["accent2"]}" stroke-width="2"/>')
    for i in range(0, span, 5):
        body.append(f'<text x="{xy[i][0]:.1f}" y="{bottom + 22}" text-anchor="middle" font-family="{MONO}" font-size="10" fill="{t["faint"]}">{pts[i].strftime("%b %d").upper()}</text>')
    return frame(w, h, t, f"Last {span} days", "\n".join(body))


def main():
    login, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    s = collect(login)
    cards = {"stats": stats_card, "langs": langs_card, "streak": streak_card, "activity": activity_card}
    for name, fn in cards.items():
        for mode, theme in THEMES.items():
            with open(os.path.join(out, f"{name}-{mode}.svg"), "w", encoding="utf-8") as f:
                f.write(fn(s, theme))
    print(f"{login}: {s['commits']} commits, {sum(s['days'].values())} contributions, {len(s['langs'])} languages")


if __name__ == "__main__":
    main()
