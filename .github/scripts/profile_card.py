"""Build the profile cards: the about section and the streak stats.

The about text is in HEADLINE, INTRO, BUILT and FOOTER below.

GitHub strips CSS from READMEs, so the look (cards, shadows, type) has to be
part of the images. There are two columns, each its own image, so they sit
side by side on a desktop and stack on a phone:
  left:  the intro and the streak stats
  right: what I built and run at AiRA
Both come out the same height, so their tops line up. The stats come from
github-readme-streak-stats (streak-stats.demolab.com), and the workflow
rebuilds the images every 6 hours.

Writes profile-left-{light,dark}.svg and profile-right-{light,dark}.svg to the
folder passed in. Icons are Octicons (MIT, Copyright (c) GitHub Inc.).
"""

import re
import sys
import time
import urllib.parse
import urllib.request
from html import escape
from pathlib import Path

# The about text. Lines are broken by hand so they fit the cards in any common
# system font. `code` is set in monospace and **bold** in bold.
HEADLINE = [
    "I’m obsessive about the code",
    "I write and I know that.",
]
INTRO = [
    "The kind who’ll leave a PR comment",
    "asking to rename a request-body alias",
    "from `sp` to `spk`, not because anyone",
    "asked, but because `spk` feels right cause",
    "I want my codebase to be **PERFECT**.",
]
BUILT_TITLE = "What I built and run at AiRA"
BUILT = [
    ("server", ["The backend, from the first commit, in",
                "FastAPI on MongoDB, Redis and Qdrant"]),
    ("cloud", ["Our whole Azure infrastructure on private",
               "networking, which I am managing alone"]),
    ("git-merge", ["The CI/CD, where every merged PR",
                   "deploys to its own slot first and is then",
                   "swapped into production, so releases",
                   "cause no downtime"]),
    ("pulse", ["Observability platform (opera.airaai.in)",
               "with token usage, cost tracking"]),
    ("plug", ["An MCP server with OAuth 2.1 that lets",
              "ChatGPT and Claude work with our",
              "company’s context"]),
]
FOOTER = ["All of it is in private repos.", "But you can ask me about any of it."]

SOURCE = "https://streak-stats.demolab.com/"
RADIUS = 20
STATS = {
    "user": "anandakrishnone",
    "mode": "weekly",
    "disable_animations": "true",
    "border_radius": RADIUS,
    "hide_longest_streak": "true",
}
THEMES = {
    "light": {
        "card": "#FFFFFF",
        "border": "#D0D7DE",
        "text": "#1F2328",
        "soft": "#424A53",
        "muted": "#59636E",
        "accent": "#1A7F37",
        "tile": 0.1,
        # shadow colour, opacity of the tight shadow, opacity of the soft one
        "shadow": ("#1F2328", 0.12, 0.24),
    },
    "dark": {
        # a step lighter than the page, so the cards sit above it
        "card": "#161B22",
        "border": "#30363D",
        "text": "#E6EDF3",
        "soft": "#C9D1D9",
        "muted": "#9198A1",
        "accent": "#3FB950",
        "tile": 0.12,
        "shadow": ("#010409", 0.8, 0.9),
    },
}

FONT = '-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif'
MONO = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace'

# The soft shadow: how much it blurs and how far it drops below a card.
BLUR, DROP = 10, 6
# Room around the cards so the shadow fades out before the edge of the image.
PAD_SIDE, PAD_TOP, PAD_BOTTOM = 2 * BLUR, 2 * BLUR - DROP, 2 * BLUR + DROP
# Two columns fit in GitHub's 838px README column, with the same 40px gutter
# between them as between the cards in a column.
CARD_WIDTH = 378
CARD_GAP = 2 * PAD_SIDE
STATS_MIN_HEIGHT = 195
# Inside the cards
PAD = 28
TEXT_X = PAD + 26 + 14  # list text starts after the icon tile
ITEM_GAP = 14

ICONS = {
    "server": "M1.75 1h12.5c.966 0 1.75.784 1.75 1.75v4c0 .372-.116.717-.314 1 .198.283.314.628.314 1v4a1.75 1.75 0 0 1-1.75 1.75H1.75A1.75 1.75 0 0 1 0 12.75v-4c0-.358.109-.707.314-1a1.739 1.739 0 0 1-.314-1v-4C0 1.784.784 1 1.75 1ZM1.5 2.75v4c0 .138.112.25.25.25h12.5a.25.25 0 0 0 .25-.25v-4a.25.25 0 0 0-.25-.25H1.75a.25.25 0 0 0-.25.25Zm.25 5.75a.25.25 0 0 0-.25.25v4c0 .138.112.25.25.25h12.5a.25.25 0 0 0 .25-.25v-4a.25.25 0 0 0-.25-.25ZM7 4.75A.75.75 0 0 1 7.75 4h4.5a.75.75 0 0 1 0 1.5h-4.5A.75.75 0 0 1 7 4.75ZM7.75 10h4.5a.75.75 0 0 1 0 1.5h-4.5a.75.75 0 0 1 0-1.5ZM3 4.75A.75.75 0 0 1 3.75 4h.5a.75.75 0 0 1 0 1.5h-.5A.75.75 0 0 1 3 4.75ZM3.75 10h.5a.75.75 0 0 1 0 1.5h-.5a.75.75 0 0 1 0-1.5Z",
    "cloud": "M2 7.25A5.225 5.225 0 0 1 7.25 2a5.222 5.222 0 0 1 4.767 3.029A4.472 4.472 0 0 1 16 9.5c0 2.505-1.995 4.5-4.5 4.5h-8A3.474 3.474 0 0 1 0 10.5c0-1.41.809-2.614 2.001-3.17Zm1.54.482a.75.75 0 0 1-.556.832c-.86.22-1.484.987-1.484 1.936 0 1.124.876 2 2 2h8c1.676 0 3-1.324 3-3s-1.324-3-3-3a.75.75 0 0 1-.709-.504A3.72 3.72 0 0 0 7.25 3.5C5.16 3.5 3.5 5.16 3.5 7.25c.002.146.014.292.035.436l.004.036.001.008Z",
    "git-merge": "M5.45 5.154A4.25 4.25 0 0 0 9.25 7.5h1.378a2.251 2.251 0 1 1 0 1.5H9.25A5.734 5.734 0 0 1 5 7.123v3.505a2.25 2.25 0 1 1-1.5 0V5.372a2.25 2.25 0 1 1 1.95-.218ZM4.25 13.5a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm8.5-4.5a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5ZM5 3.25a.75.75 0 1 0 0 .005V3.25Z",
    "pulse": "M6 2c.306 0 .582.187.696.471L10 10.731l1.304-3.26A.751.751 0 0 1 12 7h3.25a.75.75 0 0 1 0 1.5h-2.742l-1.812 4.528a.751.751 0 0 1-1.392 0L6 4.77 4.696 8.03A.75.75 0 0 1 4 8.5H.75a.75.75 0 0 1 0-1.5h2.742l1.812-4.529A.751.751 0 0 1 6 2Z",
    "plug": "M4 8H2.5a1 1 0 0 0-1 1v5.25a.75.75 0 0 1-1.5 0V9a2.5 2.5 0 0 1 2.5-2.5H4V5.133a1.75 1.75 0 0 1 1.533-1.737l2.831-.353.76-.913c.332-.4.825-.63 1.344-.63h.782c.966 0 1.75.784 1.75 1.75V4h2.25a.75.75 0 0 1 0 1.5H13v4h2.25a.75.75 0 0 1 0 1.5H13v.75a1.75 1.75 0 0 1-1.75 1.75h-.782c-.519 0-1.012-.23-1.344-.63l-.761-.912-2.83-.354A1.75 1.75 0 0 1 4 9.867Zm6.276-4.91-.95 1.14a.753.753 0 0 1-.483.265l-3.124.39a.25.25 0 0 0-.219.248v4.734c0 .126.094.233.219.249l3.124.39a.752.752 0 0 1 .483.264l.95 1.14a.25.25 0 0 0 .192.09h.782a.25.25 0 0 0 .25-.25v-8.5a.25.25 0 0 0-.25-.25h-.782a.25.25 0 0 0-.192.09Z",
    "lock": "M4 4a4 4 0 0 1 8 0v2h.25c.966 0 1.75.784 1.75 1.75v5.5A1.75 1.75 0 0 1 12.25 15h-8.5A1.75 1.75 0 0 1 2 13.25v-5.5C2 6.784 2.784 6 3.75 6H4Zm8.25 3.5h-8.5a.25.25 0 0 0-.25.25v5.5c0 .138.112.25.25.25h8.5a.25.25 0 0 0 .25-.25v-5.5a.25.25 0 0 0-.25-.25ZM10.5 6V4a2.5 2.5 0 1 0-5 0v2Z",
}

UNSAFE = re.compile(r"<script|<foreignObject|<image|\son[a-z]+\s*=|javascript:", re.I)


def fetch(params):
    url = SOURCE + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "profile-card"})
    for attempt in (1, 2, 3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8")
        except OSError as error:
            print(f"Attempt {attempt} failed: {error}", file=sys.stderr)
            if attempt < 3:
                time.sleep(15 * attempt)
    sys.exit("Could not fetch the stats. The last published images stay up.")


def stats_colors(t):
    """The streak card's colour parameters, from the theme."""
    hexes = {
        "background": t["card"], "border": t["border"], "stroke": t["border"],
        "ring": t["accent"], "fire": t["accent"], "currStreakLabel": t["accent"],
        "currStreakNum": t["text"], "sideNums": t["text"], "sideLabels": t["text"],
        "dates": t["muted"],
    }
    return {key: value.lstrip("#") for key, value in hexes.items()}


def rich(line, strong):
    """One line of text, with `code` and **bold** (in the strong colour) as tspans."""
    out = []
    for part in re.split(r"(`[^`]+`|\*\*[^*]+\*\*)", line):
        if part.startswith("`"):
            out.append(f'<tspan class="mono" font-size="15">{escape(part[1:-1])}</tspan>')
        elif part.startswith("**"):
            out.append(f'<tspan font-weight="700" fill="{strong}">{escape(part[2:-2])}</tspan>')
        else:
            out.append(escape(part))
    return "".join(out)


def icon(name, x, y, size, color):
    return f'<path transform="translate({x:g} {y:g}) scale({size / 16:g})" fill="{color}" d="{ICONS[name]}"/>'


def hairline(y, t):
    return f'<rect x="{PAD}" y="{y:g}" width="{CARD_WIDTH - 2 * PAD}" height="1" fill="{t["border"]}"/>'


def intro(t):
    """The intro card's contents, in card coordinates, and the card's height."""
    parts = []
    y = PAD
    for line in HEADLINE:  # 22px on 29px lines
        parts.append(f'<text x="{PAD}" y="{y + 21:g}" font-size="22" font-weight="600" fill="{t["text"]}">{escape(line)}</text>')
        y += 29
    y += 12
    for line in INTRO:  # 16px on 25px lines
        parts.append(f'<text x="{PAD}" y="{y + 17:g}" font-size="16" fill="{t["soft"]}">{rich(line, t["text"])}</text>')
        y += 25
    return parts, y + PAD


def built(t, extra=0):
    """The AiRA card's contents and height. `extra` spreads out the items."""
    parts = []
    y = PAD
    parts.append(f'<text x="{PAD}" y="{y + 15:g}" font-size="14" font-weight="700" fill="{t["accent"]}">{escape(BUILT_TITLE)}</text>')
    y += 21 + 14
    gap = ITEM_GAP + extra / (len(BUILT) - 1)
    for i, (name, lines) in enumerate(BUILT):
        if i:
            y += gap
        parts.append(f'<rect x="{PAD}" y="{y:g}" width="26" height="26" rx="7" fill="{t["accent"]}" fill-opacity="{t["tile"]}"/>')
        parts.append(icon(name, PAD + 6, y + 6, 14, t["accent"]))
        for j, line in enumerate(lines):  # 14px on 21px lines, the first level with the tile
            parts.append(f'<text x="{TEXT_X}" y="{y + 18 + 21 * j:g}" font-size="14" fill="{t["soft"]}">{rich(line, t["text"])}</text>')
        y += max(26, 3 + 21 * len(lines))
    y += 22
    parts.append(hairline(y, t))
    y += 1 + 20
    parts.append(icon("lock", PAD, y + 3, 13, t["muted"]))
    for line in FOOTER:  # 13px on 19px lines
        parts.append(f'<text x="{PAD + 21}" y="{y + 13.5:g}" font-size="13" fill="{t["muted"]}">{escape(line)}</text>')
        y += 19
    return parts, y + PAD


def layout():
    """Card heights that make both columns the same height."""
    intro_height = intro(THEMES["light"])[1]
    built_height = built(THEMES["light"])[1]
    stats_height = max(STATS_MIN_HEIGHT, built_height - intro_height - CARD_GAP)
    column = intro_height + CARD_GAP + stats_height
    return intro_height, stats_height, column - built_height


def stats_card(card):
    """The streak card's inside and viewBox, after checking it's what we expect."""
    if "Total Contributions" not in card or "Week Streak" not in card:
        sys.exit("The stats card came back without the stats. The last published images stay up.")
    if UNSAFE.search(card):
        sys.exit("The stats card has unexpected content in it. Not publishing it.")
    root = re.search(r"<svg\b[^>]*>", card)
    view_box = re.search(r"viewBox=['\"]([^'\"]+)['\"]", root.group(0)).group(1)
    return card[root.end():card.rindex("</svg>")], view_box


def card(t, y, height, inside):
    """A card at height y of the column: its shadow, its border and what's in it."""
    return [
        f'<rect x="{PAD_SIDE}" y="{y:g}" width="{CARD_WIDTH}" height="{height:g}" rx="{RADIUS}" fill="{t["card"]}" filter="url(#card-shadow)"/>',
        f'<rect x="{PAD_SIDE + 0.5}" y="{y + 0.5:g}" width="{CARD_WIDTH - 1}" height="{height - 1:g}" rx="{RADIUS}" fill="{t["card"]}" stroke="{t["border"]}"/>',
        f'<g transform="translate({PAD_SIDE} {y:g})">',
        *("  " + part for part in inside),
        "</g>",
    ]


def image(t, column_height, body):
    width = CARD_WIDTH + 2 * PAD_SIDE
    height = PAD_TOP + column_height + PAD_BOTTOM
    color, near, far = t["shadow"]
    # The filter works on a bigger area than the image, or the dropped shadow
    # gets cut off in a hard line near the top edge.
    margin = 3 * BLUR
    lines = "\n  ".join(body)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height:g}" viewBox="0 0 {width} {height:g}">
  <style>
    text {{ font-family: {FONT}; }}
    .mono {{ font-family: {MONO}; }}
  </style>
  <defs>
    <filter id="card-shadow" filterUnits="userSpaceOnUse" x="{-margin}" y="{-margin}" width="{width + 2 * margin}" height="{height + 2 * margin:g}" color-interpolation-filters="sRGB">
      <feGaussianBlur in="SourceAlpha" stdDeviation="1.5"/>
      <feOffset dy="1" result="near"/>
      <feGaussianBlur in="SourceAlpha" stdDeviation="{BLUR}"/>
      <feOffset dy="{DROP}" result="far"/>
      <feFlood flood-color="{color}" flood-opacity="{far}"/>
      <feComposite in2="far" operator="in" result="far-shadow"/>
      <feFlood flood-color="{color}" flood-opacity="{near}"/>
      <feComposite in2="near" operator="in" result="near-shadow"/>
      <feMerge>
        <feMergeNode in="far-shadow"/>
        <feMergeNode in="near-shadow"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  {lines}
</svg>
"""


def left(stats, t, intro_height, stats_height):
    """The intro card, then the streak card under it."""
    stats_body, view_box = stats_card(stats)
    stats_y = PAD_TOP + intro_height + CARD_GAP
    body = card(t, PAD_TOP, intro_height, intro(t)[0])
    body.append(f'<rect x="{PAD_SIDE}" y="{stats_y:g}" width="{CARD_WIDTH}" height="{stats_height:g}" rx="{RADIUS}" fill="{t["card"]}" filter="url(#card-shadow)"/>')
    body.append(f'<svg x="{PAD_SIDE}" y="{stats_y:g}" width="{CARD_WIDTH}" height="{stats_height:g}" viewBox="{view_box}">{stats_body}</svg>')
    return image(t, intro_height + CARD_GAP + stats_height, body)


def right(t, extra):
    """The card with what I built and run at AiRA."""
    parts, height = built(t, extra)
    return image(t, height, card(t, PAD_TOP, height, parts))


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: profile_card.py OUTPUT_DIR")
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    intro_height, stats_height, extra = layout()
    for name, theme in THEMES.items():
        params = {**STATS, **stats_colors(theme), "card_width": CARD_WIDTH, "card_height": stats_height}
        stats = fetch(params)
        (out / f"profile-left-{name}.svg").write_text(left(stats, theme, intro_height, stats_height), encoding="utf-8")
        (out / f"profile-right-{name}.svg").write_text(right(theme, extra), encoding="utf-8")
        print(f"Wrote profile-left-{name}.svg and profile-right-{name}.svg")


if __name__ == "__main__":
    main()
