"""Design tokens and Qt stylesheet builders.

Values mirror ``docs/design/design-handoff.md`` so the GUI tracks the hi-fi
prototype. Tokens are flat dicts of color hex strings; ``build_stylesheet``
renders a single Qt Style Sheet that themes the whole window.
"""

from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

LIGHT_TOKENS: dict[str, str] = {
    "bg": "#f0ede7",
    "panel": "#ffffff",
    "panel2": "#f7f5f1",
    "border": "#dedad0",
    "border_s": "#c0bbb0",
    "text": "#1a1826",
    "text_sub": "#706c84",
    "text_dim": "#a8a4b8",
    "accent": "#5248c8",
    "accent_bg": "#eeedfb",
    "accent_text": "#3830a0",
    "fixed_bg": "#eef4fd",
    "fixed_bdr": "#b8d0f0",
    "fixed_hdr": "#dce8fb",
    "uncat_bg": "#fffbf0",
    "uncat_bdr": "#d49820",
    "uncat_hdr": "#fef3d0",
    "menu_bg": "#e8e5de",
    "tool_bg": "#edeae3",
    "status_bg": "#1e1c2a",
    "status_fg": "#d8d6e8",
    "drag_over": "#e8e6fb",
    "drag_bdr": "#5248c8",
    "drag_reject": "#c03010",
}

DARK_TOKENS: dict[str, str] = {
    "bg": "#16151f",
    "panel": "#21202e",
    "panel2": "#28273a",
    "border": "#363448",
    "border_s": "#504e68",
    "text": "#e8e6f4",
    "text_sub": "#9290a8",
    "text_dim": "#5a5870",
    "accent": "#8b7ff0",
    "accent_bg": "#26244a",
    "accent_text": "#b0a8f8",
    "fixed_bg": "#1c2238",
    "fixed_bdr": "#304880",
    "fixed_hdr": "#222c48",
    "uncat_bg": "#221c0e",
    "uncat_bdr": "#a07820",
    "uncat_hdr": "#2e2008",
    "menu_bg": "#1c1b28",
    "tool_bg": "#1a1928",
    "status_bg": "#0d0c16",
    "status_fg": "#c8c6dc",
    "drag_over": "#2a2848",
    "drag_bdr": "#8b7ff0",
    "drag_reject": "#e74c3c",
}

FONT_FAMILY = "DM Sans, system-ui, sans-serif"


_TEMPLATE = """
QMainWindow, QWidget {{
    background: {bg};
    color: {text};
    font-family: {font_family};
    font-size: 13px;
}}
QMenuBar {{
    background: {menu_bg};
    border-bottom: 1px solid {border};
    padding: 0;
}}
QMenuBar::item {{
    padding: 3px 10px;
}}
QMenuBar::item:selected {{
    background: {accent};
    color: white;
}}
QMenu {{
    background: {panel};
    border: 1px solid {border};
    color: {text};
}}
QMenu::item:selected {{
    background: {accent};
    color: white;
}}
QToolBar {{
    background: {tool_bg};
    border-bottom: 1px solid {border};
    spacing: 6px;
    padding: 4px 8px;
}}
QStatusBar {{
    background: {status_bg};
    color: {status_fg};
    font-size: 12px;
}}
QFrame#CatTile, QFrame#BasicLandsTile, QFrame#CardInspector {{
    background: {panel};
    border: 1px solid {border};
    border-radius: 7px;
}}
QFrame#CatTile[fixedCat="true"], QFrame#BasicLandsTile {{
    background: {fixed_bg};
    border: 1px solid {fixed_bdr};
}}
QFrame#CatTile[dragOk="true"] {{
    border: 2px solid {drag_bdr};
    background: {drag_over};
}}
QFrame#CatTile[dragReject="true"] {{
    border: 2px solid {drag_reject};
}}
QFrame#UncatSidebar {{
    background: {uncat_bg};
    border-left: 2px dashed {uncat_bdr};
}}
QLabel#DeckName {{
    font-size: 15px;
    font-weight: 600;
}}
QLabel#DeckSub {{
    color: {text_sub};
    font-size: 12px;
}}
QLabel#CatName {{
    font-weight: 600;
    font-size: 13px;
}}
QLabel#CountBadge {{
    background: {panel2};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 1px 6px;
    color: {text_sub};
}}
QLabel#CountBadge[full="true"] {{
    background: {accent_bg};
    color: {accent_text};
    border: 1px solid {accent};
}}
QListView {{
    background: transparent;
    border: none;
    outline: 0;
}}
QListView::item {{
    padding: 4px 10px;
    border-bottom: 1px solid {border};
}}
QListView::item:selected {{
    background: {accent_bg};
    color: {accent_text};
    border-left: 2px solid {accent};
}}
QPushButton {{
    background: {panel};
    border: 1px solid {border};
    border-radius: 5px;
    padding: 3px 10px;
}}
QPushButton:hover {{
    background: {panel2};
}}
QPushButton:disabled {{
    color: {text_dim};
}}
"""


def build_stylesheet(tokens: dict[str, str]) -> str:
    """Render a Qt stylesheet string from a token dict."""
    return _TEMPLATE.format(font_family=FONT_FAMILY, **tokens)


def apply_theme(app: QApplication, theme: str = "light") -> None:
    """Apply the named theme's stylesheet to *app*. ``theme`` is light or dark."""
    tokens = DARK_TOKENS if theme == "dark" else LIGHT_TOKENS
    app.setStyleSheet(build_stylesheet(tokens))
    font = QFont()
    font.setFamilies(["DM Sans", "system-ui", "sans-serif"])
    font.setPointSize(10)
    app.setFont(font)
