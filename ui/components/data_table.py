"""Modern Dark Fluent Data Table Component.
Provides styled column headers, alternating row striping, sorting, and fast rendering.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Optional, Callable
from ..theme import (
    BG_CARD, BG_DARK, BORDER_COLOR, FLUENT_TEXT_PRIMARY,
    FLUENT_TEXT_SECONDARY, FONT_SMALL_BOLD, FONT_SMALL, FONT_BODY,
    apply_fluent_scrollbar_style
)


class FluentDataTable(tk.Frame):
    """WinUI 3 Dark-Themed Data Table with Column Headers, Sorting, and Custom Styling."""

    def __init__(
        self,
        parent,
        columns: List[Tuple[str, str, int]],  # (col_id, display_title, width)
        **kwargs
    ):
        try:
            parent_bg = parent["bg"]
        except Exception:
            parent_bg = BG_CARD

        super().__init__(parent, bg=parent_bg, **kwargs)
        self.columns_info = columns
        self.col_ids = [c[0] for c in columns]
        self._raw_data: List[Dict[str, Any]] = []
        self._sort_reverse: Dict[str, bool] = {c[0]: False for c in columns}

        self._setup_style()
        self._build_table()

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        apply_fluent_scrollbar_style(style)

        style.configure(
            "Fluent.Treeview",
            background="#111827",
            foreground="#F8FAFC",
            fieldbackground="#111827",
            borderwidth=0,
            font=("Segoe UI Variable Text", 9),
            rowheight=28
        )
        style.configure(
            "Fluent.Treeview.Heading",
            background="#162033",
            foreground="#94A3B8",
            relief="flat",
            borderwidth=0,
            font=("Segoe UI Variable Display", 9, "bold")
        )
        style.map(
            "Fluent.Treeview.Heading",
            background=[("active", "#1E293B")]
        )
        style.map(
            "Fluent.Treeview",
            background=[("selected", "#1E3A8A")],
            foreground=[("selected", "#00E5FF")]
        )

    def _build_table(self):
        self.tree = ttk.Treeview(
            self,
            columns=self.col_ids,
            show="headings",
            style="Fluent.Treeview",
            selectmode="browse"
        )
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview, style="Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Configure columns
        for col_id, title, width in self.columns_info:
            self.tree.heading(
                col_id,
                text=title,
                command=lambda cid=col_id: self._sort_column(cid)
            )
            self.tree.column(col_id, width=width, minwidth=60, anchor="w")

        # Alternating row tag colors
        self.tree.tag_configure("even", background="#111827")
        self.tree.tag_configure("odd", background="#151D2A")

    def set_data(self, data_list: List[Dict[str, Any]]):
        self._raw_data = data_list
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for idx, item in enumerate(self._raw_data):
            row_vals = [str(item.get(cid, "")) for cid in self.col_ids]
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree.insert("", "end", values=row_vals, tags=(tag,))

    def _sort_column(self, col_id: str):
        rev = self._sort_reverse[col_id]
        self._sort_reverse[col_id] = not rev

        def sort_key(item):
            val = item.get(col_id, "")
            try:
                clean = str(val).replace("%", "").replace("M", "").replace(",", "").replace("+", "").strip()
                return float(clean)
            except ValueError:
                return str(val).lower()

        self._raw_data.sort(key=sort_key, reverse=rev)
        self.refresh()
