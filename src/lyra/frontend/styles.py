from backend.models import FONT_FAMILY, Color, Colors, Font, Fonts

from .rules import CHECK_SIZE, Radius

GROOVE = 6
HANDLE = 10
HANDLE_HOVER = 14
SCROLLBAR = 8


def build(colors: Colors, fonts: Fonts) -> str:
    """QSS completo. El orden importa: tema primero, estático después."""
    return "\n".join([_themed(colors, fonts), _static()])


# ----------------------------------------------------------------------
# Privado
# ----------------------------------------------------------------------


def _family(names: list[str]) -> str:
    return ", ".join(f'"{n}"' if " " in n else n for n in names)


def _font(f: Font) -> str:
    return (
        f"font-family: {_family(f.fonts)}; "
        f"font-size: {f.size}px; font-weight: {f.weight};"
    )


def _themed(c: Colors, f: Fonts) -> str:
    alpha = round(max(0, min(100, c.transparency)) * 255 / 100)

    def bg(color: Color) -> str:  # fondos con transparencia
        return color.to_qss(alpha)

    primary, secondary, tertiary = (
        c.primary.to_qss(),
        c.secondary.to_qss(),
        c.tertiary.to_qss(),
    )
    text, info, inactive = c.text.to_qss(), c.info.to_qss(), c.inactive.to_qss()
    half = CHECK_SIZE // 2

    return f"""
QWidget {{ color: {text}; }}
QWidget#playerPanel {{ background-color: {bg(c.player_bg)}; }}
QWidget#contentContainer {{ background-color: {bg(c.content_bg)}; }}

/* ===== TYPOGRAPHY ===== */
QLabel#h1 {{ color: {primary}; {_font(f.h1)} }}
QLabel#h2 {{ color: {text}; {_font(f.h2)} }}
QLabel#h3 {{ color: {text}; {_font(f.h3)} }}
QLabel#label {{ color: {text}; {_font(f.label)} }}
QLabel#info {{ color: {info}; {_font(f.info)} }}
QLabel#inactive {{ color: {inactive}; {_font(f.inactive)} }}

/* ===== BUTTONS ===== */
QPushButton {{ background-color: {bg(c.surface)}; color: {text}; }}
QPushButton:hover {{ background-color: {bg(c.hover)}; }}
QPushButton:pressed {{ background-color: {tertiary}; }}
QPushButton:focus {{ background-color: {bg(c.hover)}; }}
QPushButton:checked {{ background-color: {primary}; }}
QPushButton:disabled {{ color: {inactive}; background-color: {bg(c.content_bg)}; }}

/* ===== CHECK ===== */
QCheckBox#check {{ spacing: 12px; }}
QCheckBox#check::indicator {{
    width: {CHECK_SIZE}px; height: {CHECK_SIZE}px;
    border: 2px solid {primary};
    border-radius: {half}px;
    background: transparent;
}}
QCheckBox#check::indicator:hover {{ background: {bg(c.hover)}; }}
QCheckBox#check::indicator:checked {{ background: {primary}; }}

/* ===== INPUTS ===== */
QLineEdit {{
    background-color: {bg(c.surface)}; color: {text};
    selection-background-color: {primary};
}}
QLineEdit:hover {{ border-color: {bg(c.hover)}; }}
QLineEdit:focus {{ border: 1px solid {secondary}; }}
QLineEdit:read-only {{
    background-color: {bg(c.surface)}; color: {text}; border-color: {bg(c.hover)};
}}

/* ===== SLIDERS ===== */
QSlider#slider::groove:horizontal {{ background-color: {bg(c.hover)}; }}
QSlider#slider::sub-page:horizontal {{ background-color: {primary}; }}
QSlider#slider::handle:horizontal:pressed {{ background-color: {secondary}; }}
QSlider#slider::sub-page:horizontal:disabled {{ background-color: {inactive}; }}
QSlider#slider::handle:horizontal:disabled {{ background-color: {inactive}; }}

/* ===== SCROLLBARS ===== */
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{ background: {bg(c.hover)}; }}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{ background: {info}; }}
QScrollBar::handle:vertical:pressed, QScrollBar::handle:horizontal:pressed {{ background: {secondary}; }}

/* ===== ICON BUTTONS ===== */
QToolButton {{ color: {info}; }}
QToolButton:hover {{ background-color: {bg(c.hover)}; color: {text}; }}
QToolButton:pressed {{ background-color: {tertiary}; color: {text}; }}
QToolButton:checked {{ color: {secondary}; }}
QToolButton:disabled {{ color: {inactive}; }}

/* play: el #id gana a los QToolButton:hover/pressed de arriba */
QToolButton#playButton {{ background-color: {primary}; }}
QToolButton#playButton:hover {{ background-color: {primary}; }}
QToolButton#playButton:pressed {{ background-color: {secondary}; }}
QToolButton#playButton:disabled {{ background-color: {bg(c.surface)}; }}

/* ===== LYRICS ===== */
QWidget#lyricItem QLabel#lyric {{ color: {info}; {_font(f.lyric)} }}
QWidget#lyricItem[hovered="true"] {{ background-color: {bg(c.hover)}; }}
QWidget#lyricItem[hovered="true"] QLabel#lyric {{ color: {text}; }}
QWidget#lyricItem[active="true"] QLabel#lyric {{ color: {secondary}; {_font(f.lyric_active)} }}

/* ===== LIBRARY ===== */
QWidget#trackItem:hover {{ background-color: {bg(c.hover)}; }}
"""


def _static() -> str:
    margin = -((HANDLE - GROOVE) // 2)
    margin_hover = -((HANDLE_HOVER - GROOVE) // 2)
    return f"""
QWidget {{ font-family: {_family(FONT_FAMILY)}; font-size: 15px; }}

QScrollArea {{ background-color: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background-color: transparent; }}

/* ===== BUTTONS ===== */
QPushButton {{
    border: none; outline: none;
    border-radius: {Radius.MD}px;
    padding: 10px 22px;
    font-size: 14px; font-weight: 600;
}}

/* ===== INPUTS ===== */
QLineEdit {{
    border: 1px solid transparent;
    border-radius: {Radius.SM}px;
    padding: 11px 16px;
    font-size: 14px;
}}

/* ===== SLIDERS ===== */
QSlider#slider:horizontal {{ background: transparent; border: none; min-height: 22px; }}
QSlider#slider::groove:horizontal {{
    border: none; height: {GROOVE}px; border-radius: {GROOVE // 2}px;
}}
QSlider#slider::sub-page:horizontal {{ border-radius: {GROOVE // 2}px; }}
QSlider#slider::add-page:horizontal {{ background: transparent; }}
QSlider#slider::handle:horizontal {{
    background-color: white; border: none;
    width: {HANDLE}px; height: {HANDLE}px;
    margin: {margin}px 0; border-radius: {HANDLE // 2}px;
}}
QSlider#slider::handle:horizontal:hover,
QSlider#slider::handle:horizontal:pressed {{
    width: {HANDLE_HOVER}px; height: {HANDLE_HOVER}px;
    margin: {margin_hover}px 0; border-radius: {HANDLE_HOVER // 2}px;
}}

/* ===== SCROLLBARS ===== */
QScrollBar:vertical {{ background: transparent; width: {SCROLLBAR}px; margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: {SCROLLBAR}px; margin: 2px; }}
QScrollBar::handle:vertical {{ border-radius: 2px; min-height: 36px; }}
QScrollBar::handle:horizontal {{ border-radius: 2px; min-width: 36px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* ===== ICON BUTTONS (el radio lo pone Element.icon_button) ===== */
QToolButton {{
    background-color: transparent; border: none; outline: none; padding: 10px;
}}

/* ===== LYRICS ===== */
QWidget#lyricItem {{
    background-color: transparent;
    border-radius: {Radius.SM}px;
    border-left: 4px solid transparent;
}}
QWidget#lyricItem QLabel#lyric {{ background-color: transparent; }}
/* activa: después del hover (en _themed) para ganarle */
QWidget#lyricItem[active="true"] {{ background-color: transparent; }}

/* ===== LIBRARY ===== */
QWidget#trackItem {{ background-color: transparent; border-radius: {Radius.SM}px; }}
QWidget#trackItem QLabel {{ background-color: transparent; }}

/* ===== CONFIG ===== */
QPushButton#colorSwatch {{
    border: 1px solid rgba(255, 255, 255, 255);
    border-radius: {Radius.XS}px;
    padding: 0;
}}
"""
