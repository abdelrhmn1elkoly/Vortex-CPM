"""WinUI 3 Elevated KPI Metric Card Component.
Displays executive project control indicators with top accent indicators and sub-metrics.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional
from ..theme import (
    BG_CARD, BORDER_COLOR, ACCENT_CYAN, FLUENT_TEXT_PRIMARY,
    FLUENT_TEXT_SECONDARY, FONT_SMALL_BOLD, FONT_TITLE, FONT_SMALL, FONT_DISPLAY
)


class KpiCard(tk.Canvas):
    """Elevated Fluent metric card with top accent bar, bold numeric value, and context label."""

    def __init__(
        self,
        parent,
        title: str,
        value: str,
        subtext: str,
        accent_color: str = ACCENT_CYAN,
        height: int = 100,
        **kwargs
    ):
        try:
            parent_bg = parent["bg"]
        except Exception:
            parent_bg = "#0B0F17"

        super().__init__(parent, bg=parent_bg, height=height, highlightthickness=0, bd=0, **kwargs)
        self.title_text = title.upper()
        self.value_text = value
        self.sub_text = subtext
        self.accent_color = accent_color
        self.card_bg = BG_CARD
        self.border_color = BORDER_COLOR

        self.bind("<Configure>", lambda e: self._draw())

    def update_data(self, value: str, subtext: Optional[str] = None):
        self.value_text = value
        if subtext is not None:
            self.sub_text = subtext
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20 or h < 20:
            return

        # 1. Rounded rectangle background
        self.create_rectangle(1, 1, w - 1, h - 1, fill=self.card_bg, outline=self.border_color, width=1)

        # 2. Top accent highlight bar
        self.create_rectangle(1, 1, w - 1, 4, fill=self.accent_color, outline="")

        # 3. Label / Title
        self.create_text(
            16, 20,
            text=self.title_text,
            fill=FLUENT_TEXT_SECONDARY,
            anchor="w",
            font=FONT_SMALL_BOLD
        )

        # 4. Big Primary Value
        self.create_text(
            16, 48,
            text=self.value_text,
            fill=FLUENT_TEXT_PRIMARY,
            anchor="w",
            font=("Segoe UI Variable Display", 18, "bold")
        )

        # 5. Context / Subtext
        self.create_text(
            16, 76,
            text=self.sub_text,
            fill=self.accent_color,
            anchor="w",
            font=("Segoe UI Variable Text", 9)
        )
