"""Draw the application icon: a diffraction peak on an accent tile.

    python tools/make_icon.py

Writes ``icon.png`` (256 px) and a multi-size ``icon.ico`` into the package data.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "src" / "rietesd_demo" / "data"
SIZE = 1024  # drawn large, downsampled for smooth edges
TOP, BOTTOM = (0, 120, 212), (0, 62, 146)  # accent gradient


def main() -> None:
    tile = Image.new("RGBA", (SIZE, SIZE))
    for y in range(SIZE):
        t = y / (SIZE - 1)
        colour = tuple(round(a + (b - a) * t) for a, b in zip(TOP, BOTTOM, strict=True))
        ImageDraw.Draw(tile).line([(0, y), (SIZE, y)], fill=(*colour, 255))
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=220, fill=255)
    icon = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    icon.paste(tile, (0, 0), mask)

    draw = ImageDraw.Draw(icon)
    left, right, base, top = 150, SIZE - 150, 760, 220

    def curve(x: float) -> float:  # a tall peak and a small neighbour
        u = (x - left) / (right - left)
        y = math.exp(-(((u - 0.42) / 0.075) ** 2)) + 0.28 * math.exp(-(((u - 0.74) / 0.06) ** 2))
        return base - (base - top) * y

    points = [(x, curve(x)) for x in range(left, right + 1, 4)]
    draw.line(points, fill=(255, 255, 255, 255), width=46, joint="curve")
    for x, y in (points[0], points[-1]):
        draw.ellipse([x - 23, y - 23, x + 23, y + 23], fill=(255, 255, 255, 255))
    draw.line([(left, 860), (right, 860)], fill=(255, 255, 255, 150), width=22)

    OUT.mkdir(parents=True, exist_ok=True)
    icon.resize((256, 256), Image.LANCZOS).save(OUT / "icon.png")
    icon.save(OUT / "icon.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    print(f"wrote {OUT / 'icon.png'} and icon.ico")


if __name__ == "__main__":
    main()
