import colorsys

from backend.models import Accent, Color, Colors

MIN_CONTRAST = 4.5
SAT_RANGE = (0.45, 0.90)
LIGHT_RANGE = (0.12, 0.92)
STEP = 0.02


def derive_accent(cover_colors: list[Color], colors: Colors) -> Accent | None:
    """Acento con el tono de la portada y contraste garantizado, o None si no hay color."""
    if not cover_colors:
        return None
    raw = cover_colors[0]
    surfaces = [
        _color(c) for c in (colors.player_bg, colors.content_bg, colors.surface)
    ]
    text = _color(colors.text)
    h, l, s = colorsys.rgb_to_hls(raw.r / 255, raw.g / 255, raw.b / 255)
    s = min(max(s, SAT_RANGE[0]), SAT_RANGE[1])
    dark = sum(_luminance(c) for c in surfaces) / len(surfaces) < 0.5
    toward = 1 if dark else -1  # hacia donde sube el contraste con los fondos
    primary = _fit(h, l, s, surfaces, toward)
    secondary = _fit(h, min(l + 0.10, LIGHT_RANGE[1]), s, surfaces, toward)
    tertiary = _fit(h, max(l - 0.15, LIGHT_RANGE[0]), s, [text], -toward)
    return Accent(primary, secondary, tertiary)


# ----------------------------------------------------------------------
# Privado
# ----------------------------------------------------------------------


def _color(value: Color | str) -> Color:
    """Acepta Color o texto, mientras Colors siga guardando strings."""
    return value if isinstance(value, Color) else Color.parse(value)


def _luminance(color: Color) -> float:
    def lin(v: int) -> float:
        c = v / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(color.r) + 0.7152 * lin(color.g) + 0.0722 * lin(color.b)


def _contrast(a: Color, b: Color) -> float:
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _from_hls(h: float, l: float, s: float) -> Color:
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return Color(round(r * 255), round(g * 255), round(b * 255))


def _fit(h: float, l: float, s: float, against: list[Color], direction: int) -> Color:
    """Mueve la luminosidad (no el tono) hasta cumplir el contraste con todos."""
    while LIGHT_RANGE[0] < l < LIGHT_RANGE[1]:
        color = _from_hls(h, l, s)
        if all(_contrast(color, a) >= MIN_CONTRAST for a in against):
            return color
        l += STEP * direction
    return _from_hls(
        h, min(max(l, 0.0), 1.0), s
    )  # no se alcanzó: el límite más cercano
