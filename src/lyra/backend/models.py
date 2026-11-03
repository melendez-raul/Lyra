import json
import re
from dataclasses import asdict, dataclass, field, fields
from typing import Literal

# ──────────────────────────────────────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────────────────────────────────────

_RGB = re.compile(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)")

FONT_FAMILY = [
    "Inter",
    "Segoe UI",  # Windows
    "SF Pro Text",  # macOS
    "Roboto",  # Android / muchos Linux
    "Cantarell",  # GNOME
    "Noto Sans",
    "Noto Sans CJK JP",  # CJK y símbolos que Inter no tiene
    "Noto Sans CJK SC",
    "Noto Sans CJK KR",
    "Yu Gothic",  # Windows, japonés
    "Microsoft YaHei",  # Windows, chino
    "Malgun Gothic",  # Windows, coreano
    "Hiragino Sans",  # macOS, japonés
    "sans-serif",
]

PlaybackState = Literal["loading", "playing", "paused", "stopped", "error", "closed"]


# ──────────────────────────────────────────────────────────────────────────────
# Color
# ──────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int

    def __post_init__(self) -> None:
        if not all(0 <= c <= 255 for c in (self.r, self.g, self.b)):
            raise ValueError(f"Color fuera de rango: {(self.r, self.g, self.b)}")

    @classmethod
    def parse(cls, text: str) -> "Color":
        """Acepta '#rrggbb' o 'rgb(r, g, b)'."""
        text = text.strip()
        if len(text) == 7 and text.startswith("#"):
            return cls(int(text[1:3], 16), int(text[3:5], 16), int(text[5:7], 16))
        match = _RGB.fullmatch(text)
        if not match:
            raise ValueError(f"Color inválido: {text}")
        return cls(*map(int, match.groups()))

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def to_qss(self, alpha: int | None = None) -> str:
        if alpha is None:
            return f"rgb({self.r}, {self.g}, {self.b})"
        return f"rgba({self.r}, {self.g}, {self.b}, {alpha})"


# ──────────────────────────────────────────────────────────────────────────────
# Biblioteca: letras, metadatos y pistas
# ──────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class LyricLine:
    time: float
    text: str

    def to_dict(self) -> dict:
        return {"time": self.time, "text": self.text}

    @classmethod
    def from_dict(cls, data: dict) -> "LyricLine":
        return cls(time=float(data["time"]), text=str(data["text"]))


@dataclass
class Metadata:
    path: str
    cover_path: str | None
    title: str
    artist: list[str]
    album: str
    album_artist: list[str]
    track_number: int | None
    lyrics: list[LyricLine]


@dataclass
class Track:
    index: int
    path: str
    title: str
    artist: list[str]
    album: str
    album_artist: list[str]
    cover_path: str | None
    track_number: int | None
    lyrics: list[LyricLine] = field(default_factory=list)
    cover_colors: list[Color] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Track":
        """`lyrics` puede venir como JSON (str) o lista; `cover_colors` como hex."""
        lyrics = data.get("lyrics") or []
        if isinstance(lyrics, str):
            lyrics = json.loads(lyrics)
        return cls(
            index=data["index"],
            path=data["path"],
            title=data["title"],
            artist=data["artist"],
            album=data["album"],
            album_artist=data["album_artist"],
            cover_path=data["cover_path"],
            track_number=data["track_number"],
            lyrics=[LyricLine.from_dict(item) for item in lyrics],
            cover_colors=[Color.parse(c) for c in data.get("cover_colors") or []],
        )


# ──────────────────────────────────────────────────────────────────────────────
# Reproducción
# ──────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class PlaybackStatus:
    state: PlaybackState
    track: str | None
    time: float
    duration: float | None


@dataclass
class Playlist:
    tracks: list[Track]
    current_index: int = 0
    loop: bool = False

    @property
    def current(self) -> Track | None:
        if not 0 <= self.current_index < len(self.tracks):
            return None
        return self.tracks[self.current_index]

    def select(self, index: int) -> Track | None:
        if not 0 <= index < len(self.tracks):
            return None
        self.current_index = index
        return self.current

    def next(self) -> Track | None:
        return self._step(+1)

    def previous(self) -> Track | None:
        return self._step(-1)

    def _step(self, delta: int) -> Track | None:
        """Avanza o retrocede; con loop da la vuelta en los extremos."""
        if not self.tracks:
            return None
        target = self.current_index + delta
        if self.loop:
            target %= len(self.tracks)
        elif not 0 <= target < len(self.tracks):
            return None
        self.current_index = target
        return self.current


# ──────────────────────────────────────────────────────────────────────────────
# Tema: colores, fuentes y acentos
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class Colors:
    transparency: int = 80
    player_bg: Color = field(default_factory=lambda: Color(16, 16, 25))
    content_bg: Color = field(default_factory=lambda: Color(20, 20, 31))
    surface: Color = field(default_factory=lambda: Color(30, 30, 43))
    hover: Color = field(default_factory=lambda: Color(41, 41, 58))
    text: Color = field(default_factory=lambda: Color(244, 241, 250))
    info: Color = field(default_factory=lambda: Color(181, 177, 197))
    inactive: Color = field(default_factory=lambda: Color(91, 88, 107))
    primary: Color = field(default_factory=lambda: Color(139, 92, 246))
    secondary: Color = field(default_factory=lambda: Color(167, 139, 250))
    tertiary: Color = field(default_factory=lambda: Color(109, 40, 217))

    def to_dict(self) -> dict:
        return {
            f.name: v.to_hex() if isinstance(v := getattr(self, f.name), Color) else v
            for f in fields(self)
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Colors":
        default = cls()
        kwargs = {}
        for f in fields(cls):
            if f.name not in data:
                continue
            value = data[f.name]
            if isinstance(getattr(default, f.name), Color):
                try:
                    value = Color.parse(str(value))
                except ValueError:
                    continue  # valor inválido: se queda el de por defecto
            kwargs[f.name] = value
        return cls(**kwargs)


@dataclass
class Font:
    size: int
    weight: int = 400
    fonts: list[str] = field(default_factory=lambda: list(FONT_FAMILY))


@dataclass
class Fonts:
    h1: Font = field(default_factory=lambda: Font(40, 700))
    h2: Font = field(default_factory=lambda: Font(30, 700))
    h3: Font = field(default_factory=lambda: Font(20, 700))
    label: Font = field(default_factory=lambda: Font(14, 500))
    info: Font = field(default_factory=lambda: Font(14, 500))
    inactive: Font = field(default_factory=lambda: Font(14))
    lyric: Font = field(default_factory=lambda: Font(30, 500))
    lyric_active: Font = field(default_factory=lambda: Font(50, 800))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Fonts":
        default = cls()
        kwargs = {}
        for f in fields(cls):
            if isinstance(data.get(f.name), dict):
                base = asdict(getattr(default, f.name))
                kwargs[f.name] = Font(**{**base, **data[f.name]})
        return cls(**kwargs)


@dataclass(frozen=True)
class Accent:
    primary: Color
    secondary: Color
    tertiary: Color
