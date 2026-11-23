"""Authentic Windows 11 WinUI 3 Fluent Dark QSS Stylesheet for Vortex Controls.
Accurately replicates the FluentDL / WinUI 3 visual language:
Mica base (#202020), elevated cards (#2B2B2B), 8px corner radius,
subtle borders (#383838), Windows 11 accent blue (#0078D4 / #60CDFF),
Segoe UI Variable typography, and clean table/input styling.
"""

FLUENT_DARK_QSS = """
/* Global Base Window & Font */
QMainWindow, QWidget#MainRoot {
    background-color: #202020;
    color: #FFFFFF;
    font-family: 'Segoe UI Variable Display', 'Segoe UI Variable Text', 'Segoe UI', system-ui, sans-serif;
    font-size: 13px;
}

/* Left Navigation Rail (WinUI 3 NavigationView) */
QFrame#NavRail {
    background-color: #202020;
    border-right: 1px solid #2D2D2D;
}

/* Hamburger Toggle Button */
QPushButton#HamburgerBtn {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 8px;
    margin: 8px 6px;
}

QPushButton#HamburgerBtn:hover {
    background-color: #2D2D2D;
}

QPushButton#HamburgerBtn:pressed {
    background-color: #252525;
}

/* Navigation Rail Item */
QFrame#NavRailItem {
    background-color: transparent;
    border-radius: 6px;
    margin: 2px 6px;
    border: none;
}

QFrame#NavRailItem:hover {
    background-color: #2D2D2D;
}

QFrame#NavRailItem[active="true"] {
    background-color: #2C2C2C;
}

/* Nav Item Left Accent Indicator */
QFrame#NavAccentBar {
    background-color: #60CDFF;
    border-radius: 1.5px;
}

QLabel#NavLabel {
    color: #D1D5DB;
    font-size: 13px;
    font-weight: 500;
}

QLabel#NavLabel[active="true"] {
    color: #FFFFFF;
    font-weight: 600;
}

/* Topbar Header */
QFrame#Topbar {
    background-color: #202020;
    border-bottom: 1px solid #2D2D2D;
}

QLabel#TopbarTitle {
    font-size: 16px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: 0.3px;
}

QLabel#TopbarSub {
    font-size: 11px;
    color: #9E9E9E;
}

/* WinUI 3 Elevated Card */
QFrame#Card {
    background-color: #2B2B2B;
    border: 1px solid #383838;
    border-radius: 8px;
}

/* KPI Card Styles */
QFrame#KpiCard {
    background-color: #2B2B2B;
    border: 1px solid #383838;
    border-radius: 8px;
}

QFrame#KpiCard:hover {
    border-color: #4A4A4A;
    background-color: #2F2F2F;
}

QLabel#KpiTitle {
    font-size: 11px;
    font-weight: 600;
    color: #9E9E9E;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QLabel#KpiVal {
    font-size: 22px;
    font-weight: 700;
    color: #FFFFFF;
}

QLabel#KpiSub {
    font-size: 11px;
    color: #9E9E9E;
}

/* Master-Detail Inspector Card */
QFrame#InspectorCard {
    background-color: #2B2B2B;
    border: 1px solid #383838;
    border-radius: 8px;
}

QLabel#InspectorTitle {
    font-size: 14px;
    font-weight: 700;
    color: #FFFFFF;
}

QLabel#InspectorSection {
    font-size: 11px;
    font-weight: 700;
    color: #60CDFF;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 8px;
}

QLabel#InspectorPropKey {
    font-size: 11px;
    color: #9E9E9E;
}

QLabel#InspectorPropVal {
    font-size: 12px;
    font-weight: 600;
    color: #FFFFFF;
}

/* Pill Search Bar */
QLineEdit#PillSearch {
    background-color: #2A2A2A;
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 7px 12px;
    color: #FFFFFF;
    font-size: 12px;
}

QLineEdit#PillSearch:focus {
    border: 1px solid #60CDFF;
    background-color: #1F1F1F;
}

/* Buttons */
QPushButton#PrimaryBtn {
    background-color: #0078D4;
    color: #FFFFFF;
    border: 1px solid #0063B1;
    border-radius: 6px;
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton#PrimaryBtn:hover {
    background-color: #1084D9;
}

QPushButton#PrimaryBtn:pressed {
    background-color: #006CBE;
}

QPushButton#ActionBtn {
    background-color: #2B2B2B;
    color: #FFFFFF;
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 500;
}

QPushButton#ActionBtn:hover {
    background-color: #333333;
    border-color: #4A4A4A;
}

QPushButton#ActionBtn:pressed {
    background-color: #262626;
}

/* Filter Chip Buttons */
QPushButton#FilterChip {
    background-color: #2B2B2B;
    color: #CCCCCC;
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: 500;
}

QPushButton#FilterChip:hover {
    background-color: #333333;
    color: #FFFFFF;
}

QPushButton#FilterChip[checked="true"] {
    background-color: rgba(96, 205, 255, 0.15);
    border-color: #60CDFF;
    color: #60CDFF;
    font-weight: 600;
}

/* Data Tables */
QTableWidget {
    background-color: #2B2B2B;
    border: 1px solid #383838;
    border-radius: 8px;
    gridline-color: #333333;
    color: #FFFFFF;
    selection-background-color: rgba(96, 205, 255, 0.2);
    selection-color: #FFFFFF;
    font-size: 12px;
    outline: none;
}

QTableWidget::item {
    padding: 6px 10px;
    border-bottom: 1px solid #333333;
}

QTableWidget::item:selected {
    background-color: rgba(96, 205, 255, 0.25);
    color: #FFFFFF;
}

QHeaderView::section {
    background-color: #252525;
    color: #9E9E9E;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #383838;
}

/* Dropdown ComboBox */
QComboBox {
    background-color: #2A2A2A;
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 5px 10px;
    color: #FFFFFF;
    font-size: 12px;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #2B2B2B;
    border: 1px solid #383838;
    selection-background-color: #0078D4;
    color: #FFFFFF;
    padding: 4px;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #4A4A4A;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #60CDFF;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 8px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #4A4A4A;
    min-width: 24px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #60CDFF;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""
