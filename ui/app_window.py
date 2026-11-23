"""AutoPlan Studio Main Window.
Coordinates the Fluent navigation rail, view switching,
Mica backdrop integration, and top-level application lifecycle.
"""

from __future__ import annotations
import os
import sys
import tkinter as tk
from typing import Dict, Any, Optional
from .theme import (
    BG_DARK, BG_PANEL, MICA_BG, FLUENT_TEXT_PRIMARY,
    FluentNavRail, FluentIcon, apply_mica, apply_dark_title_bar
)
from .views.dashboard_view import DashboardView
from .views.updater_view import UpdaterView
from .views.clusters_view import ClustersView
from .views.lookahead_view import LookaheadView
from .views.oos_view import OosView
from .views.export_view import ExportView
from .views.settings_view import SettingsView
from core.project_state import get_project_state


class AutoPlanAppWindow(tk.Tk):
    """Main desktop application window for AutoPlan Studio."""

    def __init__(self, initial_baseline_path: Optional[str] = None):
        super().__init__()
        self.title("AutoPlan Studio — Construction Project Controls & Fluent P6 Engine")

        # Responsive geometry calculation
        scr_w = max(1024, self.winfo_screenwidth())
        scr_h = max(700, self.winfo_screenheight())
        target_w = min(1360, max(1020, scr_w - 60))
        target_h = min(840, max(680, scr_h - 70))
        pos_x = max(10, (scr_w - target_w) // 2)
        pos_y = max(10, (scr_h - target_h) // 2)
        self.geometry(f"{target_w}x{target_h}+{pos_x}+{pos_y}")
        self.minsize(980, 620)
        self.configure(bg=BG_DARK)

        # Apply Windows 11 Mica & Dark Title Bar
        apply_mica(self, style="mica_alt")

        self.state = get_project_state()

        # Build Main Layout
        self._build_layout()

        # Keyboard shortcuts
        self.bind("<Control-b>", lambda e: self.nav_rail.toggle_expanded())

        # Load initial baseline if provided
        if initial_baseline_path and os.path.exists(initial_baseline_path):
            try:
                self.state.load_baseline(initial_baseline_path)
            except Exception as e:
                print(f"[AutoPlanAppWindow] Error loading initial baseline: {e}")

    def _build_layout(self):
        # 1. Left Navigation Rail
        self.nav_rail = FluentNavRail(
            self,
            on_page_change=self.navigate_to_page,
            width=FluentNavRail.EXPANDED_WIDTH,
            bg_color=BG_PANEL
        )
        self.nav_rail.pack(side="left", fill="y")

        # Add Nav Items
        self.nav_rail.add_nav_item("dashboard", "Executive Dashboard", FluentIcon.DASHBOARD)
        self.nav_rail.add_nav_item("updater", "XER & Site Updater", FluentIcon.REFRESH)
        self.nav_rail.add_nav_item("clusters", "Clusters Matrix", FluentIcon.LAYERS)
        self.nav_rail.add_nav_item("lookahead", "Lookahead Schedule", FluentIcon.CALENDAR)
        self.nav_rail.add_nav_item("oos", "Out-of-Sequence Ties", FluentIcon.WARNING)
        self.nav_rail.add_nav_item("export", "Reports & Deliverables", FluentIcon.EXCEL)
        self.nav_rail.add_nav_item("settings", "Project Settings", FluentIcon.SETTINGS, is_bottom=True)

        # 2. Main Content View Area
        self.content_area = tk.Frame(self, bg=BG_DARK)
        self.content_area.pack(side="right", fill="both", expand=True)

        # Instantiate View Pages
        self.views = {
            "dashboard": DashboardView(self.content_area),
            "updater": UpdaterView(self.content_area, on_navigate_dashboard=lambda: self.nav_rail.select_page("dashboard")),
            "clusters": ClustersView(self.content_area),
            "lookahead": LookaheadView(self.content_area),
            "oos": OosView(self.content_area),
            "export": ExportView(self.content_area),
            "settings": SettingsView(self.content_area)
        }

        # Show initial view
        self.current_page = "dashboard"
        self.views["dashboard"].pack(fill="both", expand=True)

    def navigate_to_page(self, page_id: str):
        if page_id in self.views and page_id != self.current_page:
            if self.current_page in self.views:
                self.views[self.current_page].pack_forget()
            self.current_page = page_id
            self.views[page_id].pack(fill="both", expand=True)
