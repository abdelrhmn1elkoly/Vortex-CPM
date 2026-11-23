"""Cluster Progress Matrix View.
Detailed breakdown and analysis of Clusters C08 to C18,
displaying BAC, Weight %, Planned %, Actual %, Earned Value, SPI, and Slippage.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional
from ..theme import (
    BG_DARK, BG_CARD, BORDER_COLOR, ACCENT_CYAN, FLUENT_TEXT_PRIMARY,
    FLUENT_TEXT_SECONDARY, FONT_TITLE, FONT_SECTION, FONT_BODY,
    FONT_SMALL_BOLD, FONT_BODY_BOLD, FluentButton
)
from ..components.data_table import FluentDataTable
from core.project_state import get_project_state


class ClustersView(tk.Frame):
    """View dedicated to cluster-level tracking and EVM variance analysis."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.state = get_project_state()
        self.state.register_listener(self.refresh_data)

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        container = tk.Frame(self, bg=BG_DARK)
        container.pack(fill="both", expand=True, padx=28, pady=20)

        # Header
        h_f = tk.Frame(container, bg=BG_DARK)
        h_f.pack(fill="x", pady=(0, 14))

        tk.Label(
            h_f, text="🏢 Cluster Progress & Earned Value Matrix (C08 – C18)",
            font=FONT_TITLE, bg=BG_DARK, fg=FLUENT_TEXT_PRIMARY
        ).pack(side="left")

        # Table Panel
        tb_panel = tk.Frame(container, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COLOR)
        tb_panel.pack(fill="both", expand=True)

        cols = [
            ("cluster", "Cluster", 90),
            ("bac_str", "Budget (BAC)", 130),
            ("weight_str", "Weight %", 80),
            ("planned_pct_str", "Planned %", 95),
            ("actual_pct_str", "Actual %", 95),
            ("variance_str", "Variance %", 95),
            ("pv_str", "PV (EGP)", 125),
            ("ev_str", "EV (EGP)", 125),
            ("sv_str", "SV (EGP)", 125),
            ("spi_str", "SPI", 75),
            ("bl_finish", "Baseline Finish", 110),
            ("fcst_finish", "Forecast Finish", 110),
            ("slip_str", "Slip (Days)", 90),
            ("remarks", "Discipline Remark", 260)
        ]
        self.table = FluentDataTable(tb_panel, columns=cols)
        self.table.pack(fill="both", expand=True, padx=12, pady=12)

    def refresh_data(self):
        a = self.state.analytics
        if not a or not a.get("clusters"):
            return

        table_rows = []
        for c in a["clusters"]:
            table_rows.append({
                "cluster": c["cluster"],
                "bac_str": f"{c['bac']/1e6:.2f} M",
                "weight_str": f"{c['weight']:.1f}%",
                "planned_pct_str": f"{c['planned_pct']:.1f}%",
                "actual_pct_str": f"{c['actual_pct']:.1f}%",
                "variance_str": f"{c['variance_pct']:+.1f}%",
                "pv_str": f"{c['pv']/1e6:.2f} M",
                "ev_str": f"{c['ev']/1e6:.2f} M",
                "sv_str": f"{c['sv']/1e6:+.2f} M",
                "spi_str": f"{c['spi']:.2f}",
                "bl_finish": c.get("bl_finish", "-"),
                "fcst_finish": c.get("fcst_finish", "-"),
                "slip_str": f"{c.get('slip_days', 0)}d",
                "remarks": c.get("remarks", "")
            })

        self.table.set_data(table_rows)
