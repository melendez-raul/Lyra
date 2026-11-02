from typing import cast

from backend import Playlist
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..rules import STRETCH, AppWidget, Element, Level
from .track_item import TrackItem


class LibraryPanel(AppWidget):
    play_requested = Signal(int)

    def __init__(self, playlist: Playlist, parent: QWidget | None = None) -> None:
        super().__init__("libraryPanel", parent)
        self._playlist = playlist
        self._items: list[TrackItem] = []
        self.scroll_area = Element.scroll(
            "libraryScrollArea", [STRETCH], level=Level.LIST
        )
        self.list_widget = self.scroll_area.widget()
        self.list_layout = cast(QVBoxLayout, self.list_widget.layout())  # pyright: ignore[reportOptionalMemberAccess]
        self.main_layout = Element.main_layout(
            self, [(self.scroll_area, 1)], level=Level.PANEL
        )
        self.refresh()

    def set_playlist(self, playlist: Playlist) -> None:
        self._playlist = playlist
        self.refresh()

    def refresh(self) -> None:
        self._clear_items()
        for track in self._playlist.tracks:
            item = TrackItem(track)
            item.play_requested.connect(self.play_requested)
            self._items.append(item)
            self.list_layout.insertWidget(self.list_layout.count() - 1, item)

    def _clear_items(self) -> None:
        for item in self._items:
            self.list_layout.removeWidget(item)
            item.deleteLater()
        self._items.clear()
