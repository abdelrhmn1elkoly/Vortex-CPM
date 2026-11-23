"""Executive Dashboard View.
Renders KPI metric cards, native S-Curve vector chart, cluster bar chart, and project summary.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Dict, Any
from ..theme import (
    BG_DARK, BG_CARD, BORDER_COLOR, ACCENT_CYAN, ACCENT_BLUE,
    ACCENT_GREEN, ACCENT_AMBER, ACCENT_RED, ACCENT_PURPLE,
    FLUENT_TEXT_PRIMARY, FLUENT_TEXT_SECONDARY, FONT_TITLE,
    FONT_SUBTITLE, FONT_SECTION, FONT_BODY, FONT_SMALL
)
from ..components.kpi_card import KpiCard
from ..components.chart_canvas import SCurveCanvas, BarChartCanvas
from ..components.data_table import FluentDataTable
from core.project_state import get_project_state


class DashboardView(tk.Frame):
    """Executive Dashboard page featuring WinUI 3 KPI cards and responsive charts."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.state = get_project_state()
        self.state.register_listener(self.on_state_updated)

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        # Scrollable container or main layout
        self.main_f = tk.Frame(self, bg=BG_DARK)
        self.main_f.pack(fill="both", expand=True, padx=24, pady=18)

        # 1. Header Row
        header_f = tk.Frame(self.main_f, bg=BG_DARK)
        header_f.pack(fill="x", pady=(0, 14))

        self.lbl_title = tk.Label(
            header_f,
            text="Executive Project Controls Dashboard",
            font=FONT_TITLE,
            bg=BG_DARK,
            fg=FLUENT_TEXT_PRIMARY
        )
        self.lbl_title.pack(side="left")

        self.lbl_sub = tk.Label(
            header_f,
            text="Real-time EVM tracking, S-Curve analysis, and schedule forecast",
            font=FONT_BODY,
            bg=BG_DARK,
            fg=FLUENT_TEXT_SECONDARY
        )
        self.lbl_sub.pack(side="left", padx=(14, 0), pady=(4, 0))

        # 2. KPI Cards Row
        kpi_row = tk.Frame(self.main_f, bg=BG_DARK)
        kpi_row.pack(fill="x", pady=(0, 16))

        self.kpi_actual = KpiCard(kpi_row, "OVERALL PHYSICAL %", "0.00%", "Planned: 0.00%", accent_color=ACCENT_CYAN)
        self.kpi_ev = KpiCard(kpi_row, "EARNED VALUE (EV)", "0.00M", "PV: 0.00M | BAC: 0.00M", accent_color=ACCENT_BLUE)
        self.kpi_spi = KpiCard(kpi_row, "SCHEDULE INDEX (SPI)", "0.00", "SV: 0.00M EGP", accent_color=ACCENT_RED)
        self.kpi_fcst = KpiCard(kpi_row, "FORECAST FINISH", "-", "Delay: 0 days", accent_color=ACCENT_AMBER)
        self.kpi_acts = KpiCard(kpi_row, "ACTIVITIES & OOS", "0 Act / 0 Done", "0 Out-of-Sequence Ties", accent_color=ACCENT_PURPLE)

        for card in [self.kpi_actual, self.kpi_ev, self.kpi_spi, self.kpi_fcst, self.kpi_acts]:
            card.pack(side="left", fill="x", expand=True, padx=5)

        # 3. Charts Grid Row (S-Curve & Cluster Bars)
        charts_row = tk.Frame(self.main_f, bg=BG_DARK)
        charts_row.pack(fill="both", expand=True, pady=(0, 14))

        # S-Curve Panel
        sc_panel = tk.Frame(charts_row, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COLOR)
        sc_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))

        sc_title_f = tk.Frame(sc_panel, bg=BG_CARD)
        sc_title_f.pack(fill="x", padx=14, pady=(10, 4))
        tk.Label(
            sc_title_f, text="📈 Cumulative S-Curve: Planned Value (PV) vs Earned Value (EV)",
            font=FONT_SECTION, bg=BG_CARD, fg=FLUENT_TEXT_PRIMARY
        ).pack(side="left")

        self.scurve_canvas = SCurveCanvas(sc_panel, height=200)
        self.scurve_canvas.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # Cluster Bar Panel
        cl_panel = tk.Frame(charts_row, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COLOR)
        cl_panel.pack(side="right", fill="both", expand=True, padx=(8, 0))

        cl_title_f = tk.Frame(cl_panel, bg=BG_CARD)
        cl_title_f.pack(fill="x", padx=14, pady=(10, 4))
        tk.Label(
            cl_title_f, text="🏢 Cluster Performance (Planned % vs Actual %)",
            font=FONT_SECTION, bg=BG_CARD, fg=FLUENT_TEXT_PRIMARY
        ).pack(side="left")

        self.cluster_canvas = BarChartCanvas(cl_panel, height=200)
        self.cluster_canvas.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # 4. Quick Cluster Matrix Table Preview at bottom
        tb_panel = tk.Frame(self.main_f, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COLOR)
        tb_panel.pack(fill="both", expand=True)

        tb_title_f = tk.Frame(tb_panel, bg=BG_CARD)
        tb_title_f.pack(fill="x", padx=14, pady=(10, 4))
        tk.Label(
            tb_title_f, text="🏢 Executive Cluster Progress Summary (C08 - C18)",
            font=FONT_SECTION, bg=BG_CARD, fg=FLUENT_TEXT_PRIMARY
        ).pack(side="left")

        cols = [
            ("cluster", "Cluster", 90),
            ("bac_str", "Budget (BAC)", 130),
            ("planned_pct_str", "Planned %", 95),
            ("actual_pct_str", "Actual %", 95),
            ("variance_str", "Variance (SV)", 130),
            ("spi_str", "SPI", 80),
            ("health", "Health Status", 100),
            ("remarks", "Discipline Remark", 260)
        ]
        self.table = FluentDataTable(tb_panel, columns=cols, height=130)
        self.table.pack(fill="both", expand=True, padx=10, pady=(0, 8))

    def on_state_updated(self):
        self.refresh_data()

    def refresh_data(self):
        a = self.state.analytics
        if not a:
            return

        # Update Titles
        self.lbl_sub.configure(
            text=f"Data Date: {a.get('data_date')}  •  Baseline: {a.get('baseline_name')}  •  Total Budget: {a.get('bac', 0)/1e6:.2f}M EGP"
        )

        # Update KPIs
        self.kpi_actual.update_data(
            f"{a.get('actual_pct', 0):.2f}%",
            f"Planned: {a.get('planned_pct', 0):.2f}% ({a.get('variance_pct', 0):+.2f}%)"
        )
        self.kpi_ev.update_data(
            f"{a.get('ev', 0)/1e6:.2f}M EGP",
            f"PV: {a.get('pv', 0)/1e6:.2f}M  |  BAC: {a.get('bac', 0)/1e6:.2f}M"
        )
        self.kpi_spi.update_data(
            f"{a.get('spi', 0):.2f}",
            f"SV: {a.get('sv', 0)/1e6:+.2f}M EGP"
        )
        self.kpi_fcst.update_data(
            str(a.get("forecast_finish", "-")),
            f"Contract Finish: {a.get('contract_finish', '-')} ({a.get('variance_days', 0)}d)"
        )
        self.kpi_acts.update_data(
            f"{a.get('active_count', 0)} Act / {a.get('completed_count', 0)} Done",
            f"{a.get('oos_count', 0)} Out-of-Sequence Ties"
        )

        # Update S-Curve
        if a.get("scurve"):
            self.scurve_canvas.set_data(a["scurve"])

        # Update Cluster Bars
        if a.get("clusters"):
            self.cluster_canvas.set_data(a["clusters"])

            # Update Table
            table_rows = []
            for c in a["clusters"]:
                table_rows.append({
                    "cluster": c["cluster"],
                    "bac_str": f"{c['bac']/1e6:.2f} M EGP",
                    "planned_pct_str": f"{c['planned_pct']:.1f}%",
                    "actual_pct_str": f"{c['actual_pct']:.1f}%",
                    "variance_str": f"{c['sv']/1e6:+.2f} M EGP",
                    "spi_str": f"{c['spi']:.2f}",
                    "health": c.get("health", "Healthy"),
                    "remarks": c.get("remarks", "")
                })
            self.table.set_data(table_rows)
