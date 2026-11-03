from backend import Config
from backend.models import Color, Font
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from ..rules import ICONS_DIR, STRETCH, AppWidget, Element, IconSize, Level
from .colors_section import ColorsSection
from .fonts_section import FontsSection
from .library_path_entry import LibraryPathEntry


class ConfigPanel(AppWidget):
    config_changed = Signal()

    def __init__(self, config: Config, parent: QWidget | None = None) -> None:
        super().__init__("configPanel", parent)
        self.config = config

        self.library_path = LibraryPathEntry(config.library_path)
        self.colors_section = ColorsSection(
            config.colors.to_dict(), config.dynamic_colors
        )
        self.fonts_section = FontsSection(config.fonts.to_dict())

        self.library_path.path_changed.connect(self._on_library_path)
        self.colors_section.transparency_changed.connect(self._on_transparency)
        self.colors_section.color_changed.connect(self._on_color)
        self.colors_section.dynamic_colors_changed.connect(self._on_dynamic_colors)
        self.fonts_section.font_changed.connect(self._on_font)

        self.save_button = Element.icon_button(
            ICONS_DIR / "save.svg",
            tooltip="Guardar cambios",
            icon_size=IconSize.SM,
            on_click=self.save_config,
        )
        self.header_row = Element.row(
            [Element.h1("Configuración"), STRETCH, self.save_button]
        )
        self.scroll_area = Element.scroll(
            "configScrollArea",
            [self.library_path, self.colors_section, self.fonts_section, STRETCH],
            level=Level.PAGE,
        )
        self.main_layout = Element.main_layout(
            self, [self.header_row, (self.scroll_area, 1)], level=Level.PANEL
        )

    def save_config(self) -> None:
        self.config.save()
        self.config_changed.emit()

    def _on_library_path(self, path: str) -> None:
        self.config.library_path = path

    def _on_transparency(self, value: int) -> None:
        self.config.colors.transparency = value

    def _on_color(self, key: str, color: Color) -> None:
        if hasattr(self.config.colors, key):
            setattr(self.config.colors, key, color)

    def _on_font(self, key: str, font: dict) -> None:
        if hasattr(self.config.fonts, key):
            setattr(self.config.fonts, key, Font(**font))

    def _on_dynamic_colors(self, enabled: bool) -> None:
        self.config.dynamic_colors = enabled
