from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QWidget

from ..rules import AppWidget, Element, Level


class LibraryPathEntry(AppWidget):
    path_changed = Signal(str)

    def __init__(
        self, library_path: str | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__("libraryPathEntry", parent)
        self.title = Element.h2("Library Path")
        self.path_input = Element.input(library_path or "")
        self.path_input.setReadOnly(True)
        self.browse_button = Element.button("Buscar", on_click=self.select_directory)
        self.path_layout = Element.row(
            [(self.path_input, 1), self.browse_button], level=Level.TIGHT
        )
        self.main_layout = Element.main_layout(
            self, [self.title, self.path_layout], level=Level.ROW
        )

    def select_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Selecciona un directorio", self.path_input.text()
        )
        if not directory:
            return
        self.set_path(directory)
        self.path_changed.emit(directory)

    def set_path(self, path: str) -> None:
        self.path_input.setText(path)
