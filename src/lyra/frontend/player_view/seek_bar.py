from backend import PlaybackStatus
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from ..rules import STRETCH, AppWidget, Element, Level


def format_time(seconds: float) -> str:
    minutes, secs = divmod(max(0, int(seconds)), 60)
    return f"{minutes}:{secs:02d}"


class SeekBar(AppWidget):
    seek_requested = Signal(float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("seekBar", parent)
        self._seeking = False
        self.current_time = Element.inactive("0:00")
        self.total_time = Element.inactive("--:--")
        self.slider = Element.slider(
            maximum=0,
            on_press=self._start_seek,
            on_move=self._preview_position,
            on_release=self._finish_seek,
        )
        self.time_layout = Element.row(
            [self.current_time, STRETCH, self.total_time], level=Level.NONE
        )
        self.main_layout = Element.main_layout(
            self, [self.slider, self.time_layout], level=Level.NONE
        )

    def set_status(self, status: PlaybackStatus) -> None:
        duration = status.duration or 0.0
        self.slider.setRange(0, round(duration * 1000))
        self.total_time.setText(
            format_time(duration) if status.duration is not None else "--:--"
        )
        if not self._seeking:
            self.slider.setValue(round(status.time * 1000))
            self.current_time.setText(format_time(status.time))

    def _start_seek(self) -> None:
        self._seeking = True

    def _preview_position(self, position_ms: int) -> None:
        self.current_time.setText(format_time(position_ms / 1000))

    def _finish_seek(self) -> None:
        position = self.slider.value() / 1000
        self._seeking = False
        self.current_time.setText(format_time(position))
        self.seek_requested.emit(position)
