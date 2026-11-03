from backend.models import LyricLine
from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import QWidget

from ..rules import AppWidget, Element, Level


class LyricItem(AppWidget):
    seek_requested = Signal(float)

    def __init__(self, line: LyricLine, parent: QWidget | None = None) -> None:
        super().__init__("lyricItem", parent)
        self.line = line
        self._hovered = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.text_label = Element.lyric(line.text, wrap=True)
        self.main_layout = Element.main_layout(
            self, [self.text_label], level=Level.ITEM
        )
        self.setProperty("active", False)
        self.setProperty("hovered", False)

    def set_active(self, active: bool) -> None:
        self.setProperty("active", active)
        self._restyle()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.seek_requested.emit(self.line.time)
            event.accept()
            return
        super().mousePressEvent(event)

    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        self._set_hovered(True)

    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        self._set_hovered(False)

    def _set_hovered(self, hovered: bool) -> None:
        if self._hovered != hovered:
            self._hovered = hovered
            self.setProperty("hovered", hovered)
            self._restyle()

    def _restyle(self) -> None:
        for widget in (self, self.text_label):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        self.updateGeometry()
