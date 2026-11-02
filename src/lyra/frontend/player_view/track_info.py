from PySide6.QtWidgets import QWidget

from ..rules import AppWidget, Element, Level


class TrackInfo(AppWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("trackInfo", parent)
        self.title = Element.h1(wrap=True)
        self.artist = Element.h2(wrap=True)
        self.album = Element.h3(wrap=True)
        self.main_layout = Element.main_layout(
            self, [self.title, self.artist, self.album], level=Level.NONE
        )

    def set_track_info(self, title: str, artist: str, album: str) -> None:
        self.title.setText(title)
        self.artist.setText(artist)
        self.album.setText(album)
