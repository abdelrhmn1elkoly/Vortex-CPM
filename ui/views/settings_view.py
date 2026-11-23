"""Project Settings & Metadata Configuration View.
Allows customizing project title, contractor, engineer, currency, and default data dates.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
from ..theme import (
    BG_DARK, BG_CARD, BORDER_COLOR, ACCENT_CYAN, FLUENT_TEXT_PRIMARY,
    FLUENT_TEXT_SECONDARY, FONT_TITLE, FONT_SECTION, FONT_BODY,
    FONT_BODY_BOLD, FluentButton, FluentInfoBar
)
from core.project_state import get_project_state


class SettingsView(tk.Frame):
    """View for adjusting project metadata and reporting preferences."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.state = get_project_state()
        self._build_ui()

    def _build_ui(self):
        container = tk.Frame(self, bg=BG_DARK)
        container.pack(fill="both", expand=True, padx=28, pady=20)

        # Header
        h_f = tk.Frame(container, bg=BG_DARK)
        h_f.pack(fill="x", pady=(0, 6))
        tk.Label(
            h_f, text="⚙️ Project Controls & Metadata Settings",
            font=FONT_TITLE, bg=BG_DARK, fg=FLUENT_TEXT_PRIMARY
        ).pack(side="left")

        tk.Label(
            container,
            text="Customize contractual project metadata, parties, currency, and report headers.",
            font=FONT_BODY, bg=BG_DARK, fg=FLUENT_TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 16))

        self.infobar = FluentInfoBar(container)

        # Card
        card = tk.Frame(container, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COLOR)
        card.pack(fill="x", pady=10, ipady=10)

        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(fill="x", padx=20, pady=16)

        self.entries = {}
        fields = [
            ("project_title", "Project Title / Package:", self.state.project_title),
            ("contractor", "Contractor Name:", self.state.contractor),
            ("engineer", "Supervising Consultant / Engineer:", self.state.engineer),
            ("client", "Client / Employer:", self.state.client),
            ("currency", "Project Currency Symbol:", self.state.currency),
            ("data_date", "Default Data Date (YYYY-MM-DD):", self.state.data_date)
        ]

        for key, label_text, default_val in fields:
            row_f = tk.Frame(inner, bg=BG_CARD)
            row_f.pack(fill="x", pady=8)

            tk.Label(
                row_f, text=label_text, font=FONT_BODY_BOLD,
                bg=BG_CARD, fg=FLUENT_TEXT_PRIMARY, width=32, anchor="w"
            ).pack(side="left")

            ent = tk.Entry(
                row_f, font=("Segoe UI Variable Text", 9), bg="#0B0F17", fg="#F8FAFC",
                insertbackground="#FFF", relief="flat", highlightthickness=1,
                highlightbackground="#334155", highlightcolor=ACCENT_CYAN, width=50
            )
            ent.insert(0, default_val)
            ent.pack(side="left", ipady=4)
            self.entries[key] = ent

        # Save Button
        b_f = tk.Frame(inner, bg=BG_CARD)
        b_f.pack(fill="x", pady=(18, 4))
        FluentButton(
            b_f, text="💾 Save Project Settings",
            command=self.save_settings, variant="accent", height=36, width=220
        ).pack(side="left")

    def save_settings(self):
        self.state.project_title = self.entries["project_title"].get().strip()
        self.state.contractor = self.entries["contractor"].get().strip()
        self.state.engineer = self.entries["engineer"].get().strip()
        self.state.client = self.entries["client"].get().strip()
        self.state.currency = self.entries["currency"].get().strip()
        self.state.data_date = self.entries["data_date"].get().strip()

        self.state.recalculate_analytics()
        self.state.notify_listeners()
        self.infobar.show("Project settings saved successfully and reports refreshed!", severity="success")
