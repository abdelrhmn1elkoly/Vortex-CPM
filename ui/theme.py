"""Authentic Windows 11 Fluent Design & Mica Material System for Vortex Controls.
Directly implements the official DWM system backdrop materials from Vortex PT:
- Mica (DWMSBT_MAINWINDOW, value 2)
- Mica Old / Mica Alt (DWMSBT_TABBEDWINDOW, value 4)
- Acrylic (DWMSBT_TRANSIENTWINDOW, value 3)
- Dark Solid (DWMSBT_NONE, value 1)
Provides live theme switching, dynamic QSS generation, and DWM window integration.
"""

from __future__ import annotations
import sys
import ctypes
from typing import Dict, Any, Optional

THEME_PALETTES: Dict[str, Dict[str, Any]] = {
    "mica": {
        "id": "mica",
        "name": "Mica",
        "description": "Windows 11 Mica material desktop wallpaper tint",
        "bg": "#20232A",
        "root_bg": "rgba(32, 35, 42, 0.72)",
        "panel": "#282C34",
        "card": "#2F3440",
        "card_hover": "#363C4A",
        "stroke": "#3D4452",
        "accent": "#60CDFF",
        "accent_hover": "#78D5FF",
        "text_primary": "#FFFFFF",
        "text_secondary": "#9E9E9E",
        "dwm_val": 2,  # DWMSBT_MAINWINDOW
    },
    "mica_alt": {
        "id": "mica_alt",
        "name": "Mica Old",
        "description": "Windows 11 Tabbed Mica Alt deeper material",
        "bg": "#18191B",
        "root_bg": "rgba(24, 25, 27, 0.82)",
        "panel": "#202124",
        "card": "#26282B",
        "card_hover": "#2E3034",
        "stroke": "#36383D",
        "accent": "#00E5FF",
        "accent_hover": "#33EBFF",
        "text_primary": "#FFFFFF",
        "text_secondary": "#94A3B8",
        "dwm_val": 4,  # DWMSBT_TABBEDWINDOW
    },
    "acrylic": {
        "id": "acrylic",
        "name": "Acrylic",
        "description": "Windows 11 Acrylic translucent backdrop",
        "bg": "#1A202C",
        "root_bg": "rgba(26, 32, 44, 0.60)",
        "panel": "#222A38",
        "card": "#2A3446",
        "card_hover": "#323E54",
        "stroke": "#38455C",
        "accent": "#38BDF8",
        "accent_hover": "#60A5FA",
        "text_primary": "#FFFFFF",
        "text_secondary": "#A0AEC0",
        "dwm_val": 3,  # DWMSBT_TRANSIENTWINDOW
    },
    "solid_dark": {
        "id": "solid_dark",
        "name": "Dark Solid",
        "description": "Opaque high-contrast studio dark theme",
        "bg": "#121212",
        "root_bg": "#121212",
        "panel": "#1A1A1A",
        "card": "#222222",
        "card_hover": "#2A2A2A",
        "stroke": "#2E2E2E",
        "accent": "#0078D4",
        "accent_hover": "#1084D9",
        "text_primary": "#FFFFFF",
        "text_secondary": "#888888",
        "dwm_val": 1,  # DWMSBT_NONE
    }
}

ACTIVE_THEME = "mica"


def generate_theme_qss(theme_id: str = "mica") -> str:
    """Generates a complete, tailored Qt stylesheet matching the specified theme palette."""
    pal = THEME_PALETTES.get(theme_id, THEME_PALETTES["mica"])

    bg = pal["bg"]
    root_bg = pal.get("root_bg", bg)
    panel = pal["panel"]
    card = pal["card"]
    card_hover = pal["card_hover"]
    stroke = pal["stroke"]
    accent = pal["accent"]
    accent_hover = pal["accent_hover"]
    text_primary = pal["text_primary"]
    text_sec = pal["text_secondary"]

    return f"""
    /* Base Window */
    QMainWindow, QWidget#MainRoot {{
        background-color: {root_bg};
        color: {text_primary};
        font-family: 'Segoe UI Variable Display', 'Segoe UI Variable Text', 'Segoe UI', system-ui, sans-serif;
        font-size: 13px;
    }}

    /* Left Navigation Rail */
    QFrame#NavRail {{
        background-color: {panel};
        border-right: 1px solid {stroke};
    }}

    /* Hamburger Button */
    QPushButton#HamburgerBtn {{
        background-color: transparent;
        border: none;
        border-radius: 6px;
        padding: 8px;
        margin: 8px 6px;
    }}

    QPushButton#HamburgerBtn:hover {{
        background-color: {card_hover};
    }}

    /* Nav Rail Item */
    QFrame#NavRailItem {{
        background-color: transparent;
        border-radius: 6px;
        margin: 2px 6px;
        border: none;
    }}

    QFrame#NavRailItem:hover {{
        background-color: {card_hover};
    }}

    QFrame#NavRailItem[active="true"] {{
        background-color: {card};
    }}

    QFrame#NavAccentBar {{
        background-color: {accent};
        border-radius: 1.5px;
    }}

    QLabel#NavLabel {{
        color: {text_sec};
        font-size: 13px;
        font-weight: 500;
    }}

    QLabel#NavLabel[active="true"] {{
        color: {text_primary};
        font-weight: 600;
    }}

    /* Topbar Header */
    QFrame#Topbar {{
        background-color: {panel};
        border-bottom: 1px solid {stroke};
    }}

    QLabel#TopbarTitle {{
        font-size: 16px;
        font-weight: 700;
        color: {text_primary};
        letter-spacing: 0.3px;
    }}

    QLabel#TopbarSub {{
        font-size: 11px;
        color: {text_sec};
    }}

    /* Cards & Panels */
    QFrame#Card, QFrame#KpiCard, QFrame#InspectorCard, QFrame#SidebarCard {{
        background-color: {card};
        border: 1px solid {stroke};
        border-radius: 8px;
    }}

    /* Secondary Sidebar (Layers & Metrics) */
    QFrame#SideToolPane {{
        background-color: {panel};
        border-right: 1px solid {stroke};
    }}

    QPushButton#SubtleLinkBtn {{
        background: transparent;
        border: none;
        color: {accent};
        font-size: 11px;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
    }}

    QPushButton#SubtleLinkBtn:hover {{
        background-color: {card_hover};
    }}

    /* WinUI 3 Toggle Switch Styling */
    QCheckBox {{
        spacing: 6px;
    }}

    QCheckBox::indicator {{
        width: 32px;
        height: 18px;
        border-radius: 9px;
        border: 1px solid {stroke};
        background-color: {panel};
    }}

    QCheckBox::indicator:checked {{
        background-color: {accent};
        border: 1px solid {accent};
    }}

    QCheckBox::indicator:hover {{
        border: 1px solid {accent};
    }}

    QFrame#KpiCard:hover {{
        background-color: {card_hover};
        border-color: {accent};
    }}

    QLabel#KpiTitle {{
        font-size: 11px;
        font-weight: 600;
        color: {text_sec};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    QLabel#KpiVal {{
        font-size: 22px;
        font-weight: 700;
        color: {text_primary};
    }}

    QLabel#KpiSub {{
        font-size: 11px;
        color: {text_sec};
    }}

    /* Status Footer Bar (Vortex PT Parity) */
    QFrame#StatusFooter {{
        background-color: {panel};
        border-top: 1px solid {stroke};
        min-height: 28px;
        max-height: 28px;
    }}

    QLabel#FooterStatusText {{
        font-size: 11px;
        color: {text_sec};
        font-weight: 500;
    }}

    QLabel#FooterSelectionText {{
        font-size: 11px;
        color: {text_primary};
        font-weight: 600;
        padding: 0 8px;
        border-left: 1px solid {stroke};
        border-right: 1px solid {stroke};
    }}

    QLabel#FooterMetricsText {{
        font-size: 11px;
        color: {text_sec};
        font-family: 'Consolas', 'Segoe UI', monospace;
    }}

    /* Inputs */
    QLineEdit#PillSearch {{
        background-color: {panel};
        border: 1px solid {stroke};
        border-radius: 6px;
        padding: 6px 12px;
        color: {text_primary};
        font-size: 12px;
    }}

    QLineEdit#PillSearch:focus {{
        border: 1px solid {accent};
        background-color: {bg};
    }}

    /* Buttons */
    QPushButton#PrimaryBtn {{
        background-color: {accent};
        color: #0F172A;
        border: 1px solid {accent_hover};
        border-radius: 6px;
        padding: 6px 16px;
        font-size: 12px;
        font-weight: 700;
    }}

    QPushButton#PrimaryBtn:hover {{
        background-color: {accent_hover};
    }}

    QPushButton#ActionBtn {{
        background-color: {card};
        color: {text_primary};
        border: 1px solid {stroke};
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 12px;
        font-weight: 500;
    }}

    QPushButton#ActionBtn:hover {{
        background-color: {card_hover};
        border-color: {accent};
    }}

    /* Filter Chips */
    QPushButton#FilterChip {{
        background-color: {panel};
        color: {text_sec};
        border: 1px solid {stroke};
        border-radius: 6px;
        padding: 4px 12px;
        font-size: 11px;
        font-weight: 500;
    }}

    QPushButton#FilterChip:hover {{
        background-color: {card_hover};
        color: {text_primary};
    }}

    QPushButton#FilterChip[checked="true"] {{
        background-color: {card};
        border-color: {accent};
        color: {accent};
        font-weight: 700;
    }}

    /* Tables */
    QTableWidget {{
        background-color: {card};
        border: 1px solid {stroke};
        border-radius: 8px;
        gridline-color: {stroke};
        color: {text_primary};
        selection-background-color: {card_hover};
        selection-color: {accent};
        font-size: 12px;
        outline: none;
    }}

    QTableWidget::item {{
        padding: 6px 10px;
        border-bottom: 1px solid {stroke};
    }}

    QHeaderView::section {{
        background-color: {panel};
        color: {text_sec};
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        padding: 8px 10px;
        border: none;
        border-bottom: 1px solid {stroke};
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        border: none;
        background: transparent;
        width: 8px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background: {stroke};
        min-height: 24px;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {accent};
    }}
    """


def apply_dwm_backdrop(target: Any, theme_id: str = "mica") -> bool:
    """Applies Windows 11 DWM backdrop material (Mica, Mica Old, Acrylic, or Dark Solid)
    with native rounded corners, dark title bar, and distinct theme palettes.
    """
    if not sys.platform.startswith("win"):
        return False

    pal = THEME_PALETTES.get(theme_id, THEME_PALETTES["mica"])
    dwm_val = pal["dwm_val"]

    try:
        from PySide6.QtCore import Qt
        if hasattr(target, "winId"):
            hwnd = int(target.winId())
            window_widget = target
        else:
            hwnd = int(target)
            window_widget = None

        # 1. Dark Mode title bar (20 for Win11/Win10 20H1+, 19 for older Win10)
        dark = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark), ctypes.sizeof(dark))
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(dark), ctypes.sizeof(dark))

        # 2. Window Corner Preference (33: 2 = DWMWCP_ROUND)
        round_corners = ctypes.c_int(2)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(round_corners), ctypes.sizeof(round_corners))

        # 3. Border Color (34: #383838)
        border_color = ctypes.c_int(0x383838)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 34, ctypes.byref(border_color), ctypes.sizeof(border_color))

        # 4. Apply authentic Windows 11 Backdrop Material
        applied_backdrop = False
        try:
            from qframelesswindow import WindowEffect
            we = WindowEffect(window_widget) if window_widget else WindowEffect()
            if theme_id == "mica":
                we.setMicaEffect(hwnd, isDarkMode=True, isAlt=False)
                applied_backdrop = True
            elif theme_id == "mica_alt":
                we.setMicaEffect(hwnd, isDarkMode=True, isAlt=True)
                applied_backdrop = True
            elif theme_id == "acrylic":
                we.setAcrylicEffect(hwnd, gradientColor="1A202C99")
                applied_backdrop = True
            else:
                we.removeBackgroundEffect(hwnd)
                applied_backdrop = True
        except Exception:
            pass

        if not applied_backdrop:
            # Fallback to direct DwmSetWindowAttribute
            backdrop = ctypes.c_int(dwm_val)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 38, ctypes.byref(backdrop), ctypes.sizeof(backdrop))
            if theme_id != "solid_dark":
                class _MARGINS(ctypes.Structure):
                    _fields_ = [('cxLeftWidth', ctypes.c_int), ('cxRightWidth', ctypes.c_int), ('cyTopHeight', ctypes.c_int), ('cyBottomHeight', ctypes.c_int)]
                mrg = _MARGINS(-1, -1, -1, -1)
                ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(mrg))

        if window_widget is not None:
            if theme_id == "solid_dark":
                window_widget.setAttribute(Qt.WA_TranslucentBackground, False)
            else:
                window_widget.setAttribute(Qt.WA_TranslucentBackground, True)

        return True
    except Exception:
        return False


# =========================================================================
# Backward Compatibility Exports for Legacy Modules
# =========================================================================
BG_DARK = "#20232A"
BG_PANEL = "#282C34"
BG_CARD = "#2F3440"
BG_CARD_HOVER = "#363C4A"
STROKE_CARD = "#3D4452"
ACCENT_CYAN = "#60CDFF"
ACCENT_BLUE = "#0078D4"
ACCENT_GREEN = "#10B981"
ACCENT_AMBER = "#F59E0B"
ACCENT_RED = "#EF4444"
TEXT_WHITE = "#FFFFFF"
TEXT_MUTED = "#9E9E9E"

def apply_mica(window) -> bool:
    try:
        hwnd = int(window.winId()) if hasattr(window, "winId") else int(window.winfo_id())
        return apply_dwm_backdrop(hwnd, "mica")
    except Exception:
        return False

def apply_dark_title_bar(window) -> bool:
    try:
        hwnd = int(window.winId()) if hasattr(window, "winId") else int(window.winfo_id())
        return apply_dwm_backdrop(hwnd, "mica")
    except Exception:
        return False

