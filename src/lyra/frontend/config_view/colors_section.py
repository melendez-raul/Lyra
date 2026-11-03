from backend.models import Color
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QWidget

from ..rules import (
    STRETCH,
    SWATCH_HEIGHT,
    TRANSPARENCY_LABEL_WIDTH,
    AppWidget,
    Element,
    Level,
)


class ColorEntry(AppWidget):
    color_changed = Signal(object)  # Color

    def __init__(self, name: str, color: Color, parent: QWidget | None = None) -> None:
        super().__init__("colorEntry", parent)
        self._color = color
        self.swatch = Element.button("", on_click=self._pick)
        self.swatch.setObjectName("colorSwatch")
        self.swatch.setFixedHeight(SWATCH_HEIGHT)
        self.main_layout = Element.main_layout(
            self, [Element.label(name), self.swatch], level=Level.TIGHT
        )
        self._paint()

    def _paint(self) -> None:
        self.swatch.setStyleSheet(f"background-color: {self._color.to_qss()};")

    def _pick(self) -> None:
        c = self._color
        dialog = QColorDialog(QColor(c.r, c.g, c.b), self)
        dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        if dialog.exec() != QColorDialog.DialogCode.Accepted:
            return
        picked = dialog.selectedColor()
        if not picked.isValid():
            return
        self._color = Color(picked.red(), picked.green(), picked.blue())
        self._paint()
        self.color_changed.emit(self._color)


class ColorsSection(AppWidget):
    transparency_changed = Signal(int)
    color_changed = Signal(str, object)  # clave, Color
    dynamic_colors_changed = Signal(bool)

    def __init__(
        self,
        colors: dict,  # Colors.to_dict(): hex y transparency
        dynamic_colors: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("colorsSection", parent)
        transparency = max(0, min(100, int(colors.get("transparency", 80))))
        self.dynamic_check = Element.check(
            "Colores dinámicos",
            checked=dynamic_colors,
            on_toggle=self.dynamic_colors_changed.emit,
            tooltip="Usar el color de la portada como acento",
        )
        self.transparency_value = Element.label(f"{transparency}%")
        self.transparency_value.setFixedWidth(TRANSPARENCY_LABEL_WIDTH)
        self.transparency_value.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.transparency_slider = Element.slider(
            value=transparency, on_change=self._on_transparency_changed
        )
        self.transparency_row = Element.row(
            [(self.transparency_slider, 1), self.transparency_value]
        )
        entries: list[ColorEntry] = []
        for key, value in colors.items():
            if key == "transparency":
                continue
            entry = ColorEntry(key.replace("_", " ").title(), Color.parse(value))
            entry.color_changed.connect(lambda c, k=key: self.color_changed.emit(k, c))
            entries.append(entry)
        self.main_layout = Element.main_layout(
            self,
            [
                Element.h2("Colors"),
                self.dynamic_check,
                Element.label("Background Transparency"),
                self.transparency_row,
                self._two_columns(entries),
            ],
            level=Level.SECTION,
        )

    @staticmethod
    def _two_columns(entries: list[ColorEntry]):
        """Reparte en zigzag: pares a la izquierda, impares a la derecha."""
        left = Element.column([*entries[0::2], STRETCH], level=Level.ROW)
        right = Element.column([*entries[1::2], STRETCH], level=Level.ROW)
        row = Element.row([left, right], level=Level.SECTION)
        row.setStretch(0, 1)
        row.setStretch(1, 1)
        return row

    def _on_transparency_changed(self, value: int) -> None:
        self.transparency_value.setText(f"{value}%")
        self.transparency_changed.emit(value)
