import colorsys
from pathlib import Path

from PIL import Image

from ..models import Color

BUCKETS = 36  # cubos de 10° de tono
MIN_SAT = 0.25
MIN_VAL = 0.20
MAX_COLORS = 3
MIN_SHARE = 0.15  # de los píxeles con color, no de todos
MIN_ABSOLUTE = 0.005  # al menos 0.5 % de la imagen, para no tomar ruido
MIN_SEPARATION = 3  # cubos (30°) entre candidatos

# ----------------------------------------------------------------------
# Público
# ----------------------------------------------------------------------


def extract_colors(path: str | Path) -> list[Color]:
    """Hasta MAX_COLORS tonos reales de la portada, del más al menos relevante."""
    try:
        with Image.open(path) as img:
            img = img.convert("RGB")
            img.thumbnail((96, 96))
            pixels = list(img.getdata())  # pyright: ignore[reportArgumentType]
    except (OSError, ValueError):
        return []
    weight = [0.0] * BUCKETS
    sums = [[0.0, 0.0, 0.0] for _ in range(BUCKETS)]
    for r, g, b in pixels:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if s < MIN_SAT or v < MIN_VAL:
            continue
        w = s * v
        i = int(h * BUCKETS) % BUCKETS
        weight[i] += w
        sums[i][0] += r * w
        sums[i][1] += g * w
        sums[i][2] += b * w
    colorful = sum(weight)  # base relativa: solo lo que tiene color
    if colorful == 0:
        return []
    smoothed = [
        weight[(i - 1) % BUCKETS] + weight[i] + weight[(i + 1) % BUCKETS]
        for i in range(BUCKETS)
    ]
    chosen: list[int] = []
    result: list[Color] = []
    while len(result) < MAX_COLORS:
        candidates = [
            i
            for i in range(BUCKETS)
            if all(
                min((i - c) % BUCKETS, (c - i) % BUCKETS) >= MIN_SEPARATION
                for c in chosen
            )
        ]
        if not candidates:
            break
        best = max(candidates, key=smoothed.__getitem__)
        if smoothed[best] / colorful < MIN_SHARE or smoothed[best] < MIN_ABSOLUTE * len(
            pixels
        ):
            break
        group = [(best - 1) % BUCKETS, best, (best + 1) % BUCKETS]
        total = sum(weight[i] for i in group)
        r, g, b = (round(sum(sums[i][c] for i in group) / total) for c in range(3))
        result.append(Color(r, g, b))
        chosen.append(best)
    return result
