from backend import Config
from backend.models import Font
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from ..rules import (
    ICONS_DIR,
    STRETCH,
    AppWidget,
    Element,
    IconSize,
    Level,
)
from .colors_section import ColorsSection
from .fonts_section import FontsSection
from .library_path_entry import LibraryPathEntry


class ConfigPanel(AppWidget):
    config_changed = Signal()

    def __init__(self, config: Config, parent: QWidget | None = None) -> None:
        super().__init__("configPanel", parent)
        self.config = config

        self.library_path = LibraryPathEntry(config.library_path)
        self.colors_section = ColorsSection(config.colors.to_dict())
        self.fonts_section = FontsSection(config.fonts.to_dict())
        self.library_path.path_changed.connect(self._on_library_path_changed)
        self.colors_section.transparency_changed.connect(self._on_transparency_changed)
        self.colors_section.color_changed.connect(self._on_color_changed)
        self.fonts_section.font_changed.connect(self._on_font_changed)

        self.title = Element.h1("Configuración")
        self.save_button = Element.icon_button(
            ICONS_DIR / "save.svg",
            tooltip="Guardar cambios",
            icon_size=IconSize.SM,
            on_click=self.save_config,
        )
        self.header_row = Element.row([self.title, STRETCH, self.save_button])

        self.scroll_area = Element.scroll(
            "configScrollArea",
            [self.library_path, self.colors_section, self.fonts_section, STRETCH],
            level=Level.PAGE,
        )
        self.main_layout = Element.main_layout(
            self, [self.header_row, (self.scroll_area, 1)], level=Level.PANEL
        )

    def _on_library_path_changed(self, path: str) -> None:
        self.config.library_path = path

    def _on_transparency_changed(self, value: int) -> None:
        self.config.colors.transparency = value

    def _on_color_changed(self, key: str, color: str) -> None:
        if hasattr(self.config.colors, key):
            setattr(self.config.colors, key, color)

    def _on_font_changed(self, key: str, font: dict) -> None:
        if hasattr(self.config.fonts, key):
            setattr(self.config.fonts, key, Font(**font))

    def save_config(self) -> None:
        self.config.save()
        self.config_changed.emit()
