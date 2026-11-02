from pathlib import Path

from backend import Track
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QSizePolicy, QWidget

from ..rules import THUMB_SIZE, AppWidget, Element, Level


class TrackItem(AppWidget):
    play_requested = Signal(int)

    def __init__(self, track: Track, parent: QWidget | None = None) -> None:
        super().__init__("trackItem", parent)
        self._track = track
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.artwork = Element.label("")
        self.artwork.setFixedSize(THUMB_SIZE, THUMB_SIZE)
        self.artwork.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_cover(track.cover_path)
        self.info_layout = Element.column(
            [
                Element.label(track.title, wrap=True),
                Element.info(", ".join(track.artist), wrap=True),
                Element.info(track.album, wrap=True),
            ],
            level=Level.TIGHT,
        )
        self.main_layout = Element.row(
            [self.artwork, self.info_layout], level=Level.ITEM, parent=self
        )
        self.main_layout.setStretchFactor(self.info_layout, 1)

    def _set_cover(self, path: str | Path | None) -> None:
        pixmap = QPixmap(str(path)) if path else QPixmap()
        if pixmap.isNull():
            return
        dpr = self.devicePixelRatioF()
        scaled = pixmap.scaled(
            self.artwork.size() * dpr,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        scaled.setDevicePixelRatio(dpr)
        self.artwork.setPixmap(scaled)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.play_requested.emit(self._track.index)
            event.accept()
            return
        super().mousePressEvent(event)
