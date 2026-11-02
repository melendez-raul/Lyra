from PySide6.QtCore import Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QWidget

from ..rules import AppWidget, Element, Level

SIZE_RANGE = (6, 200)
WEIGHT_RANGE = (100, 900)
SIZE_WIDTH = 90
WEIGHT_WIDTH = 90


class FontEntry(AppWidget):
    font_changed = Signal(dict)  # {"size", "weight", "fonts"}

    def __init__(self, name: str, font: dict, parent: QWidget | None = None) -> None:
        super().__init__("fontEntry", parent)
        self._font = dict(font)
        self.size_input = Element.input("px", on_edit=self._on_edited)
        self.size_input.setValidator(QIntValidator(*SIZE_RANGE, self.size_input))
        self.size_input.setFixedWidth(SIZE_WIDTH)
        self.weight_input = Element.input("100-900", on_edit=self._on_edited)
        self.weight_input.setValidator(QIntValidator(*WEIGHT_RANGE, self.weight_input))
        self.weight_input.setFixedWidth(WEIGHT_WIDTH)
        self.fonts_input = Element.input(
            "Inter, Segoe UI, sans-serif", on_edit=self._on_edited
        )

        self.row = Element.row(
            [
                Element.info("Size"),
                self.size_input,
                Element.info("Weight"),
                self.weight_input,
                Element.info("Fonts"),
                (self.fonts_input, 1),
            ]
        )
        self.main_layout = Element.main_layout(
            self, [Element.label(name), self.row], level=Level.ROW
        )
        self._write_fields()

    def set_font(self, font: dict) -> None:
        self._font = dict(font)
        self._write_fields()

    def _write_fields(self) -> None:
        self.size_input.setText(str(self._font["size"]))
        self.weight_input.setText(str(self._font["weight"]))
        self.fonts_input.setText(", ".join(self._font["fonts"]))

    @staticmethod
    def _to_int(text: str, fallback: int) -> int:
        try:
            return int(text)
        except ValueError:
            return fallback

    def _on_edited(self) -> None:
        names = (n.strip().strip("\"'") for n in self.fonts_input.text().split(","))
        font = {
            "size": self._to_int(self.size_input.text(), self._font["size"]),
            "weight": self._to_int(self.weight_input.text(), self._font["weight"]),
            "fonts": [n for n in names if n] or self._font["fonts"],
        }
        old, self._font = self._font, font
        self._write_fields()
        if font != old:
            self.font_changed.emit(font)


class FontsSection(AppWidget):
    font_changed = Signal(str, dict)  # key, {"size", "weight", "fonts"}

    def __init__(self, fonts: dict, parent: QWidget | None = None) -> None:
        super().__init__("fontsSection", parent)
        self.font_entries: dict[str, FontEntry] = {}
        for key, font in fonts.items():
            entry = FontEntry(key.replace("_", " ").title(), font)
            entry.font_changed.connect(lambda f, k=key: self.font_changed.emit(k, f))
            self.font_entries[key] = entry

        self.main_layout = Element.main_layout(
            self,
            [Element.h2("Fonts"), *self.font_entries.values()],
            level=Level.SECTION,
        )

    def set_font(self, key: str, font: dict) -> None:
        if key in self.font_entries:
            self.font_entries[key].set_font(font)
