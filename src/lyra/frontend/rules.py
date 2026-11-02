import atexit
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, IntEnum
from pathlib import Path
from typing import ClassVar, TypeVar

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QBoxLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .custom_elements import ClickSlider

# ==================================
# CONSTANTS
# ==================================

Margins = tuple[int, int, int, int]  # left, top, right, bottom

ICON_PADDING = 30  # espacio alrededor del icono dentro del botón
DEFAULT_ICON_BUTTON = "iconButton"

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
SELECTORS_FILE = BASE_DIR / "selectors.txt"


# ==================================
# TYPES
# ==================================

Callback = Callable[[], object]  # click, editingFinished
BoolCallback = Callable[[bool], object]  # toggled
TextCallback = Callable[[str], object]  # textChanged
IntCallback = Callable[[int], object]  # valueChanged


class Radius(IntEnum):
    SM = 14  # inputs, albumArt, lyricItem, trackItem
    MD = 18  # botones pill
    LG = 20  # QToolButton
    FULL = 9999  # círculo / pill completo (se recorta al lado menor)


class IconSize(IntEnum):
    SM = 24
    MD = 36
    LG = 50


@dataclass(frozen=True)
class Spacing:
    margins: Margins = (0, 0, 0, 0)
    gap: int = 0


THUMB_SIZE = 75


class Level(Enum):
    NONE = Spacing((0, 0, 0, 0), 0)
    SECTION = Spacing((0, 0, 0, 0), 16)
    ROW = Spacing((0, 0, 0, 0), 12)
    PANEL = Spacing((24, 24, 24, 24), 16)
    BAR = Spacing((24, 16, 24, 16), 0)  # cabecera de la ventana
    ITEM = Spacing((12, 12, 12, 12), 12)  # fila de lista con miniatura
    LIST = Spacing((0, 0, 0, 0), 8)  # separación entre filas
    TIGHT = Spacing((0, 0, 0, 0), 4)  # líneas de texto apiladas
    PAGE = Spacing((0, 0, 0, 0), 28)  # secciones apiladas dentro de un panel


class _Stretch:
    """Marcador para addStretch()."""


STRETCH = _Stretch()

Child = QWidget | QLayout | tuple[QWidget, int] | _Stretch  # (widget, stretch_factor)

BoxLayout = TypeVar("BoxLayout", bound=QBoxLayout)


# ==================================
# ELEMENT
# ==================================


class Element:
    _selectors: ClassVar[set[str]] = set()

    # ----------------------------------
    # SELECTOR REGISTRY
    # ----------------------------------

    @classmethod
    def _register(cls, widget: QWidget) -> None:
        """Anota 'Tipo#nombre' para revisar después qué selectores necesita el QSS."""
        cls._selectors.add(f"{type(widget).__name__}#{widget.objectName()}")

    @classmethod
    def dump_selectors(cls, path: Path = SELECTORS_FILE) -> None:
        if cls._selectors:
            path.write_text("\n".join(sorted(cls._selectors)) + "\n", encoding="utf-8")

    # ----------------------------------
    # LABELS
    # ----------------------------------

    @staticmethod
    def _label(text: str, name: str, wrap: bool = False) -> QLabel:
        widget = QLabel(text)
        widget.setObjectName(name)
        if wrap:
            widget.setWordWrap(True)
            widget.setAlignment(Qt.AlignmentFlag.AlignLeft)
        return widget

    @classmethod
    def h1(cls, text: str = "", wrap: bool = False) -> QLabel:
        return cls._label(text, "h1", wrap)

    @classmethod
    def h2(cls, text: str = "", wrap: bool = False) -> QLabel:
        return cls._label(text, "h2", wrap)

    @classmethod
    def h3(cls, text: str = "", wrap: bool = False) -> QLabel:
        return cls._label(text, "h3", wrap)

    @classmethod
    def label(cls, text: str = "", wrap: bool = False) -> QLabel:
        return cls._label(text, "label", wrap)

    @classmethod
    def info(cls, text: str = "", wrap: bool = False) -> QLabel:
        return cls._label(text, "info", wrap)

    @classmethod
    def inactive(cls, text: str = "", wrap: bool = False) -> QLabel:
        return cls._label(text, "inactive", wrap)

    @classmethod
    def lyric(cls, text: str = "", wrap: bool = False) -> QLabel:
        return cls._label(text, "lyric", wrap)

    # ----------------------------------
    # BUTTONS
    # ----------------------------------

    @staticmethod
    def button(text: str, on_click: Callback | None = None) -> QPushButton:
        widget = QPushButton(text)
        widget.setObjectName("button")
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        if on_click is not None:
            widget.clicked.connect(lambda _checked=False: on_click())
        return widget

    @staticmethod
    def toggle_button(
        text: str,
        object_name: str = "toggleButton",
        checked: bool = False,
        on_toggle: BoolCallback | None = None,
    ) -> QPushButton:
        widget = QPushButton(text)
        widget.setObjectName(object_name)
        widget.setCheckable(True)
        widget.setChecked(checked)  # antes de conectar: no dispara el callback
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        if on_toggle is not None:
            widget.toggled.connect(on_toggle)
        return widget

    @classmethod
    def icon_button(
        cls,
        icon: QIcon | str | Path,
        tooltip: str = "",
        icon_size: IconSize = IconSize.SM,
        object_name: str = DEFAULT_ICON_BUTTON,
        on_click: Callback | None = None,
    ) -> QToolButton:
        widget = QToolButton()
        widget.setObjectName(object_name)
        widget.setProperty("appRole", "iconButton")
        widget.setIcon(icon if isinstance(icon, QIcon) else QIcon(str(icon)))
        widget.setIconSize(QSize(icon_size, icon_size))
        button_size = icon_size + ICON_PADDING
        widget.setFixedSize(button_size, button_size)
        widget.setStyleSheet(
            f"QToolButton#{object_name} {{ border-radius: {button_size // 2}px; }}"
        )
        widget.setToolTip(tooltip)
        widget.setAccessibleName(tooltip)
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        widget.setMouseTracking(True)
        widget.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        if on_click is not None:
            widget.clicked.connect(lambda _checked=False: on_click())
        if object_name != DEFAULT_ICON_BUTTON:
            cls._register(widget)
        return widget

    # ----------------------------------
    # INPUTS
    # ----------------------------------

    @staticmethod
    def input(
        placeholder: str = "",
        on_edit: Callback | None = None,
        on_change: TextCallback | None = None,
    ) -> QLineEdit:
        """on_edit: Enter o pérdida de foco. on_change: en cada tecla."""
        widget = QLineEdit()
        widget.setObjectName("input")
        widget.setPlaceholderText(placeholder)
        if on_edit is not None:
            widget.editingFinished.connect(on_edit)
        if on_change is not None:
            widget.textChanged.connect(on_change)
        return widget

    @staticmethod
    def slider(
        orientation: Qt.Orientation = Qt.Orientation.Horizontal,
        minimum: int = 0,
        maximum: int = 100,
        value: int = 0,
        clickable: bool = True,
        on_change: IntCallback | None = None,  # valueChanged
        on_press: Callback | None = None,  # sliderPressed
        on_move: IntCallback | None = None,  # sliderMoved (solo el usuario)
        on_release: Callback | None = None,  # sliderReleased
    ) -> QSlider:
        widget = ClickSlider(orientation) if clickable else QSlider(orientation)
        widget.setObjectName("appSlider")
        widget.setRange(minimum, maximum)
        widget.setValue(value)
        if on_change is not None:
            widget.valueChanged.connect(on_change)
        if on_press is not None:
            widget.sliderPressed.connect(on_press)
        if on_move is not None:
            widget.sliderMoved.connect(on_move)
        if on_release is not None:
            widget.sliderReleased.connect(on_release)
        return widget

    # ----------------------------------
    # CONTAINERS
    # ----------------------------------

    @staticmethod
    def card() -> QFrame:
        widget = QFrame()
        widget.setObjectName("card")
        return widget

    # ----------------------------------
    # LAYOUTS
    # ----------------------------------

    @staticmethod
    def _fill(
        layout: BoxLayout,
        children: list[Child],
        level: Level,
        margins: Margins | None,
    ) -> BoxLayout:
        spacing = level.value
        layout.setContentsMargins(*(spacing.margins if margins is None else margins))
        layout.setSpacing(spacing.gap)
        for child in children:
            if isinstance(child, _Stretch):
                layout.addStretch()
            elif isinstance(child, tuple):
                widget, stretch = child
                layout.addWidget(widget, stretch)
            elif isinstance(child, QLayout):
                layout.addLayout(child)
            else:
                layout.addWidget(child)
        return layout

    @classmethod
    def column(
        cls,
        children: list[Child],
        level: Level = Level.SECTION,
        parent: QWidget | None = None,
        margins: Margins | None = None,
    ) -> QVBoxLayout:
        return cls._fill(QVBoxLayout(parent), children, level, margins)  # pyright: ignore[reportArgumentType]

    @classmethod
    def row(
        cls,
        children: list[Child],
        level: Level = Level.ROW,
        parent: QWidget | None = None,
        margins: Margins | None = None,
    ) -> QHBoxLayout:
        return cls._fill(QHBoxLayout(parent), children, level, margins)  # pyright: ignore[reportArgumentType]

    @classmethod
    def main_layout(
        cls,
        parent: QWidget,
        children: list[Child],
        level: Level = Level.PANEL,
        margins: Margins | None = None,
    ) -> QVBoxLayout:
        """Layout vertical raíz: se instala directamente en `parent`."""
        return cls.column(children, level, parent, margins)

    @staticmethod
    def scroll(
        name: str,
        children: list[Child],
        level: Level = Level.SECTION,
        margins: Margins | None = None,
        horizontal: bool = True,
    ) -> QScrollArea:
        content = AppWidget(f"{name}Content")
        Element.main_layout(content, children, level, margins)
        area = QScrollArea()
        area.setObjectName(name)
        area.setWidgetResizable(True)
        area.setFrameShape(QScrollArea.Shape.NoFrame)
        if not horizontal:
            area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        area.setWidget(content)
        return area


# ==================================
# BASE WIDGET
# ==================================


class AppWidget(QWidget):
    def __init__(self, object_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)


atexit.register(Element.dump_selectors)
