from typing import cast

from backend import LyricLine
from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QObject,
    QPropertyAnimation,
    QTimer,
    Signal,
)
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..rules import RESUME_DELAY_MS, SCROLL_DURATION_MS, AppWidget, Element, Level
from .lyric_item import LyricItem


class LyricsPanel(AppWidget):
    seek_requested = Signal(float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("lyricsPanel", parent)
        self._items: list[LyricItem] = []
        self._active_index = -1
        self._user_scrolling = False
        self._dragging = False
        self.bottom_spacer = QWidget()
        self.scroll_area = Element.scroll(
            "lyricsScrollArea",
            [self.bottom_spacer],
            level=Level.NONE,
            horizontal=False,
        )
        self.list_widget = self.scroll_area.widget()
        self.list_layout = cast(QVBoxLayout, self.list_widget.layout())  # pyright: ignore[reportOptionalMemberAccess]
        self.main_layout = Element.main_layout(
            self, [(self.scroll_area, 1)], level=Level.PANEL
        )
        self.scroll_animation = QPropertyAnimation(
            self.scroll_area.verticalScrollBar(), b"value", self
        )
        self.scroll_animation.setDuration(SCROLL_DURATION_MS)
        self.scroll_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.resume_timer = QTimer(self)
        self.resume_timer.setSingleShot(True)
        self.resume_timer.setInterval(RESUME_DELAY_MS)
        self.resume_timer.timeout.connect(self._resume_autoscroll)
        self.scroll_area.viewport().installEventFilter(self)
        self.scroll_area.verticalScrollBar().installEventFilter(self)

    # ----------------------------------
    # CONTENIDO
    # ----------------------------------

    def set_lyrics(self, lines: list[LyricLine]) -> None:
        """Reemplaza la letra. Una lista vacía la limpia."""
        self._release_scroll()
        self.scroll_animation.stop()
        self._clear_items()
        self._active_index = -1
        self.scroll_area.verticalScrollBar().setValue(0)
        for line in lines:
            item = LyricItem(line)
            item.seek_requested.connect(self._on_item_clicked)
            self._items.append(item)
            self.list_layout.insertWidget(self.list_layout.count() - 1, item)
        self._update_bottom_spacer()

    def set_active_lyric(self, index: int) -> None:
        if not 0 <= index < len(self._items) or index == self._active_index:
            return
        if self._active_index != -1:
            self._items[self._active_index].set_active(False)
        self._active_index = index
        self._items[index].set_active(True)
        if not self._user_scrolling:
            self._scroll_to_active()

    # ----------------------------------
    # AUTOSCROLL
    # ----------------------------------

    def _scroll_to_active(self) -> None:
        if self._active_index == -1:
            return
        item = self._items[self._active_index]
        QTimer.singleShot(0, lambda: self._scroll_to_item(item))

    def _scroll_to_item(self, item: LyricItem) -> None:
        if item not in self._items or self._user_scrolling:
            return
        self.list_layout.activate()
        scrollbar = self.scroll_area.verticalScrollBar()
        self.scroll_animation.stop()
        self.scroll_animation.setStartValue(scrollbar.value())
        self.scroll_animation.setEndValue(item.y())
        self.scroll_animation.start()

    def _on_user_scroll(self) -> None:
        self._user_scrolling = True
        self.scroll_animation.stop()  # corta la animación en curso
        if not self._dragging:
            self.resume_timer.start()  # reinicia los 2 s

    def _resume_autoscroll(self) -> None:
        self._user_scrolling = False
        self._scroll_to_active()

    def _release_scroll(self) -> None:
        self.resume_timer.stop()
        self._user_scrolling = False
        self._dragging = False

    def _on_item_clicked(self, time: float) -> None:
        # elegir una línea termina la exploración: la vista sigue a la nueva
        self._release_scroll()
        self.seek_requested.emit(time)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        kind = event.type()
        if kind == QEvent.Type.Wheel:
            self._on_user_scroll()
        elif watched is self.scroll_area.verticalScrollBar():
            if kind == QEvent.Type.MouseButtonPress:
                self._dragging = True
                self.resume_timer.stop()
                self._on_user_scroll()
            elif kind == QEvent.Type.MouseButtonRelease:
                self._dragging = False
                self.resume_timer.start()
        return super().eventFilter(watched, event)

    # ----------------------------------
    # LIMPIEZA Y TAMAÑO
    # ----------------------------------

    def _clear_items(self) -> None:
        for item in self._items:
            self.list_layout.removeWidget(item)
            item.deleteLater()
        self._items.clear()

    def _update_bottom_spacer(self) -> None:
        self.bottom_spacer.setFixedHeight(self.scroll_area.viewport().height())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_bottom_spacer()
