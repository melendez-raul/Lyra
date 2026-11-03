from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget

from ..rules import ICONS_DIR, STRETCH, AppWidget, Element, IconSize


class PlaybackControls(AppWidget):
    previous_requested = Signal()
    play_pause_requested = Signal()
    next_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("playbackControls", parent)
        self._play_icon = QIcon(str(ICONS_DIR / "play.svg"))
        self._pause_icon = QIcon(str(ICONS_DIR / "pause.svg"))
        self._playing: bool | None = None
        self._enabled: bool | None = None
        self.previous_button = Element.icon_button(
            ICONS_DIR / "prev.svg",
            tooltip="Anterior",
            icon_size=IconSize.SM,
            on_click=self.previous_requested.emit,
        )
        self.play_button = Element.icon_button(
            self._play_icon,
            tooltip="Reproducir",
            icon_size=IconSize.LG,
            object_name="playButton",
            on_click=self.play_pause_requested.emit,
        )
        self.next_button = Element.icon_button(
            ICONS_DIR / "next.svg",
            tooltip="Siguiente",
            icon_size=IconSize.SM,
            on_click=self.next_requested.emit,
        )
        self.main_layout = Element.row(
            [
                STRETCH,
                self.previous_button,
                self.play_button,
                self.next_button,
                STRETCH,
            ],
            parent=self,
        )

    def set_playing(self, playing: bool) -> None:
        if playing == self._playing:
            return
        self._playing = playing
        label = "Pausar" if playing else "Reproducir"
        self.play_button.setIcon(self._pause_icon if playing else self._play_icon)
        self.play_button.setToolTip(label)

    def set_enabled(self, enabled: bool) -> None:
        if enabled == self._enabled:
            return
        self._enabled = enabled
        for button in (self.previous_button, self.play_button, self.next_button):
            button.setEnabled(enabled)
