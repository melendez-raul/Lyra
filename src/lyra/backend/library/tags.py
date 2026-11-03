import re
from pathlib import Path

from mutagen.flac import FLAC, Picture

from ..models import LyricLine, Metadata

UNKNOWN_ARTIST = "No Artist"
UNKNOWN_ALBUM = "Unknown"

_LYRIC_LINE = re.compile(r"\[(\d{2}):(\d{2})(?:\.(\d{1,3}))?\](.*)")


# ----------------------------------------------------------------------
# Público
# ----------------------------------------------------------------------


def read(path: Path) -> tuple[Metadata, Picture | None]:
    """Metadatos y portada embebida de un FLAC. Solo lee."""
    audio = FLAC(path)
    artist = _split_names(_get_tag(audio, "ARTIST"))
    album_artist = _split_names(_get_tag(audio, "ALBUMARTIST"))
    album_artist = album_artist or artist or [UNKNOWN_ARTIST]
    raw_lyrics = _get_tag(audio, "LYRICS")
    metadata = Metadata(
        path=str(path),
        cover_path=None,
        title=_get_tag(audio, "TITLE") or path.stem,
        artist=artist or album_artist,
        album=_get_tag(audio, "ALBUM") or UNKNOWN_ALBUM,
        album_artist=album_artist,
        track_number=_parse_track_number(_get_tag(audio, "TRACKNUMBER")),
        lyrics=_parse_lyrics(raw_lyrics) if raw_lyrics else [],
    )
    return metadata, (audio.pictures[0] if audio.pictures else None)


# ----------------------------------------------------------------------
# Privado
# ----------------------------------------------------------------------


def _get_tag(audio: FLAC, name: str) -> str | None:
    values = audio.get(name)
    if not values:
        return None
    return values[0].strip() or None


def _split_names(value: str | None) -> list[str]:
    """Separa por ';' sin vacíos ni duplicados, conservando el orden."""
    if not value:
        return []
    names = [part.strip() for part in value.split(";")]
    return list(dict.fromkeys(name for name in names if name))


def _parse_track_number(value: str | None) -> int | None:
    """Acepta '3' o '3/12'."""
    if not value:
        return None
    match = re.match(r"\s*(\d+)", value)
    return int(match.group(1)) if match else None


def _parse_lyrics(raw: str) -> list[LyricLine]:
    """Letras LRC a líneas ordenadas por tiempo."""
    lines = []
    for line in raw.splitlines():
        match = _LYRIC_LINE.match(line)
        if not match:
            continue
        minutes, seconds, fraction, text = match.groups()
        text = text.strip()
        if not text:
            continue
        timestamp = int(minutes) * 60 + int(seconds)
        if fraction:
            timestamp += int(fraction) / (10 ** len(fraction))
        lines.append(LyricLine(timestamp, text))
    return sorted(lines, key=lambda line: line.time)
