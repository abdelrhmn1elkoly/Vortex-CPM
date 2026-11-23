"""Executive Export & Reporting Center View.
Provides one-click exporting to Multi-Tab Excel, Print-Ready PDF,
Interactive HTML Web Dashboard, and Updated Primavera P6 .XER schedule files.
"""

from __future__ import annotations
import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional
from ..theme import (
    BG_DARK, BG_CARD, BORDER_COLOR, ACCENT_CYAN, ACCENT_BLUE,
    ACCENT_GREEN, ACCENT_AMBER, FLUENT_TEXT_PRIMARY, FLUENT_TEXT_SECONDARY,
    FONT_TITLE, FONT_SECTION, FONT_BODY, FONT_BODY_BOLD, FONT_SMALL,
    FluentButton, FluentInfoBar, FluentIcon
)
from core.project_state import get_project_state
from core.excel_exporter import ExcelExporter
from core.pdf_exporter import PDFExporter


class ExportView(tk.Frame):
    """View dedicated to output deliverables: Excel, PDF, Web Dashboard, and updated XER."""

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
            h_f, text="📑 Executive Reports & Export Center",
            font=FONT_TITLE, bg=BG_DARK, fg=FLUENT_TEXT_PRIMARY
        ).pack(side="left")

        tk.Label(
            container,
            text="Generate high-definition PDF reports, multi-tab Excel workbooks, interactive standalone web dashboards, or export the updated Primavera P6 schedule file.",
            font=FONT_BODY, bg=BG_DARK, fg=FLUENT_TEXT_SECONDARY, wraplength=900, justify="left"
        ).pack(anchor="w", pady=(0, 16))

        self.infobar = FluentInfoBar(container)

        # 4 Export Cards Grid
        grid_f = tk.Frame(container, bg=BG_DARK)
        grid_f.pack(fill="both", expand=True, pady=10)

        # Card 1: Multi-Tab Excel Workbook
        self._create_export_card(
            grid_f,
            title="📊 Multi-Tab Executive Excel Workbook (.XLSX)",
            desc="Generates a formatted, multi-sheet Excel workbook (Executive Dashboard, Cluster Matrix, Discipline Breakdown, Lookahead, S-Curve log, and Out-of-Sequence audit).",
            btn_text="⬇️ Export Excel Workbook",
            btn_variant="accent",
            command=self.export_excel,
            row=0, col=0
        )

        # Card 2: Print-Ready PDF Report
        self._create_export_card(
            grid_f,
            title="🖨️ Executive PDF Report (.PDF)",
            desc="Renders an executive, high-resolution vector PDF using Microsoft Edge headless rendering, complete with S-Curve charts, cluster tables, and contractual milestones.",
            btn_text="⬇️ Export / Print PDF",
            btn_variant="standard",
            command=self.export_pdf,
            row=0, col=1
        )

        # Card 3: Interactive HTML5 Web Dashboard
        self._create_export_card(
            grid_f,
            title="🌐 Standalone Interactive Web Dashboard (.HTML)",
            desc="Exports a self-contained, offline HTML5 dashboard with dynamic Chart.js animations, live search filtering, and dark Fluent styling to share with clients or management.",
            btn_text="🚀 Open Web Dashboard",
            btn_variant="standard",
            command=self.open_web_dashboard,
            row=1, col=0
        )

        # Card 4: Updated Primavera P6 .XER
        self._create_export_card(
            grid_f,
            title="⚡ Updated Primavera P6 Schedule (.XER)",
            desc="Exports the updated schedule with synchronized TASK physical completion percentages, remaining durations, actual dates, and recalculated TASKRSRC resource costs.",
            btn_text="💾 Save Updated .XER File",
            btn_variant="standard",
            command=self.export_xer,
            row=1, col=1
        )

        # Bottom Open Output Directory Button
        bot_f = tk.Frame(container, bg=BG_DARK)
        bot_f.pack(fill="x", pady=(18, 0))
        FluentButton(
            bot_f, text="📂 Open Project Exports Directory",
            command=self.open_export_dir, width=240
        ).pack(side="left")

    def _create_export_card(self, parent, title, desc, btn_text, btn_variant, command, row, col):
        card = tk.Frame(parent, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COLOR)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        parent.grid_columnconfigure(col, weight=1)
        parent.grid_rowconfigure(row, weight=1)

        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(fill="both", expand=True, padx=20, pady=18)

        tk.Label(inner, text=title, font=FONT_SECTION, bg=BG_CARD, fg=FLUENT_TEXT_PRIMARY, anchor="w").pack(fill="x", pady=(0, 8))
        tk.Label(inner, text=desc, font=FONT_BODY, bg=BG_CARD, fg=FLUENT_TEXT_SECONDARY, wraplength=420, justify="left", anchor="w").pack(fill="x", pady=(0, 16))

        btn = FluentButton(inner, text=btn_text, command=command, variant=btn_variant, height=36, width=240)
        btn.pack(side="bottom", anchor="w")

    def export_excel(self):
        if not self.state.analytics:
            self.infobar.show("No schedule data loaded to export. Please load baseline first.", severity="warning")
            return

        def_name = f"HPT_Weekly_Report_{self.state.data_date}.xlsx"
        p = filedialog.asksaveasfilename(
            title="Save Executive Excel Workbook",
            defaultextension=".xlsx",
            initialfile=def_name,
            filetypes=[("Excel Workbooks", "*.xlsx")]
        )
        if p:
            try:
                ExcelExporter.export(self.state.analytics, p)
                self.infobar.show(f"Excel workbook exported successfully:\n{p}", severity="success")
                if messagebox.askyesno("Export Complete", f"Excel report generated!\n{p}\n\nDo you want to open it now?"):
                    os.startfile(p)
            except Exception as e:
                self.infobar.show(f"Failed to export Excel: {e}", severity="error")

    def export_pdf(self):
        if not self.state.analytics:
            self.infobar.show("No schedule data loaded to export. Please load baseline first.", severity="warning")
            return

        def_name = f"HPT_Executive_Report_{self.state.data_date}.pdf"
        p = filedialog.asksaveasfilename(
            title="Save Executive PDF Report",
            defaultextension=".pdf",
            initialfile=def_name,
            filetypes=[("PDF Documents", "*.pdf")]
        )
        if p:
            success, msg = PDFExporter.export_pdf(self.state.analytics, p)
            self.infobar.show(msg, severity="success" if success else "info")
            if success and os.path.exists(p):
                if messagebox.askyesno("PDF Export Complete", f"PDF generated successfully!\n{p}\n\nDo you want to open it now?"):
                    os.startfile(p)

    def open_web_dashboard(self):
        if not self.state.analytics:
            self.infobar.show("No schedule data loaded to view dashboard.", severity="warning")
            return

        target_dir = os.path.dirname(self.state.baseline_path) if self.state.baseline_path else os.getcwd()
        html_path = os.path.join(target_dir, f"AutoPlan_Studio_Dashboard_{self.state.data_date}.html")
        PDFExporter.preview_in_browser(self.state.analytics, html_path)
        self.infobar.show(f"Interactive web dashboard generated:\n{html_path}", severity="success")

    def export_xer(self):
        if not self.state.xer_engine:
            self.infobar.show("No baseline XER loaded to export.", severity="warning")
            return

        def_name = f"HT-1_BL_UPDATED_{self.state.data_date}.xer"
        p = filedialog.asksaveasfilename(
            title="Save Updated Primavera P6 .XER",
            defaultextension=".xer",
            initialfile=def_name,
            filetypes=[("Primavera P6 Files", "*.xer *.exr")]
        )
        if p:
            try:
                self.state.xer_engine.export_xer(p)
                self.infobar.show(f"Updated P6 schedule exported:\n{p}", severity="success")
                messagebox.showinfo("XER Exported", f"Successfully exported updated Primavera P6 schedule:\n{p}")
            except Exception as e:
                self.infobar.show(f"Failed to export XER: {e}", severity="error")

    def open_export_dir(self):
        target_dir = os.path.dirname(self.state.baseline_path) if self.state.baseline_path else os.getcwd()
        if os.path.exists(target_dir):
            os.startfile(target_dir)
