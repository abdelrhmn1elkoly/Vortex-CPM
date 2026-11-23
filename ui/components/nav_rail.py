"""WinUI 3 Collapsible Navigation Rail for Vortex Controls.
Replicates the authentic FluentDL navigation rail:
Collapsible width (48px compact ↔ 210px expanded) via Hamburger button,
vertical accent bar indicator on active selection, and pinned Help/Settings.
"""

from __future__ import annotations
from typing import Dict, Tuple, List, Optional
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy
)
from ui.custom_icons import get_fluent_icon


class NavRailItemWidget(QFrame):
    """An individual selectable item in the navigation rail."""

    clicked = Signal(str)

    def __init__(self, page_id: str, title: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.page_id = page_id
        self.title = title
        self.icon_name = icon_name
        self.is_active = False
        self.is_expanded = True

        self.setObjectName("NavRailItem")
        self.setFixedHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(title)

        self._init_ui()

    def _init_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 10, 0)
        lay.setSpacing(8)

        # 1. Left Accent Indicator Bar (Active highlight line)
        self.accent_bar = QFrame()
        self.accent_bar.setObjectName("NavAccentBar")
        self.accent_bar.setFixedWidth(3)
        self.accent_bar.setFixedHeight(20)
        self.accent_bar.setVisible(False)
        lay.addWidget(self.accent_bar)

        # 2. Icon Label
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self._update_icon()
        lay.addWidget(self.icon_label)

        # 3. Text Label
        self.text_label = QLabel(self.title)
        self.text_label.setObjectName("NavLabel")
        lay.addWidget(self.text_label, 1)

    def _update_icon(self):
        color = "#60CDFF" if self.is_active else "#D1D5DB"
        icon = get_fluent_icon(self.icon_name, color=color, size=18)
        self.icon_label.setPixmap(icon.pixmap(18, 18))

    def set_active(self, active: bool):
        self.is_active = active
        self.accent_bar.setVisible(active)
        self.setProperty("active", "true" if active else "false")
        self.text_label.setProperty("active", "true" if active else "false")
        self._update_icon()
        self.style().unpolish(self)
        self.style().polish(self)
        self.style().unpolish(self.text_label)
        self.style().polish(self.text_label)

    def set_expanded(self, expanded: bool):
        self.is_expanded = expanded
        self.text_label.setVisible(expanded)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.page_id)
        super().mousePressEvent(event)


class NavRail(QFrame):
    """WinUI 3 collapsible navigation sidebar."""

    page_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NavRail")
        self.is_expanded = True
        self.setFixedWidth(210)

        self.items: Dict[str, NavRailItemWidget] = {}
        self.active_page = "dash"

        self._init_ui()

    def _init_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 8, 0, 12)
        main_lay.setSpacing(2)

        # 1. Top Hamburger Toggle Button
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(6, 0, 6, 4)

        self.btn_hamburger = QPushButton()
        self.btn_hamburger.setObjectName("HamburgerBtn")
        self.btn_hamburger.setFixedSize(36, 36)
        self.btn_hamburger.setCursor(Qt.PointingHandCursor)
        self.btn_hamburger.setIcon(get_fluent_icon("hamburger", color="#D1D5DB", size=18))
        self.btn_hamburger.setIconSize(QSize(18, 18))
        self.btn_hamburger.setToolTip("Toggle Navigation (Ctrl+B)")
        self.btn_hamburger.clicked.connect(self.toggle)
        top_bar.addWidget(self.btn_hamburger)

        # Brand header label (visible in expanded mode)
        self.lbl_brand = QLabel("VORTEX CONTROLS")
        self.lbl_brand.setStyleSheet("font-size: 12px; font-weight: 800; color: #FFFFFF; letter-spacing: 0.8px; margin-left: 4px;")
        top_bar.addWidget(self.lbl_brand, 1)

        main_lay.addLayout(top_bar)

        # 2. Main Navigation Items
        nav_pages = [
            ("dash", "Dashboard", "dashboard"),
            ("updater", "XER & Site Updater", "updater"),
            ("clusters", "Clusters Matrix", "clusters"),
            ("lookahead", "Lookahead Schedule", "lookahead"),
            ("oos", "Out-of-Sequence Audit", "oos"),
            ("compare", "Schedule Audit", "compliance"),
            ("trends", "History & Trends", "matrix"),
            ("export", "Deliverables & Reports", "export"),
        ]

        for p_id, title, icon_name in nav_pages:
            item = NavRailItemWidget(p_id, title, icon_name)
            item.clicked.connect(self.select_page)
            self.items[p_id] = item
            main_lay.addWidget(item)

        # Vertical Spacer
        main_lay.addStretch(1)

        # 3. Pinned Bottom Items (Help & Settings)
        bottom_pages = [
            ("help", "Help & Guidance", "help"),
            ("settings", "Project Settings", "settings"),
        ]

        for p_id, title, icon_name in bottom_pages:
            item = NavRailItemWidget(p_id, title, icon_name)
            item.clicked.connect(self.select_page)
            self.items[p_id] = item
            main_lay.addWidget(item)

        # Set default active item
        self.select_page("dash")

    def toggle(self):
        """Toggles between compact (48px) and expanded (210px) modes."""
        self.is_expanded = not self.is_expanded
        new_width = 210 if self.is_expanded else 48
        self.setFixedWidth(new_width)
        self.lbl_brand.setVisible(self.is_expanded)

        for item in self.items.values():
            item.set_expanded(self.is_expanded)

    def select_page(self, page_id: str):
        """Activates the specified navigation item."""
        self.active_page = page_id
        for pid, item in self.items.items():
            item.set_active(pid == page_id)
        self.page_changed.emit(page_id)
