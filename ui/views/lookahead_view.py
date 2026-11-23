"""Lookahead & Critical Activities Schedule View.
Filterable and searchable schedule view of active, critical, and upcoming 30-day activities.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, List, Dict, Any
from ..theme import (
    BG_DARK, BG_CARD, BORDER_COLOR, ACCENT_CYAN, FLUENT_TEXT_PRIMARY,
    FLUENT_TEXT_SECONDARY, FONT_TITLE, FONT_SECTION, FONT_BODY,
    FONT_SMALL, FONT_MONO
)
from ..components.data_table import FluentDataTable
from core.project_state import get_project_state


class LookaheadView(tk.Frame):
    """View presenting active and 30-day lookahead activities with variance tracking."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.state = get_project_state()
        self.state.register_listener(self.refresh_data)

        self._all_activities: List[Dict[str, Any]] = []
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        container = tk.Frame(self, bg=BG_DARK)
        container.pack(fill="both", expand=True, padx=28, pady=20)

        # Header
        h_f = tk.Frame(container, bg=BG_DARK)
        h_f.pack(fill="x", pady=(0, 12))

        tk.Label(
            h_f, text="📅 Active & 30-Day Lookahead Activities",
            font=FONT_TITLE, bg=BG_DARK, fg=FLUENT_TEXT_PRIMARY
        ).pack(side="left")

        # Search & Filter Bar
        f_bar = tk.Frame(container, bg=BG_DARK)
        f_bar.pack(fill="x", pady=(0, 10))

        tk.Label(f_bar, text="Search:", font=FONT_BODY, bg=BG_DARK, fg=FLUENT_TEXT_SECONDARY).pack(side="left", padx=(0, 6))
        self.ent_search = tk.Entry(
            f_bar, font=("Segoe UI Variable Text", 9), bg="#111827", fg="#F8FAFC",
            insertbackground="#FFF", relief="flat", highlightthickness=1,
            highlightbackground="#334155", highlightcolor=ACCENT_CYAN, width=30
        )
        self.ent_search.pack(side="left", padx=(0, 16), ipady=3)
        self.ent_search.bind("<KeyRelease>", lambda e: self.filter_activities())

        tk.Label(f_bar, text="Status:", font=FONT_BODY, bg=BG_DARK, fg=FLUENT_TEXT_SECONDARY).pack(side="left", padx=(0, 6))
        self.status_var = tk.StringVar(value="ALL")
        self.opt_status = tk.OptionMenu(
            f_bar, self.status_var, "ALL", "In progress", "Complete", "Not started",
            command=lambda v: self.filter_activities()
        )
        self.opt_status.configure(
            bg="#111827", fg="#F8FAFC", activebackground="#1E293B",
            activeforeground="#FFF", relief="flat", highlightthickness=1,
            highlightbackground="#334155", font=("Segoe UI Variable Text", 9)
        )
        self.opt_status.pack(side="left")

        # Table Panel
        tb_panel = tk.Frame(container, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COLOR)
        tb_panel.pack(fill="both", expand=True)

        cols = [
            ("act_id", "Activity ID", 150),
            ("act_name", "Activity Name", 320),
            ("cluster", "Cluster", 80),
            ("discipline", "Discipline", 140),
            ("status", "Status", 100),
            ("pct_str", "Progress %", 90),
            ("target_start", "Target Start", 100),
            ("bl_finish", "Baseline Finish", 100),
            ("late_str", "Delay", 80)
        ]
        self.table = FluentDataTable(tb_panel, columns=cols)
        self.table.pack(fill="both", expand=True, padx=12, pady=12)

    def refresh_data(self):
        a = self.state.analytics
        if not a or not a.get("activities"):
            return
        self._all_activities = a["activities"]
        self.filter_activities()

    def filter_activities(self):
        q = self.ent_search.get().strip().lower()
        st = self.status_var.get()

        rows = []
        for act in self._all_activities:
            if st != "ALL" and act.get("status", "").lower() != st.lower():
                continue
            if q and q not in act.get("act_id", "").lower() and q not in act.get("act_name", "").lower():
                continue

            late_d = act.get("late_days", 0)
            rows.append({
                "act_id": act["act_id"],
                "act_name": act["act_name"],
                "cluster": act.get("cluster", ""),
                "discipline": act.get("discipline", ""),
                "status": act.get("status", ""),
                "pct_str": f"{act.get('pct', 0):.1f}%",
                "target_start": act.get("target_start", "-"),
                "bl_finish": act.get("bl_finish", "-"),
                "late_str": f"{late_d}d" if late_d > 0 else "-"
            })

        self.table.set_data(rows)
