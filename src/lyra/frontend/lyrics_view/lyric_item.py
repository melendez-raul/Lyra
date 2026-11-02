from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import QWidget

from ..rules import AppWidget, Element, Level


class LyricItem(AppWidget):
    seek_requested = Signal(float)

    def __init__(
        self,
        time: float,
        text: str,
        is_active: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("lyricItem", parent)
        self.time = time
        self.text = text
        self.is_active = False
        self.is_hovered = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.text_label = Element.lyric(text, wrap=True)
        self.main_layout = Element.main_layout(
            self, [self.text_label], level=Level.ITEM
        )
        self.setProperty("hovered", False)
        self.set_active(is_active)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.seek_requested.emit(self.time)
            event.accept()
            return
        super().mousePressEvent(event)

    def set_active(self, active: bool) -> None:
        self.is_active = active
        self.setProperty("active", active)
        self._refresh_all()

    def enterEvent(self, event: QEvent) -> None:  # Evento para hover
        super().enterEvent(event)  # pyright: ignore[reportArgumentType]
        self._set_hovered(True)

    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        self._set_hovered(False)

    def _set_hovered(self, hovered: bool) -> None:
        if self.is_hovered == hovered:
            return
        self.is_hovered = hovered
        self.setProperty("hovered", hovered)
        self._refresh_all()

    def _refresh_all(self) -> None:
        self._refresh_style(self)
        self._refresh_style(self.text_label)
        self.text_label.updateGeometry()
        self.updateGeometry()

    @staticmethod
    def _refresh_style(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()
