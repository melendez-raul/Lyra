from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, IntEnum
from pathlib import Path
from typing import TypeVar

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QBoxLayout,
    QCheckBox,
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

# ======================================================================
# ESTÁNDARES: todo valor compartido de la interfaz vive en este bloque
# ======================================================================

# --- config ------------------------------------------------------------
# colors
SWATCH_HEIGHT = 30
TRANSPARENCY_LABEL_WIDTH = 48
# fonts
SIZE_RANGE = (6, 200)
WEIGHT_RANGE = (100, 900)
SIZE_WIDTH = 90
WEIGHT_WIDTH = 90

# --- lyrics ------------------------------------------------------------
SCROLL_DURATION_MS = 400
RESUME_DELAY_MS = 3000

# --- player ------------------------------------------------------------
DEFAULT_SIZE = 300
HINT_WIDTH = 400


# --- rutas -------------------------------------------------------------
ICONS_DIR = Path(__file__).resolve().parent / "assets" / "icons"

# --- tamaños (px) ------------------------------------------------------
THUMB_SIZE = 75  # miniatura de portada en la lista
CHECK_SIZE = 22  # indicador del check (el radio del QSS es CHECK_SIZE // 2)
ICON_BUTTON_PADDING = 30  # espacio alrededor del icono dentro del botón
SCROLLBAR_GAP = 16  # aire entre el contenido y la barra de scroll

# --- tipos -------------------------------------------------------------
Margins = tuple[int, int, int, int]  # left, top, right, bottom
Callback = Callable[[], object]
BoolCallback = Callable[[bool], object]
IntCallback = Callable[[int], object]


class Radius(IntEnum):
    XS = 8
    SM = 14  # inputs, lyricItem, trackItem, albumArt
    MD = 18  # botones pill
    LG = 20  # QToolButton


class IconSize(IntEnum):
    SM = 24
    MD = 36
    LG = 50


@dataclass(frozen=True)
class Spacing:
    margins: Margins = (0, 0, 0, 0)
    gap: int = 0


class Level(Enum):
    """Espaciado estándar. Los márgenes los pone el panel; el gap, el contenedor."""

    # solo gap, de menor a mayor
    NONE = Spacing((0, 0, 0, 0), 0)  # hijos pegados o un solo hijo
    TIGHT = Spacing((0, 0, 0, 0), 4)  # líneas de texto apiladas
    LIST = Spacing((0, 0, 0, 0), 8)  # filas de una lista
    ROW = Spacing((0, 0, 0, 0), 12)  # elementos en una fila o grupo
    SECTION = Spacing((0, 0, 0, 0), 16)  # título + contenido
    PAGE = Spacing((0, 0, 0, 0), 28)  # secciones apiladas en un panel
    # con márgenes
    ITEM = Spacing((12, 12, 12, 12), 12)  # fila de lista con miniatura
    PANEL = Spacing((24, 24, 24, 24), 16)  # panel lateral o de contenido
    BAR = Spacing((24, 16, 24, 16), 0)  # cabecera de la ventana


class _Stretch:
    """Marcador para addStretch()."""


STRETCH = _Stretch()

Child = QWidget | QLayout | tuple[QWidget, int] | _Stretch  # (widget, stretch)
BoxLayout = TypeVar("BoxLayout", bound=QBoxLayout)


# ======================================================================
# WIDGET BASE
# ======================================================================


class AppWidget(QWidget):
    def __init__(self, object_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)


# ======================================================================
# ELEMENT
# Cada elemento usa el nombre de su tipo como objectName ("button",
# "input", "slider"...). Solo se cambia cuando el QSS necesita una regla
# propia (por ejemplo "playButton").
# ======================================================================


class Element:
    # ----------------------------------
    # LABELS
    # ----------------------------------

    @staticmethod
    def _label(text: str, name: str, wrap: bool) -> QLabel:
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
    def icon_button(
        icon: QIcon | str | Path,
        tooltip: str = "",
        icon_size: IconSize = IconSize.SM,
        object_name: str = "iconButton",
        on_click: Callback | None = None,
    ) -> QToolButton:
        """object_name solo se cambia si el QSS necesita una regla propia."""
        widget = QToolButton()
        widget.setObjectName(object_name)
        widget.setIcon(icon if isinstance(icon, QIcon) else QIcon(str(icon)))
        widget.setIconSize(QSize(icon_size, icon_size))
        size = icon_size + ICON_BUTTON_PADDING
        widget.setFixedSize(size, size)
        widget.setStyleSheet(
            f"QToolButton#{object_name} {{ border-radius: {size // 2}px; }}"
        )
        widget.setToolTip(tooltip)
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        widget.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        if on_click is not None:
            widget.clicked.connect(lambda _checked=False: on_click())
        return widget

    @staticmethod
    def check(
        text: str = "",
        checked: bool = False,
        on_toggle: BoolCallback | None = None,
        tooltip: str = "",
    ) -> QCheckBox:
        """Check redondo: lleno si está activo, vacío si no (lo dibuja el QSS)."""
        widget = QCheckBox(text)
        widget.setObjectName("check")
        widget.setChecked(checked)  # antes de conectar: no dispara el callback
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        widget.setToolTip(tooltip)
        if on_toggle is not None:
            widget.toggled.connect(on_toggle)
        return widget

    # ----------------------------------
    # INPUTS
    # ----------------------------------

    @staticmethod
    def input(placeholder: str = "", on_edit: Callback | None = None) -> QLineEdit:
        """on_edit: Enter o pérdida de foco."""
        widget = QLineEdit()
        widget.setObjectName("input")
        widget.setPlaceholderText(placeholder)
        if on_edit is not None:
            widget.editingFinished.connect(on_edit)
        return widget

    @staticmethod
    def slider(
        orientation: Qt.Orientation = Qt.Orientation.Horizontal,
        minimum: int = 0,
        maximum: int = 100,
        value: int = 0,
        on_change: IntCallback | None = None,
        on_press: Callback | None = None,
        on_move: IntCallback | None = None,
        on_release: Callback | None = None,
    ) -> QSlider:
        widget = ClickSlider(orientation)
        widget.setObjectName("slider")
        widget.setRange(minimum, maximum)
        widget.setValue(value)  # antes de conectar: no dispara callbacks
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

    @classmethod
    def scroll(
        cls,
        name: str,
        children: list[Child],
        level: Level = Level.SECTION,
        margins: Margins | None = None,
        horizontal: bool = True,
    ) -> QScrollArea:
        left, top, right, bottom = level.value.margins if margins is None else margins
        content = AppWidget(f"{name}Content")
        cls.main_layout(
            content, children, level, (left, top, right + SCROLLBAR_GAP, bottom)
        )
        area = QScrollArea()
        area.setObjectName(name)
        area.setWidgetResizable(True)
        area.setFrameShape(QScrollArea.Shape.NoFrame)
        if not horizontal:
            area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        area.setWidget(content)
        return area
