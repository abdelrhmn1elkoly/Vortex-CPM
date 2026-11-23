"""Native Dark Fluent Canvas Charts.
High-DPI vector rendering of S-Curves, Planned vs Actual bars, and SPI status indicators.
"""

from __future__ import annotations
import tkinter as tk
from typing import List, Dict, Any, Optional
from ..theme import (
    BG_CARD, BORDER_COLOR, ACCENT_CYAN, ACCENT_BLUE, ACCENT_GREEN,
    ACCENT_AMBER, ACCENT_RED, FLUENT_TEXT_PRIMARY, FLUENT_TEXT_SECONDARY,
    FONT_SMALL, FONT_SMALL_BOLD, FONT_SECTION
)


class SCurveCanvas(tk.Canvas):
    """Native Tkinter vector chart rendering cumulative Planned Value (PV) vs Earned Value (EV)."""

    def __init__(self, parent, height: int = 180, **kwargs):
        try:
            parent_bg = parent["bg"]
        except Exception:
            parent_bg = BG_CARD

        super().__init__(parent, bg=parent_bg, height=height, highlightthickness=0, bd=0, **kwargs)
        self.data_points: List[Dict[str, Any]] = []
        self.bind("<Configure>", lambda e: self._draw())

    def set_data(self, points: List[Dict[str, Any]]):
        self.data_points = points
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 60 or h < 60 or not self.data_points:
            self.create_text(w / 2, h / 2, text="No S-Curve data loaded", fill=FLUENT_TEXT_SECONDARY, font=FONT_SMALL)
            return

        pad_left, pad_right = 50, 20
        pad_top, pad_bottom = 25, 30
        plot_w = w - pad_left - pad_right
        plot_h = h - pad_top - pad_bottom

        # Determine max PV
        max_val = max([p.get("pv_m", 0) for p in self.data_points] + [p.get("ev_m", 0) or 0 for p in self.data_points] + [10.0])
        max_val = max(10.0, max_val * 1.05)

        # Draw Gridlines & Y Ticks (4 levels)
        for i in range(5):
            y_ratio = i / 4.0
            y_pos = pad_top + plot_h * (1.0 - y_ratio)
            val_at_y = max_val * y_ratio
            self.create_line(pad_left, y_pos, w - pad_right, y_pos, fill="#1E293B", dash=(2, 2))
            self.create_text(pad_left - 8, y_pos, text=f"{val_at_y:.0f}M", fill=FLUENT_TEXT_SECONDARY, anchor="e", font=FONT_SMALL)

        n_pts = len(self.data_points)
        if n_pts < 2:
            return

        # Coordinates computation helper
        def get_coords(val, idx):
            x = pad_left + (idx / (n_pts - 1)) * plot_w
            y = pad_top + plot_h * (1.0 - (val / max_val))
            return x, y

        # 1. Planned Value (PV) Curve (Blue)
        pv_coords = []
        for idx, pt in enumerate(self.data_points):
            pv = pt.get("pv_m", 0.0)
            x, y = get_coords(pv, idx)
            pv_coords.extend([x, y])

        if len(pv_coords) >= 4:
            self.create_line(*pv_coords, fill=ACCENT_BLUE, width=2.5, smooth=True)

        # 2. Earned Value (EV) Curve (Cyan)
        ev_pts = [(idx, pt.get("ev_m")) for idx, pt in enumerate(self.data_points) if pt.get("ev_m") is not None]
        ev_coords = []
        for idx, ev in ev_pts:
            x, y = get_coords(ev, idx)
            ev_coords.extend([x, y])

        if len(ev_coords) >= 4:
            self.create_line(*ev_coords, fill=ACCENT_CYAN, width=3, smooth=True)
            for idx, ev in ev_pts:
                x, y = get_coords(ev, idx)
                self.create_oval(x - 3, y - 3, x + 3, y + 3, fill=ACCENT_CYAN, outline="#0B0F17")

        # X-Axis Week Labels (sample 6-8 evenly spaced)
        step = max(1, n_pts // 7)
        for idx in range(0, n_pts, step):
            pt = self.data_points[idx]
            x, _ = get_coords(0, idx)
            self.create_text(x, h - pad_bottom + 12, text=pt.get("week", ""), fill=FLUENT_TEXT_SECONDARY, font=FONT_SMALL)

        # Legend
        self.create_rectangle(w - 170, 6, w - 156, 10, fill=ACCENT_BLUE, outline="")
        self.create_text(w - 150, 8, text="Planned Value (PV)", fill=FLUENT_TEXT_PRIMARY, anchor="w", font=FONT_SMALL)

        self.create_rectangle(w - 75, 6, w - 61, 10, fill=ACCENT_CYAN, outline="")
        self.create_text(w - 55, 8, text="Earned (EV)", fill=FLUENT_TEXT_PRIMARY, anchor="w", font=FONT_SMALL)


class BarChartCanvas(tk.Canvas):
    """Horizontal bar chart comparing Planned % vs Actual % across clusters or disciplines."""

    def __init__(self, parent, height: int = 180, **kwargs):
        try:
            parent_bg = parent["bg"]
        except Exception:
            parent_bg = BG_CARD

        super().__init__(parent, bg=parent_bg, height=height, highlightthickness=0, bd=0, **kwargs)
        self.items: List[Dict[str, Any]] = []
        self.bind("<Configure>", lambda e: self._draw())

    def set_data(self, items: List[Dict[str, Any]]):
        self.items = items
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 60 or h < 60 or not self.items:
            self.create_text(w / 2, h / 2, text="No chart data available", fill=FLUENT_TEXT_SECONDARY, font=FONT_SMALL)
            return

        pad_left = 60
        pad_right = 20
        pad_top = 20
        pad_bottom = 20
        plot_w = w - pad_left - pad_right
        plot_h = h - pad_top - pad_bottom

        display_items = self.items[:8]
        n = len(display_items)
        if n == 0:
            return

        row_h = plot_h / n

        for idx, item in enumerate(display_items):
            label = str(item.get("cluster") or item.get("discipline") or f"Item {idx+1}")
            p_pct = float(item.get("planned_pct", 0) or item.get("pv_pct", 0) or 0)
            a_pct = float(item.get("actual_pct", 0) or item.get("ev_pct", 0) or 0)

            cy = pad_top + idx * row_h + row_h / 2

            # Label
            self.create_text(pad_left - 8, cy, text=label, fill=FLUENT_TEXT_PRIMARY, anchor="e", font=FONT_SMALL_BOLD)

            # Planned Bar (Blue)
            p_w = plot_w * (min(100.0, p_pct) / 100.0)
            self.create_rectangle(pad_left, cy - 6, pad_left + p_w, cy - 1, fill=ACCENT_BLUE, outline="")

            # Actual Bar (Green / Cyan)
            a_w = plot_w * (min(100.0, a_pct) / 100.0)
            self.create_rectangle(pad_left, cy + 1, pad_left + a_w, cy + 6, fill=ACCENT_GREEN, outline="")

        # Legend
        self.create_rectangle(pad_left, 6, pad_left + 12, 12, fill=ACCENT_BLUE, outline="")
        self.create_text(pad_left + 16, 9, text="Planned %", fill=FLUENT_TEXT_SECONDARY, anchor="w", font=FONT_SMALL)

        self.create_rectangle(pad_left + 80, 6, pad_left + 92, 12, fill=ACCENT_GREEN, outline="")
        self.create_text(pad_left + 96, 9, text="Actual %", fill=FLUENT_TEXT_SECONDARY, anchor="w", font=FONT_SMALL)
