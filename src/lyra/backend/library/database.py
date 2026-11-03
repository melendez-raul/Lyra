import json
import sqlite3 as sql
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from ..models import Color, Metadata, Track

_SCHEMA = """
CREATE TABLE IF NOT EXISTS artists (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS albums (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    cover_path TEXT,
    cover_hash TEXT,
    cover_colors TEXT CHECK (cover_colors IS NULL OR json_valid(cover_colors))
);
CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    album_id INTEGER REFERENCES albums(id),
    track_number INTEGER,
    lyrics TEXT DEFAULT NULL CHECK (lyrics IS NULL OR json_valid(lyrics))
);
CREATE TABLE IF NOT EXISTS album_artists (
    album_id INTEGER NOT NULL REFERENCES albums(id),
    artist_id INTEGER NOT NULL REFERENCES artists(id),
    position INTEGER NOT NULL,
    PRIMARY KEY (album_id, artist_id)
);
CREATE TABLE IF NOT EXISTS track_artists (
    track_id INTEGER NOT NULL REFERENCES tracks(id),
    artist_id INTEGER NOT NULL REFERENCES artists(id),
    position INTEGER NOT NULL,
    PRIMARY KEY (track_id, artist_id)
);
"""


class LibraryError(Exception):
    pass


class Database:
    """Solo SQL: no lee tags, no toca archivos, no calcula colores."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        with self._transaction() as connection:
            connection.executescript(_SCHEMA)

    # ------------------------------------------------------------------
    # Público
    # ------------------------------------------------------------------

    def registered_paths(self) -> set[str]:
        with self._transaction() as connection:
            rows = connection.execute("SELECT path FROM tracks").fetchall()
        return {row["path"] for row in rows}

    def colors_for_hash(self, cover_hash: str) -> list[Color] | None:
        """Colores ya calculados para esa portada, o None si no se conocen."""
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT cover_colors FROM albums "
                "WHERE cover_hash = ? AND cover_colors IS NOT NULL LIMIT 1",
                (cover_hash,),
            ).fetchone()
        if row is None:
            return None
        return [Color.parse(c) for c in json.loads(row["cover_colors"])]

    def insert(
        self,
        metadata: Metadata,
        cover_hash: str | None = None,
        cover_colors: list[Color] | None = None,
    ) -> None:
        """Registra pista, artistas y álbum. metadata.cover_path ya viene resuelto."""
        with self._transaction() as connection:
            cursor = connection.cursor()
            if cursor.execute(
                "SELECT 1 FROM tracks WHERE path = ?", (metadata.path,)
            ).fetchone():
                return
            track_artists = [
                self._get_or_create_artist(cursor, n) for n in metadata.artist
            ]
            album_artists = [
                self._get_or_create_artist(cursor, n) for n in metadata.album_artist
            ]
            album_id = self._get_or_create_album(cursor, metadata.album, album_artists)
            self._set_cover(
                cursor, album_id, metadata.cover_path, cover_hash, cover_colors
            )
            lyrics = (
                json.dumps(
                    [line.to_dict() for line in metadata.lyrics], ensure_ascii=False
                )
                if metadata.lyrics
                else None
            )
            cursor.execute(
                "INSERT INTO tracks (path, title, album_id, track_number, lyrics) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    metadata.path,
                    metadata.title,
                    album_id,
                    metadata.track_number,
                    lyrics,
                ),
            )
            if cursor.lastrowid:
                cursor.executemany(
                    "INSERT INTO track_artists (track_id, artist_id, position) "
                    "VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
                    [(cursor.lastrowid, a, i) for i, a in enumerate(track_artists)],
                )

    def remove(self, paths: set[str]) -> list[str]:
        """Borra pistas y lo que quede huérfano.

        Devuelve las portadas que ya no usa ningún álbum, para que quien
        maneja archivos decida si las borra.
        """
        if not paths:
            return []
        marks = ",".join("?" * len(paths))
        args = tuple(paths)
        with self._transaction() as connection:
            connection.execute(
                "DELETE FROM track_artists WHERE track_id IN "
                f"(SELECT id FROM tracks WHERE path IN ({marks}))",
                args,
            )
            connection.execute(f"DELETE FROM tracks WHERE path IN ({marks})", args)
            orphans = connection.execute(
                "SELECT id, cover_path FROM albums WHERE id NOT IN "
                "(SELECT album_id FROM tracks WHERE album_id IS NOT NULL)"
            ).fetchall()
            for album in orphans:
                connection.execute(
                    "DELETE FROM album_artists WHERE album_id = ?", (album["id"],)
                )
                connection.execute("DELETE FROM albums WHERE id = ?", (album["id"],))
            connection.execute(
                "DELETE FROM artists WHERE id NOT IN "
                "(SELECT artist_id FROM track_artists "
                "UNION SELECT artist_id FROM album_artists)"
            )
            unused = []
            for cover in {a["cover_path"] for a in orphans if a["cover_path"]}:
                still_used = connection.execute(
                    "SELECT 1 FROM albums WHERE cover_path = ?", (cover,)
                ).fetchone()
                if not still_used:
                    unused.append(cover)
        return unused

    def load_tracks(self) -> list[Track]:
        """Pistas ordenadas por álbum y número."""
        with self._transaction() as connection:
            rows = connection.execute(
                """
                SELECT
                    t.path, t.title, t.track_number, t.lyrics,
                    al.title AS album, al.cover_path, al.cover_colors,
                    (
                        SELECT json_group_array(name) FROM (
                            SELECT ar.name FROM track_artists ta
                            JOIN artists ar ON ar.id = ta.artist_id
                            WHERE ta.track_id = t.id ORDER BY ta.position
                        )
                    ) AS artist,
                    (
                        SELECT json_group_array(name) FROM (
                            SELECT ar.name FROM album_artists aa
                            JOIN artists ar ON ar.id = aa.artist_id
                            WHERE aa.album_id = al.id ORDER BY aa.position
                        )
                    ) AS album_artist
                FROM tracks t
                LEFT JOIN albums al ON al.id = t.album_id
                ORDER BY al.title, t.track_number, t.title
                """
            ).fetchall()
        try:
            tracks = []
            for index, row in enumerate(rows):
                data = dict(row)
                data["index"] = index
                data["artist"] = json.loads(data["artist"] or "[]")
                data["album_artist"] = json.loads(data["album_artist"] or "[]")
                data["cover_colors"] = json.loads(data["cover_colors"] or "[]")
                tracks.append(Track.from_dict(data))
            return tracks
        except (ValueError, TypeError) as error:
            raise LibraryError from error

    # ------------------------------------------------------------------
    # Privado
    # ------------------------------------------------------------------

    def _connect(self) -> sql.Connection:
        connection = sql.connect(self.db_path)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.row_factory = sql.Row
        return connection

    @contextmanager
    def _transaction(self) -> Iterator[sql.Connection]:
        """Commit al salir, rollback si falla, y siempre cierra."""
        connection = self._connect()
        try:
            with connection:
                yield connection
        except sql.Error as error:
            raise LibraryError from error
        finally:
            connection.close()

    @staticmethod
    def _get_or_create_artist(cursor: sql.Cursor, name: str) -> int:
        cursor.execute(
            "INSERT INTO artists (name) VALUES (?) ON CONFLICT (name) DO NOTHING",
            (name,),
        )
        row = cursor.execute(
            "SELECT id FROM artists WHERE name = ?", (name,)
        ).fetchone()
        return row["id"]

    @staticmethod
    def _album_artist_ids(cursor: sql.Cursor, album_id: int) -> list[int]:
        rows = cursor.execute(
            "SELECT artist_id FROM album_artists WHERE album_id = ? ORDER BY position",
            (album_id,),
        ).fetchall()
        return [row["artist_id"] for row in rows]

    def _get_or_create_album(
        self, cursor: sql.Cursor, title: str, artist_ids: list[int]
    ) -> int:
        for album in cursor.execute(
            "SELECT id FROM albums WHERE title = ?", (title,)
        ).fetchall():
            if self._album_artist_ids(cursor, album["id"]) == artist_ids:
                return album["id"]
        cursor.execute("INSERT INTO albums (title) VALUES (?)", (title,))
        album_id = cursor.lastrowid
        cursor.executemany(
            "INSERT INTO album_artists (album_id, artist_id, position) VALUES (?, ?, ?)",
            [(album_id, a, i) for i, a in enumerate(artist_ids)],
        )
        return album_id  # pyright: ignore[reportReturnType]

    @staticmethod
    def _set_cover(
        cursor: sql.Cursor,
        album_id: int,
        cover_path: str | None,
        cover_hash: str | None,
        cover_colors: list[Color] | None,
    ) -> None:
        """Asigna la portada solo si el álbum todavía no tiene una."""
        if not cover_path:
            return
        colors = json.dumps([c.to_hex() for c in cover_colors or []])
        cursor.execute(
            "UPDATE albums SET cover_path = ?, cover_hash = ?, cover_colors = ? "
            "WHERE id = ? AND cover_path IS NULL",
            (cover_path, cover_hash, colors, album_id),
        )
