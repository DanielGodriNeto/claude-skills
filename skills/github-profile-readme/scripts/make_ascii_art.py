"""Optional: turns any image into a dark-theme ASCII picture (PNG) for the card's left panel.

Dense character = bright pixel on a dark background. Needs Pillow + numpy (the nightly card only reads the PNG).
Usage: python make_ascii_art.py input.jpg output.png [--cols 120] [--invert]
Use --invert for dark ink on a white drawing. Set FONT to any monospaced .ttf on your machine.
"""
import argparse

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT, SIZE = r"C:\Windows\Fonts\consolab.ttf", 10   # ponytail: Windows path; change for Linux/macOS
CHARS = " .:-=+*#%@"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--cols", type=int, default=120)
    ap.add_argument("--invert", action="store_true")
    a = ap.parse_args()
    font = ImageFont.truetype(FONT, SIZE)
    cw = round(font.getlength("M"))
    img = Image.open(a.src).convert("L")
    rows = round(a.cols * img.height / img.width * cw / SIZE)
    g = np.asarray(img.resize((a.cols, rows), Image.BOX), dtype=np.float32) / 255.0
    if a.invert:
        g = 1 - g
    lo, hi = np.percentile(g, 4), np.percentile(g, 97)
    g = np.clip((g - lo) / max(hi - lo, 1e-6), 0, 1)
    out = Image.new("RGB", (a.cols * cw, rows * SIZE), (15, 20, 25))
    d = ImageDraw.Draw(out)
    for y in range(rows):
        for x in range(a.cols):
            v = g[y, x]
            ch = CHARS[min(int(v * len(CHARS)), len(CHARS) - 1)]
            if ch != " ":
                d.text((x * cw, y * SIZE), ch, font=font, fill=(int(60 + 172 * v), int(76 + 162 * v), int(90 + 152 * v)))
    out.save(a.out, optimize=True)


if __name__ == "__main__":
    main()
