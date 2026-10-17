"""Renders a profile card (dark + light SVG) with a progress bar toward a contribution goal. Pure stdlib.

Live data needs GITHUB_TOKEN in the environment (in Actions: ${{ github.token }}); it only talks to api.github.com.
Usage:
  python render_card.py card.svg --user octocat --goal 1000 --name "Ada Lovelace" --tagline "Computer Science"
  python render_card.py card.svg --user octocat --contributions 420 --repos 12      # offline preview
  --image panel.png   optional picture (dark, any size) shown in a left panel; embedded as base64
Writes OUT and OUT with -light before the extension (card.svg -> card-light.svg).
"""
import argparse
import base64
import datetime as dt
import json
import os
import urllib.request
from html import escape

AMBER = "#e0a458"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"
DARK = dict(text="#e8eef2", key="#7fb6d4", dim="#7d8a96", bg="#0f1419", line="#2b3640")
LIGHT = dict(text="#1f2933", key="#1d5f8f", dim="#5b6b78", bg="#f6f8fa", line="#c5ced6")
PANEL_W = 300


def api(url, token, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "profile-card")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch_stats(user, token):
    """(total contributions, public repos, joined YYYY-MM); one aliased query per year (API caps a window at 1 year)."""
    info = api(f"https://api.github.com/users/{user}", token)
    created = dt.datetime.fromisoformat(info["created_at"].replace("Z", "+00:00"))
    now = dt.datetime.now(dt.timezone.utc)
    parts = []
    for year in range(created.year, now.year + 1):
        end = min(dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc), now)
        start = max(dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc), created)
        parts.append(f'y{year}: contributionsCollection(from: "{start:%Y-%m-%dT%H:%M:%SZ}", '
                     f'to: "{end:%Y-%m-%dT%H:%M:%SZ}") {{ contributionCalendar {{ totalContributions }} }}')
    data = api("https://api.github.com/graphql", token, {"query": f'{{ user(login: "{user}") {{ {" ".join(parts)} }} }}'})
    total = sum(v["contributionCalendar"]["totalContributions"] for v in data["data"]["user"].values())
    return total, info["public_repos"], created.strftime("%Y-%m")


def row(x, y, key, val):
    return (f'<text x="{x}" y="{y}"><tspan class="k">{escape(key)}</tspan>'
            f'<tspan class="v" x="{x + 120}">{escape(val)}</tspan></text>')


def render(a, stats, t):
    contributions, repos, joined = stats
    done = min(contributions, a.goal)
    x0 = 14 + (PANEL_W + 26 if a.image else 0)
    inner_w = 820 - x0 - 14
    panel = ""
    if a.image:
        with open(a.image, "rb") as f:
            png = base64.b64encode(f.read()).decode()
        panel = (f'<clipPath id="f"><rect x="14" y="14" width="{PANEL_W}" height="232" rx="4"/></clipPath>'
                 f'<image href="data:image/png;base64,{png}" x="14" y="14" width="{PANEL_W}" height="232" '
                 f'preserveAspectRatio="xMidYMid slice" clip-path="url(#f)"/>')
    bar = f'<rect x="{x0}" y="112" width="{inner_w}" height="6" rx="3" fill="{t["line"]}"/>' \
          f'<rect x="{x0}" y="112" width="{max(inner_w * done / a.goal, 4):.1f}" height="6" rx="3" fill="{AMBER}"/>'
    rows = [
        row(x0, 150, "Contributions", f"{contributions:,} of {a.goal:,}"),
        row(x0, 172, "Public repos", str(repos)),
        row(x0, 194, "Since", joined),
        row(x0, 216, "Goal left", f"{max(a.goal - contributions, 0):,}"),
    ]
    label = f"Profile card: {a.name}, {a.tagline}, {contributions} of {a.goal} contributions"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="820" height="260" viewBox="0 0 820 260" role="img" aria-label="{escape(label)}">
  <style>
    text {{ font-family: {MONO}; font-size: 13px; fill: {t["text"]}; }}
    .k {{ fill: {t["key"]}; font-weight: 700; }}
    .dim {{ fill: {t["dim"]}; font-size: 12px; }}
    .name {{ font-size: 20px; font-weight: 700; }}
    .dot {{ animation: pulse 1.8s ease-in-out infinite; }}
    @keyframes pulse {{ 50% {{ opacity: .4; }} }}
    @media (prefers-reduced-motion: reduce) {{ .dot {{ animation: none; }} }}
  </style>
  <rect x=".5" y=".5" width="819" height="259" rx="8" fill="{t["bg"]}" stroke="{t["line"]}"/>
  {panel}
  <text class="name" x="{x0}" y="50">{escape(a.name)}</text>
  <text class="dim" x="{x0}" y="72">{escape(a.tagline)} · github.com/{escape(a.user)}</text>
  <circle class="dot" cx="{x0 + inner_w * done / a.goal:.1f}" cy="115" r="4" fill="{AMBER}"/>
  {bar}
  {chr(10).join(rows)}
</svg>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--user", required=True)
    ap.add_argument("--name", default="")
    ap.add_argument("--tagline", default="")
    ap.add_argument("--goal", type=int, default=1000, help="contributions that fill the bar")
    ap.add_argument("--image")
    ap.add_argument("--contributions", type=int)
    ap.add_argument("--repos", type=int)
    a = ap.parse_args()
    a.name = a.name or a.user
    a.goal = max(a.goal, 1)
    if a.contributions is not None and a.repos is not None:
        stats = (a.contributions, a.repos, "preview")
    else:
        stats = fetch_stats(a.user, os.environ["GITHUB_TOKEN"])
    root, ext = os.path.splitext(a.out)
    for path, theme in ((a.out, DARK), (f"{root}-light{ext}", LIGHT)):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(render(a, stats, theme))


if __name__ == "__main__":
    main()
