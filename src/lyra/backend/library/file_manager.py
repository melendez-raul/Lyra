import hashlib
import re
import shutil
from pathlib import Path

from mutagen.flac import FLAC, Picture

from .tags import UNKNOWN_ARTIST

_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
_MAX_NAME_LENGTH = 120


# ----------------------------------------------------------------------
# Público
# ----------------------------------------------------------------------


def safe_name(name: str) -> str:
    """Nombre válido como archivo o carpeta en cualquier sistema."""
    name = _INVALID_CHARS.sub("_", name).strip()[:_MAX_NAME_LENGTH]
    name = name.strip().rstrip(". ")
    if not name:
        return "_"
    if name.split(".")[0].upper() in _RESERVED_NAMES:
        name = f"_{name}"
    return name


def album_dir(root: Path, album_artist: list[str], album: str) -> Path:
    """Crea (si falta) root/Artista/Álbum y la devuelve."""
    artist_name = ", ".join(album_artist) or UNKNOWN_ARTIST
    directory = root / safe_name(artist_name) / safe_name(album)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def move_and_rename(source: Path, to_dir: Path, name: str, ext: str) -> str:
    """Mueve el archivo a `to_dir` con nombre seguro y devuelve su ruta."""
    destination = _unique_path(to_dir, safe_name(name), ext, source)
    if not destination.exists():
        shutil.move(source, destination)
    return str(destination)


def strip_comment(path: Path) -> None:
    """Borra el tag COMMENT del FLAC (modifica el archivo)."""
    audio = FLAC(path)
    if audio.get("COMMENT"):
        audio.pop("COMMENT")
        audio.save()


def cover_hash(picture: Picture) -> str:
    return hashlib.sha1(picture.data).hexdigest()


def save_cover(picture: Picture, directory: Path, name: str) -> str:
    """Escribe la portada como <name>.ext en `directory` si no existe."""
    extension = ".png" if picture.mime == "image/png" else ".jpg"
    directory.mkdir(parents=True, exist_ok=True)
    cover = directory / f"{name}{extension}"
    if not cover.exists():
        cover.write_bytes(picture.data)
    return str(cover)


def delete_files(paths: list[str]) -> None:
    for path in paths:
        Path(path).unlink(missing_ok=True)


# ----------------------------------------------------------------------
# Privado
# ----------------------------------------------------------------------


def _unique_path(directory: Path, name: str, ext: str, source: Path) -> Path:
    candidate = directory / f"{name}{ext}"
    counter = 2
    while candidate.exists() and not candidate.samefile(source):
        candidate = directory / f"{name} ({counter}){ext}"
        counter += 1
    return candidate
