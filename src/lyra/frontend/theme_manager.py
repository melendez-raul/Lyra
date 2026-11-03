import importlib
from dataclasses import replace

from backend import Config
from backend.models import Accent
from PySide6.QtWidgets import QApplication

from . import styles


class ThemeManager:
    def __init__(self, app: QApplication, config: Config) -> None:
        self.app = app
        self.config = config

    def apply(self, accent: Accent | None = None) -> None:
        """Genera el QSS desde la config (más el acento, si hay) y lo aplica."""
        colors = self.config.colors
        if accent is not None:
            colors = replace(
                colors,
                primary=accent.primary,
                secondary=accent.secondary,
                tertiary=accent.tertiary,
            )
        self.app.setStyleSheet(styles.build(colors, self.config.fonts))

    def reload_module(self, accent: Accent | None = None) -> None:
        """Solo desarrollo: relee styles.py del disco y reaplica."""
        importlib.reload(styles)
        self.apply(accent)
