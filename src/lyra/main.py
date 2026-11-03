import sys
from pathlib import Path

from backend import Config, Controller, Player
from frontend import MainWindow, ThemeManager
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QFileDialog

ICON = Path(__file__).parent / "frontend/assets/Lyra-logo.png"


def ask_library(config: Config) -> Path | None:
    """Carpeta guardada si es válida; si no, la pide y la guarda."""
    if config.library_path and Path(config.library_path).is_dir():
        return Path(config.library_path)
    selected = QFileDialog.getExistingDirectory(
        None, "Seleccionar biblioteca musical", str(Path.home())
    )
    if not selected:
        return None
    config.library_path = selected
    config.save()
    return Path(selected)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Lyra")
    app.setWindowIcon(QIcon(str(ICON)))
    config = Config.load()
    theme_manager = ThemeManager(app, config)
    theme_manager.apply()
    music_dir = ask_library(config)
    if music_dir is None:
        return 0
    player = Player()
    controller = Controller(player)
    controller.initialize(music_dir, config.structure_library)
    window = MainWindow(controller, theme_manager, config)
    window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    window.show()
    try:
        return app.exec()
    finally:
        player.close()


if __name__ == "__main__":
    sys.exit(main())
