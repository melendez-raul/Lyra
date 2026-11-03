from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from .models import PlaybackState, PlaybackStatus


class Player(QObject):
    status_changed = Signal(object)
    track_finished = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._audio = QAudioOutput(self)
        self._player = QMediaPlayer(self)
        self._player.setAudioOutput(self._audio)
        self._track: str | None = None
        self._closed = False
        self._error = False
        self._player.playbackStateChanged.connect(self._emit_status)
        self._player.positionChanged.connect(self._emit_status)
        self._player.durationChanged.connect(self._emit_status)
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)
        self._player.errorOccurred.connect(self._on_error)

    # ------------------------------------------------------------------
    # Público
    # ------------------------------------------------------------------

    def play(self, path: str) -> None:
        if self._closed:
            return
        self._track = path
        self._error = False
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()

    def pause(self) -> None:
        if not self._closed:
            self._player.pause()

    def resume(self) -> None:
        if not self._closed:
            self._player.play()

    def stop(self) -> None:
        if self._closed:
            return
        self._release()
        self._emit_status()

    def seek(self, seconds: float) -> None:
        if self._closed:
            return
        position_ms = max(0, int(seconds * 1000))
        duration_ms = self._player.duration()
        if duration_ms > 0:
            position_ms = min(position_ms, duration_ms)
        self._player.setPosition(position_ms)

    def get_status(self) -> PlaybackStatus:
        duration_ms = self._player.duration()
        return PlaybackStatus(
            state=self._get_state(),
            track=self._track,
            time=self._player.position() / 1000,
            duration=duration_ms / 1000 if duration_ms > 0 else None,
        )

    def close(self) -> None:
        if self._closed:
            return
        self._release()
        self._closed = True
        self._emit_status()

    # ------------------------------------------------------------------
    # Privado
    # ------------------------------------------------------------------

    def _release(self) -> None:
        """Detiene y descarga la pista actual."""
        self._player.stop()
        self._player.setSource(QUrl())
        self._track = None
        self._error = False

    def _get_state(self) -> PlaybackState:
        if self._closed:
            return "closed"
        if self._error:
            return "error"
        media_status = self._player.mediaStatus()
        if media_status == QMediaPlayer.MediaStatus.LoadingMedia:
            return "loading"
        if media_status == QMediaPlayer.MediaStatus.InvalidMedia:
            return "error"
        playback_state = self._player.playbackState()
        if playback_state == QMediaPlayer.PlaybackState.PlayingState:
            return "playing"
        if playback_state == QMediaPlayer.PlaybackState.PausedState:
            return "paused"
        return "stopped"

    def _emit_status(self, *_args) -> None:
        self.status_changed.emit(self.get_status())

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._emit_status()
            self.track_finished.emit()
            return
        if status == QMediaPlayer.MediaStatus.InvalidMedia:
            self._error = True
        elif status == QMediaPlayer.MediaStatus.LoadingMedia:
            self._error = False
        self._emit_status()

    def _on_error(self, *_args) -> None:
        self._error = True
        self._emit_status()
