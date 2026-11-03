import logging
from pathlib import Path

from mutagen import MutagenError

from ..models import Track
from . import file_manager, tags
from .database import Database, LibraryError
from .palette import extract_colors

__all__ = ["Library", "LibraryError"]

logger = logging.getLogger(__name__)

APP_DIR_NAME = "Lyra"
SUPPORTED_EXTENSIONS = {".flac"}


class Library:
    def __init__(
        self,
        directory: Path,
        structure: bool = False,
        data_dir: Path | None = None,
    ) -> None:
        """Biblioteca de `directory`.

        data_dir: dónde van library.db y covers/. Por defecto <directory>/Lyra.
        structure: si es True, scan() ordena los archivos en Artista/Álbum/.
        """
        self.music_dir = directory
        self.structure = structure
        self.data_dir = data_dir or directory / APP_DIR_NAME
        self.covers_dir = self.data_dir / "covers"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.database = Database(self.data_dir / "library.db")

    # ------------------------------------------------------------------
    # Público
    # ------------------------------------------------------------------

    def scan(self) -> None:
        """Sincroniza la DB con el disco: alta de lo nuevo, baja de lo que ya no está."""
        if not self.music_dir.is_dir():
            logger.warning("Carpeta no disponible: %s", self.music_dir)
            return
        on_disk = {
            str(path)
            for path in self.music_dir.rglob("*")
            if path.suffix.lower() in SUPPORTED_EXTENSIONS
        }
        in_db = self.database.registered_paths()
        file_manager.delete_files(self.database.remove(in_db - on_disk))
        for path in sorted(on_disk - in_db):
            try:
                self._process_file(Path(path))
            except (OSError, ValueError, MutagenError, LibraryError) as error:
                logger.warning("Omitido %s: %s", path, error)

    def load_tracks(self) -> list[Track]:
        return self.database.load_tracks()

    # ------------------------------------------------------------------
    # Privado
    # ------------------------------------------------------------------

    def _process_file(self, path: Path) -> None:
        """Flujo explícito: leer, organizar, guardar portada, colores, insertar."""
        if self.structure:
            file_manager.strip_comment(path)
        metadata, picture = tags.read(path)
        destination = None
        if self.structure:
            destination = file_manager.album_dir(
                self.music_dir, metadata.album_artist, metadata.album
            )
            metadata.path = file_manager.move_and_rename(
                path, destination, metadata.title, ".flac"
            )
        digest, colors = None, None
        if picture is not None:
            digest = file_manager.cover_hash(picture)
            if destination is not None:
                metadata.cover_path = file_manager.save_cover(
                    picture, destination, "cover"
                )
            else:
                metadata.cover_path = file_manager.save_cover(
                    picture, self.covers_dir, digest
                )
            colors = self.database.colors_for_hash(digest)
            if colors is None:
                colors = extract_colors(metadata.cover_path)
        self.database.insert(metadata, digest, colors)  # pyright: ignore[reportArgumentType]
