import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QWidget

from ..rules import STRETCH, AppWidget, Element, Level

_RGB = re.compile(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)")
SWATCH_HEIGHT = 30


def parse_rgb(color: str) -> tuple[int, int, int] | None:
    match = _RGB.fullmatch(color)
    return tuple(map(int, match.groups())) if match else None  # type: ignore[return-value]


class ColorEntry(AppWidget):
    color_changed = Signal(str)  # "rgb(r, g, b)"

    def __init__(self, name: str, color: str, parent: QWidget | None = None) -> None:
        super().__init__("colorEntry", parent)
        self._color = color
        self.swatch = Element.button("", on_click=self._pick)
        self.swatch.setObjectName("colorSwatch")
        self.swatch.setFixedHeight(SWATCH_HEIGHT)
        self.main_layout = Element.main_layout(
            self, [Element.label(name), self.swatch], level=Level.TIGHT
        )
        self.set_color(color)

    def set_color(self, color: str) -> None:
        self._color = color
        self.swatch.setStyleSheet(f"background-color: {color};")

    def _pick(self) -> None:
        rgb = parse_rgb(self._color)
        if rgb is None:
            return
        dialog = QColorDialog(QColor(*rgb), self)
        dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        if dialog.exec() != QColorDialog.DialogCode.Accepted:
            return
        picked = dialog.selectedColor()
        if not picked.isValid():
            return
        color = f"rgb({picked.red()}, {picked.green()}, {picked.blue()})"
        self.set_color(color)
        self.color_changed.emit(color)


TRANSPARENCY_LABEL_WIDTH = 50


class ColorsSection(AppWidget):
    transparency_changed = Signal(int)
    color_changed = Signal(str, str)

    def __init__(self, colors: dict, parent: QWidget | None = None) -> None:
        super().__init__("themeSection", parent)
        transparency = max(0, min(100, int(colors.get("transparency", 85))))
        self.transparency_value = Element.label(f"{transparency}%")
        self.transparency_value.setFixedWidth(TRANSPARENCY_LABEL_WIDTH)
        self.transparency_value.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.transparency_slider = Element.slider(
            value=transparency, on_change=self._on_transparency_changed
        )
        self.transparency_layout = Element.row(
            [(self.transparency_slider, 1), self.transparency_value]
        )
        self.color_entries: dict[str, ColorEntry] = {}
        columns: tuple[list[ColorEntry], list[ColorEntry]] = ([], [])
        index = 0
        for key, color in colors.items():
            if key == "transparency":
                continue
            entry = ColorEntry(key.replace("_", " ").title(), color)
            entry.color_changed.connect(lambda c, k=key: self.color_changed.emit(k, c))
            self.color_entries[key] = entry
            columns[index % 2].append(entry)
            index += 1
        left = Element.column([*columns[0], STRETCH], level=Level.ROW)
        right = Element.column([*columns[1], STRETCH], level=Level.ROW)
        self.colors_layout = Element.row([left, right], level=Level.SECTION)
        self.colors_layout.setStretch(0, 1)
        self.colors_layout.setStretch(1, 1)
        self.main_layout = Element.main_layout(
            self,
            [
                Element.h2("Colors"),
                Element.label("Background Transparency"),
                self.transparency_layout,
                self.colors_layout,
            ],
            level=Level.SECTION,
        )

    def _on_transparency_changed(self, value: int) -> None:
        self.transparency_value.setText(f"{value}%")
        self.transparency_changed.emit(value)

    def set_color(self, key: str, color: str) -> None:
        if key in self.color_entries:
            self.color_entries[key].set_color(color)
