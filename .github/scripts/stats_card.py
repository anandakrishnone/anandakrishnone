"""Rebuild the profile stats card with a drop shadow.

The card comes from github-readme-streak-stats (streak-stats.demolab.com).
GitHub strips CSS from READMEs, so the shadow has to be part of the image.
This puts each card on a slightly bigger canvas with a soft shadow under it
and writes streak-light.svg and streak-dark.svg to the folder passed in.
"""

import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

SOURCE = "https://streak-stats.demolab.com/"
RADIUS = 20
CARD = {
    "user": "anandakrishnone",
    "mode": "weekly",
    "disable_animations": "true",
    "border_radius": RADIUS,
    "hide_longest_streak": "true",
    "card_width": 400,
}
THEMES = {
    "light": {
        "colors": {
            "background": "FFFFFF",
            "border": "D0D7DE",
            "stroke": "D0D7DE",
            "ring": "1A7F37",
            "fire": "1A7F37",
            "currStreakNum": "1F2328",
            "sideNums": "1F2328",
            "currStreakLabel": "1A7F37",
            "sideLabels": "1F2328",
            "dates": "59636E",
        },
        # shadow colour, opacity of the tight shadow, opacity of the soft one
        "shadow": ("#1F2328", 0.12, 0.24),
    },
    "dark": {
        "colors": {
            # a step lighter than the page, so the card sits above it
            "background": "161B22",
            "border": "30363D",
            "stroke": "30363D",
            "ring": "3FB950",
            "fire": "3FB950",
            "currStreakNum": "E6EDF3",
            "sideNums": "E6EDF3",
            "currStreakLabel": "3FB950",
            "sideLabels": "E6EDF3",
            "dates": "9198A1",
        },
        "shadow": ("#010409", 0.8, 0.9),
    },
}
# The soft shadow: how much it blurs and how far it drops below the card.
BLUR, DROP = 10, 6
# Room around the card so the shadow fades out before the edge of the image.
PAD_SIDE, PAD_TOP, PAD_BOTTOM = 2 * BLUR, 2 * BLUR - DROP, 2 * BLUR + DROP

UNSAFE = re.compile(r"<script|<foreignObject|<image|\son[a-z]+\s*=|javascript:", re.I)


def fetch(params):
    url = SOURCE + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "profile-stats-card"})
    for attempt in (1, 2, 3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8")
        except OSError as error:
            print(f"Attempt {attempt} failed: {error}", file=sys.stderr)
            if attempt < 3:
                time.sleep(15 * attempt)
    sys.exit("Could not fetch the card. The last published one stays up.")


def add_shadow(card, background, shadow):
    if "Total Contributions" not in card or "Week Streak" not in card:
        sys.exit("The card came back without the stats. The last published one stays up.")
    if UNSAFE.search(card):
        sys.exit("The card has unexpected content in it. Not publishing it.")

    root = re.search(r"<svg\b[^>]*>", card)
    view_box = re.search(r"viewBox=['\"]([^'\"]+)['\"]", root.group(0)).group(1)
    width, height = (float(n) for n in view_box.split()[2:])
    body = card[root.end():card.rindex("</svg>")]

    color, near, far = shadow
    full_width = width + 2 * PAD_SIDE
    full_height = height + PAD_TOP + PAD_BOTTOM
    # The filter works on a bigger area than the image, or the dropped shadow
    # gets cut off in a hard line near the top edge.
    margin = 3 * BLUR
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{full_width:g}" height="{full_height:g}" viewBox="0 0 {full_width:g} {full_height:g}">
  <defs>
    <filter id="card-shadow" filterUnits="userSpaceOnUse" x="{-margin}" y="{-margin}" width="{full_width + 2 * margin:g}" height="{full_height + 2 * margin:g}" color-interpolation-filters="sRGB">
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
  <rect x="{PAD_SIDE}" y="{PAD_TOP}" width="{width:g}" height="{height:g}" rx="{RADIUS}" fill="#{background}" filter="url(#card-shadow)"/>
  <svg x="{PAD_SIDE}" y="{PAD_TOP}" width="{width:g}" height="{height:g}" viewBox="{view_box}">{body}</svg>
</svg>
"""


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: stats_card.py OUTPUT_DIR")
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for name, theme in THEMES.items():
        card = fetch({**CARD, **theme["colors"]})
        svg = add_shadow(card, theme["colors"]["background"], theme["shadow"])
        (out / f"streak-{name}.svg").write_text(svg, encoding="utf-8")
        print(f"Wrote streak-{name}.svg")


if __name__ == "__main__":
    main()
