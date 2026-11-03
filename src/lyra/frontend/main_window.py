from bisect import bisect_right

from backend import Config, Controller
from backend.models import Color, Track
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QSplitter, QStackedWidget, QWidget

from .accents import derive_accent
from .config_view import ConfigPanel
from .library_view import LibraryPanel
from .lyrics_view import LyricsPanel
from .player_view import PlayerPanel
from .rules import ICONS_DIR, STRETCH, AppWidget, Element, IconSize, Level
from .theme_manager import ThemeManager

WINDOW_SIZE = (1280, 800)
WINDOW_MIN_SIZE = (900, 600)
SPLITTER_SIZES = (320, 960)


class MainWindow(QMainWindow):
    def __init__(
        self,
        controller: Controller,
        theme_manager: ThemeManager,
        config: Config,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.controller = controller
        self.theme_manager = theme_manager
        self.config = config
        self._library_path = config.library_path
        self._accent_key: Color | None = None
        self._accent_applied = False  # fuerza el primer aplicado y los reaplicados
        self.setWindowTitle("Lyra")
        self.resize(*WINDOW_SIZE)
        self.setMinimumSize(*WINDOW_MIN_SIZE)
        self.player_panel = PlayerPanel()
        self.library_panel = LibraryPanel(controller.playlist)
        self.lyrics_panel = LyricsPanel()
        self.config_panel = ConfigPanel(config)
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentStack")
        for panel in (self.library_panel, self.lyrics_panel, self.config_panel):
            self.content_stack.addWidget(panel)
        self.view_button = Element.button("Biblioteca", on_click=self.toggle_view)
        self.config_button = Element.icon_button(
            ICONS_DIR / "config.svg",
            tooltip="Configuración",
            icon_size=IconSize.SM,
            on_click=self.show_config,
        )
        self.header_layout = Element.row(
            [self.view_button, STRETCH, self.config_button], level=Level.BAR
        )
        self.content_container = AppWidget("contentContainer")
        Element.main_layout(
            self.content_container,
            [self.header_layout, (self.content_stack, 1)],
            level=Level.NONE,
        )
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setObjectName("mainSplitter")
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(0)
        self.splitter.addWidget(self.player_panel)
        self.splitter.addWidget(self.content_container)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 3)
        self.splitter.setSizes(list(SPLITTER_SIZES))
        self.background_widget = AppWidget("appBackground")
        Element.main_layout(self.background_widget, [self.splitter], level=Level.NONE)
        self.setCentralWidget(self.background_widget)
        self._connect_signals()
        self._refresh()

    # ----------------------------------
    # CONEXIONES
    # ----------------------------------

    def _connect_signals(self) -> None:
        player, controller = self.player_panel, self.controller
        player.previous_requested.connect(controller.previous)
        player.play_pause_requested.connect(controller.toggle_playback)
        player.next_requested.connect(controller.next)
        player.seek_requested.connect(controller.seek)
        self.lyrics_panel.seek_requested.connect(controller.seek)
        self.library_panel.play_requested.connect(controller.play_index)
        controller.current_track_changed.connect(self._on_track_changed)
        controller.status_changed.connect(self._on_status_changed)
        controller.playlist_changed.connect(self.library_panel.set_playlist)
        self.config_panel.config_changed.connect(self._on_config_changed)

    # ----------------------------------
    # NAVEGACIÓN
    # ----------------------------------

    def toggle_view(self) -> None:
        if self.content_stack.currentWidget() is self.library_panel:
            self.show_lyrics()
        else:
            self.show_library()

    def show_library(self) -> None:
        self.content_stack.setCurrentWidget(self.library_panel)
        self.view_button.setText("Biblioteca")

    def show_lyrics(self) -> None:
        self.content_stack.setCurrentWidget(self.lyrics_panel)
        self.view_button.setText("Letras")

    def show_config(self) -> None:
        self.content_stack.setCurrentWidget(self.config_panel)

    # ----------------------------------
    # PISTA Y REPRODUCCIÓN
    # ----------------------------------

    def _refresh(self) -> None:
        """Pone toda la UI al día con la pista y el estado actuales."""
        track = self.controller.current_track
        self._show_track(track)
        self.player_panel.set_status(self.controller.get_status())

    def _show_track(self, track: Track | None) -> None:
        self._apply_theme(track)
        self.player_panel.set_track(track)
        self.lyrics_panel.set_lyrics(track.lyrics if track else [])

    def _on_track_changed(self, track: Track | None) -> None:
        self._show_track(track)

    def _on_status_changed(self, status) -> None:
        self.player_panel.set_status(status)
        self._sync_lyrics(status.time)

    def _sync_lyrics(self, position: float) -> None:
        track = self.controller.current_track
        if not track or not track.lyrics:
            return
        # las líneas vienen ordenadas por tiempo
        times = [line.time for line in track.lyrics]
        index = bisect_right(times, position) - 1
        if index >= 0:
            self.lyrics_panel.set_active_lyric(index)

    # ----------------------------------
    # CONFIGURACIÓN Y TEMA
    # ----------------------------------

    def _on_config_changed(self) -> None:
        self._accent_applied = False  # fuerza el reaplicado con la config nueva
        self._apply_theme(self.controller.current_track)
        if self.config.library_path != self._library_path:
            self._library_path = self.config.library_path
            self.controller.initialize(
                self.config.library_path,  # pyright: ignore[reportArgumentType]
                self.config.structure_library,
            )
            self._refresh()

    def _apply_theme(self, track: Track | None) -> None:
        accent = None
        if track and self.config.dynamic_colors:
            accent = derive_accent(track.cover_colors, self.config.colors)
        key = accent.primary if accent else None
        if self._accent_applied and key == self._accent_key:
            return  # mismo acento: no se reaplica el QSS
        self._accent_applied = True
        self._accent_key = key
        self.theme_manager.apply(accent)
