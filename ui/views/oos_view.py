"""Out-of-Sequence Logic Ties Audit View.
Identifies and lists relationships where a predecessor is Not Started
while its successor has already commenced or completed.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, List, Dict, Any
from ..theme import (
    BG_DARK, BG_CARD, BORDER_COLOR, ACCENT_CYAN, ACCENT_AMBER,
    FLUENT_TEXT_PRIMARY, FLUENT_TEXT_SECONDARY, FONT_TITLE,
    FONT_SECTION, FONT_BODY, FONT_SMALL, FONT_MONO
)
from ..components.data_table import FluentDataTable
from core.project_state import get_project_state


class OosView(tk.Frame):
    """View dedicated to schedule logic integrity and Out-of-Sequence relationships."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.state = get_project_state()
        self.state.register_listener(self.refresh_data)

        self._all_ties: List[Dict[str, Any]] = []
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        container = tk.Frame(self, bg=BG_DARK)
        container.pack(fill="both", expand=True, padx=28, pady=20)

        # Header
        h_f = tk.Frame(container, bg=BG_DARK)
        h_f.pack(fill="x", pady=(0, 6))

        tk.Label(
            h_f, text="⚠️ Out-of-Sequence Relationships (OOS Logic Audit)",
            font=FONT_TITLE, bg=BG_DARK, fg=FLUENT_TEXT_PRIMARY
        ).pack(side="left")

        # Info Box
        info_f = tk.Frame(container, bg="#2A1B0E", highlightthickness=1, highlightbackground=ACCENT_AMBER)
        info_f.pack(fill="x", pady=(0, 14), padx=2, ipady=6)
        tk.Label(
            info_f,
            text="⚠️ An Out-of-Sequence tie occurs when a Finish-to-Start or Start-to-Start successor has actual progress recorded before its predecessor has started.\nThis can distort critical path float calculations in Primavera P6 and indicates work proceeding out of logical sequence on site.",
            font=FONT_BODY, bg="#2A1B0E", fg="#FCD34D", justify="left"
        ).pack(anchor="w", padx=14)

        # Search Bar
        f_bar = tk.Frame(container, bg=BG_DARK)
        f_bar.pack(fill="x", pady=(0, 10))

        tk.Label(f_bar, text="Filter Logic Ties:", font=FONT_BODY, bg=BG_DARK, fg=FLUENT_TEXT_SECONDARY).pack(side="left", padx=(0, 6))
        self.ent_search = tk.Entry(
            f_bar, font=("Segoe UI Variable Text", 9), bg="#111827", fg="#F8FAFC",
            insertbackground="#FFF", relief="flat", highlightthickness=1,
            highlightbackground="#334155", highlightcolor=ACCENT_CYAN, width=32
        )
        self.ent_search.pack(side="left", padx=(0, 16), ipady=3)
        self.ent_search.bind("<KeyRelease>", lambda e: self.filter_ties())

        # Table Panel
        tb_panel = tk.Frame(container, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COLOR)
        tb_panel.pack(fill="both", expand=True)

        cols = [
            ("pred_id", "Predecessor ID", 150),
            ("pred_name", "Predecessor Name", 280),
            ("tie", "Tie", 60),
            ("succ_id", "Successor ID", 150),
            ("succ_name", "Successor Name", 280),
            ("succ_status", "Successor Status", 110),
            ("succ_pct_str", "Successor %", 90)
        ]
        self.table = FluentDataTable(tb_panel, columns=cols)
        self.table.pack(fill="both", expand=True, padx=12, pady=12)

    def refresh_data(self):
        a = self.state.analytics
        if not a or not a.get("oos_ties"):
            return
        self._all_ties = a["oos_ties"]
        self.filter_ties()

    def filter_ties(self):
        q = self.ent_search.get().strip().lower()

        rows = []
        for o in self._all_ties:
            if q and q not in o.get("pred_id", "").lower() and q not in o.get("succ_id", "").lower() and q not in o.get("pred_name", "").lower() and q not in o.get("succ_name", "").lower():
                continue

            rows.append({
                "pred_id": o.get("pred_id", ""),
                "pred_name": o.get("pred_name", ""),
                "tie": o.get("tie", "FS"),
                "succ_id": o.get("succ_id", ""),
                "succ_name": o.get("succ_name", ""),
                "succ_status": o.get("succ_status", ""),
                "succ_pct_str": f"{o.get('succ_pct', 0):.1f}%"
            })

        self.table.set_data(rows)
