from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon

from ..rules import ICONS_DIR, STRETCH, AppWidget, Element, IconSize


class PlaybackControls(AppWidget):
    previous_requested = Signal()
    play_pause_requested = Signal()
    next_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__("playbackControls", parent)
        self.previous_button = Element.icon_button(
            ICONS_DIR / "prev.svg",
            tooltip="Anterior",
            icon_size=IconSize.SM,
            on_click=self.previous_requested.emit,
        )
        self.play_button = Element.icon_button(
            ICONS_DIR / "play.svg",
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
        icon_name = "pause.svg" if playing else "play.svg"
        self.play_button.setIcon(QIcon(str(ICONS_DIR / icon_name)))
        self.play_button.setAccessibleName("Pausar" if playing else "Reproducir")
        self.play_button.setToolTip("Pausar" if playing else "Reproducir")

    def set_enabled(self, enabled: bool) -> None:
        self.previous_button.setEnabled(enabled)
        self.play_button.setEnabled(enabled)
        self.next_button.setEnabled(enabled)
