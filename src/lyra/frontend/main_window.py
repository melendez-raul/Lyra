from backend import Config, Controller
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QSplitter, QStackedWidget, QWidget

from .accents import pick_accent
from .config_view import ConfigPanel
from .library_view import LibraryPanel
from .lyrics_view import LyricsPanel
from .player_view import PlayerPanel
from .rules import ICONS_DIR, STRETCH, AppWidget, Element, IconSize, Level
from .theme_manager import ThemeManager

WINDOW_SIZE = (1280, 800)
WINDOW_MIN_SIZE = (900, 600)
SPLITTER_SIZES = (320, 960)
FORCE_ACCENT = "__force__"


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
        self._accent_name: str | None = None

        self.setWindowTitle("Lyra")
        self.resize(*WINDOW_SIZE)
        self.setMinimumSize(*WINDOW_MIN_SIZE)

        # paneles
        self.player_panel = PlayerPanel()
        self.library_panel = LibraryPanel(self.controller.playlist)
        self.lyrics_panel = LyricsPanel()
        self.config_panel = ConfigPanel(self.config)

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentStack")
        for panel in (self.library_panel, self.lyrics_panel, self.config_panel):
            self.content_stack.addWidget(panel)

        # cabecera
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

        # contenido (cabecera + stack)
        self.content_container = AppWidget("contentContainer")
        self.content_layout = Element.main_layout(
            self.content_container,
            [self.header_layout, (self.content_stack, 1)],
            level=Level.NONE,
        )

        # splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setObjectName("mainSplitter")
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(0)
        self.splitter.addWidget(self.player_panel)
        self.splitter.addWidget(self.content_container)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 3)
        self.splitter.setSizes(list(SPLITTER_SIZES))

        # fondo
        self.background_widget = AppWidget("appBackground")
        self.background_layout = Element.main_layout(
            self.background_widget, [self.splitter], level=Level.NONE
        )
        self.setCentralWidget(self.background_widget)

        self._connect_signals()
        self._initialize_player()

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

    def _initialize_player(self) -> None:
        track = self.controller.current_track
        self.player_panel.set_track(track)
        self.player_panel.set_status(self.controller.get_status())
        self.lyrics_panel.set_lyrics(track.lyrics if track else [])
        self._apply_cover_theme(track)

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

    def _on_track_changed(self, track) -> None:
        self._apply_cover_theme(track)
        self.player_panel.set_track(track)
        self.lyrics_panel.set_lyrics(track.lyrics if track else [])

    def _on_status_changed(self, status) -> None:
        self.player_panel.set_status(status)
        self._sync_lyrics(status.time)

    def _sync_lyrics(self, position: float) -> None:
        track = self.controller.current_track
        if not track or not track.lyrics:
            return
        active = -1
        for index, lyric in enumerate(track.lyrics):
            if lyric["time"] > position:
                break
            active = index
        if active != -1:
            self.lyrics_panel.set_active_lyric(active)

    # ----------------------------------
    # CONFIGURACIÓN Y TEMA
    # ----------------------------------

    def _on_config_changed(self) -> None:
        self._accent_name = FORCE_ACCENT
        self._apply_cover_theme(self.controller.current_track)
        if self.config.library_path != self._library_path:
            self._library_path = self.config.library_path
            self.controller.load_library(self.config.library_path)  # pyright: ignore[reportArgumentType]
            self._initialize_player()

    def _apply_cover_theme(self, track) -> None:
        pick = None
        if track and self.config.dynamic_colors:
            pick = pick_accent(track.cover_color, self.config.accents)
        name = pick[0] if pick else None
        if name == self._accent_name:
            return
        self._accent_name = name
        colors = self.config.colors.to_dict()
        if pick:
            colors.update(pick[1].to_dict())
        self.theme_manager.set_theme(colors, self.config.fonts.to_dict())
