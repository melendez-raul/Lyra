from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QWidget

from ..rules import AppWidget, Element, Level


class LibraryPathEntry(AppWidget):
    path_changed = Signal(str)

    def __init__(
        self, library_path: str | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__("libraryPathEntry", parent)
        self.path_input = Element.input()
        self.path_input.setReadOnly(True)
        self.path_input.setText(library_path or "")
        self.path_row = Element.row(
            [
                (self.path_input, 1),
                Element.button("Buscar", on_click=self._select_directory),
            ],
            level=Level.LIST,
        )
        self.main_layout = Element.main_layout(
            self, [Element.h2("Library Path"), self.path_row], level=Level.ROW
        )

    def _select_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Selecciona un directorio", self.path_input.text()
        )
        if directory:
            self.path_input.setText(directory)
            self.path_changed.emit(directory)
