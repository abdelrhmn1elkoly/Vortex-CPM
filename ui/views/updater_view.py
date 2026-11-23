"""Weekly Site Progress & XER Updater View.
Loads Baseline .XER, imports weekly site progress .XLSX, applies updates,
recalculates project controls, and generates updated Primavera schedule files.
"""

from __future__ import annotations
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional
from ..theme import (
    BG_DARK, BG_CARD, BORDER_COLOR, ACCENT_CYAN, ACCENT_BLUE,
    ACCENT_GREEN, ACCENT_AMBER, ACCENT_RED, FLUENT_TEXT_PRIMARY,
    FLUENT_TEXT_SECONDARY, FONT_TITLE, FONT_SECTION, FONT_BODY,
    FONT_BODY_BOLD, FONT_SMALL, FONT_MONO, FluentButton, FluentInfoBar, FluentIcon
)
from core.project_state import get_project_state


class UpdaterView(tk.Frame):
    """View dedicated to schedule baseline updates and site progress ingestion."""

    def __init__(self, parent, on_navigate_dashboard: Optional[callable] = None, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.state = get_project_state()
        self.on_navigate_dashboard = on_navigate_dashboard

        self._build_ui()
        self._sync_inputs()

    def _build_ui(self):
        container = tk.Frame(self, bg=BG_DARK)
        container.pack(fill="both", expand=True, padx=28, pady=20)

        # Header
        lbl_head = tk.Label(
            container,
            text="Primavera P6 Baseline (.XER) & Weekly Site Excel Updater",
            font=FONT_TITLE, bg=BG_DARK, fg=FLUENT_TEXT_PRIMARY
        )
        lbl_head.pack(anchor="w", pady=(0, 4))

        lbl_desc = tk.Label(
            container,
            text="Select your baseline schedule (.XER) and weekly progress sheet (.XLSX). The engine updates TASK statuses, EVM costs, remaining durations, and recalculates the entire dashboard.",
            font=FONT_BODY, bg=BG_DARK, fg=FLUENT_TEXT_SECONDARY, wraplength=900, justify="left"
        )
        lbl_desc.pack(anchor="w", pady=(0, 16))

        # InfoBar for alerts
        self.infobar = FluentInfoBar(container)

        # Control Card
        card = tk.Frame(container, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COLOR)
        card.pack(fill="x", pady=(0, 18), ipady=8)

        card_lay = tk.Frame(card, bg=BG_CARD)
        card_lay.pack(fill="x", padx=16, pady=12)

        # 1. Baseline File Selection
        f1 = tk.Frame(card_lay, bg=BG_CARD)
        f1.pack(fill="x", pady=6)
        tk.Label(f1, text="1. Baseline P6 Schedule (.XER):", font=FONT_BODY_BOLD, bg=BG_CARD, fg=FLUENT_TEXT_PRIMARY, width=28, anchor="w").pack(side="left")
        self.btn_pick_xer = FluentButton(f1, text="📁 Choose Baseline .XER", command=self.pick_baseline, width=220)
        self.btn_pick_xer.pack(side="left", padx=(0, 12))
        self.lbl_xer_status = tk.Label(f1, text="No baseline file selected", font=FONT_BODY, bg=BG_CARD, fg=FLUENT_TEXT_SECONDARY)
        self.lbl_xer_status.pack(side="left")

        # 2. Site Progress Excel Selection
        f2 = tk.Frame(card_lay, bg=BG_CARD)
        f2.pack(fill="x", pady=6)
        tk.Label(f2, text="2. Weekly Progress Sheet (.XLSX):", font=FONT_BODY_BOLD, bg=BG_CARD, fg=FLUENT_TEXT_PRIMARY, width=28, anchor="w").pack(side="left")
        self.btn_pick_xls = FluentButton(f2, text="📊 Choose Progress Excel", command=self.pick_excel, width=220)
        self.btn_pick_xls.pack(side="left", padx=(0, 12))
        self.lbl_xls_status = tk.Label(f2, text="No weekly progress sheet selected", font=FONT_BODY, bg=BG_CARD, fg=FLUENT_TEXT_SECONDARY)
        self.lbl_xls_status.pack(side="left")

        # 3. Data Date Selector
        f3 = tk.Frame(card_lay, bg=BG_CARD)
        f3.pack(fill="x", pady=6)
        tk.Label(f3, text="3. Schedule Data Date (YYYY-MM-DD):", font=FONT_BODY_BOLD, bg=BG_CARD, fg=FLUENT_TEXT_PRIMARY, width=28, anchor="w").pack(side="left")
        self.ent_data_date = tk.Entry(
            f3, font=("Segoe UI Variable Text", 10), bg="#0F172A", fg="#F8FAFC",
            insertbackground="#FFF", relief="flat", highlightthickness=1,
            highlightbackground="#334155", highlightcolor=ACCENT_CYAN, width=16
        )
        self.ent_data_date.insert(0, self.state.data_date)
        self.ent_data_date.pack(side="left", padx=(0, 12), ipady=3)
        tk.Label(f3, text="(e.g., 2026-10-29)", font=FONT_SMALL, bg=BG_CARD, fg=FLUENT_TEXT_SECONDARY).pack(side="left")

        # 4. Action Buttons
        f4 = tk.Frame(card_lay, bg=BG_CARD)
        f4.pack(fill="x", pady=(14, 4))
        self.btn_apply = FluentButton(
            f4, text="⚡ Apply Weekly Progress to Baseline & Update XER",
            command=self.run_update, variant="accent", height=38, width=380
        )
        self.btn_apply.pack(side="left")

        # Log & Details Panel
        log_panel = tk.Frame(container, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COLOR)
        log_panel.pack(fill="both", expand=True)

        log_head = tk.Frame(log_panel, bg=BG_CARD)
        log_head.pack(fill="x", padx=14, pady=(10, 6))
        tk.Label(log_head, text="📋 Execution & Audit Log", font=FONT_SECTION, bg=BG_CARD, fg=FLUENT_TEXT_PRIMARY).pack(side="left")

        self.txt_log = tk.Text(
            log_panel, font=FONT_MONO, bg="#0B0F17", fg="#E2E8F0",
            relief="flat", highlightthickness=0, padx=12, pady=10
        )
        self.txt_log.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Initial instruction log
        self._log("AutoPlan Studio initialized.\nStep 1: Choose Baseline .XER\nStep 2: Choose Weekly Site Progress Excel (.XLSX)\nStep 3: Click 'Apply Weekly Progress' to update schedule and recalculate dashboard.\n")

    def _sync_inputs(self):
        if self.state.baseline_path:
            self.lbl_xer_status.configure(
                text=f"✅ {os.path.basename(self.state.baseline_path)} ({self.state.xer_engine.get_project_summary().get('task_count', 0)} activities)",
                fg=ACCENT_GREEN
            )
        if self.state.site_excel_path:
            self.lbl_xls_status.configure(
                text=f"✅ {os.path.basename(self.state.site_excel_path)} ({len(self.state.progress_map)} activities parsed)",
                fg=ACCENT_GREEN
            )
        self.ent_data_date.delete(0, tk.END)
        self.ent_data_date.insert(0, self.state.data_date)

    def _log(self, text: str):
        self.txt_log.insert(tk.END, text + "\n")
        self.txt_log.see(tk.END)

    def pick_baseline(self):
        path = filedialog.askopenfilename(
            title="Choose Primavera P6 Baseline (.XER)",
            filetypes=[("Primavera P6 XER Files", "*.xer *.exr"), ("All Files", "*.*")]
        )
        if path:
            try:
                summary = self.state.load_baseline(path)
                self.lbl_xer_status.configure(
                    text=f"✅ {os.path.basename(path)} ({summary.get('task_count', 0)} tasks, BAC: {self.state.analytics.get('bac', 0)/1e6:.2f}M EGP)",
                    fg=ACCENT_GREEN
                )
                self._log(f"Loaded Baseline XER: {path}")
                self._log(f"   Project: {summary.get('project_name')}")
                self._log(f"   Tasks: {summary.get('task_count')} | Resources: {summary.get('resource_count')} | Relationships: {summary.get('pred_count')}")
                if summary.get("data_date"):
                    self.ent_data_date.delete(0, tk.END)
                    self.ent_data_date.insert(0, summary["data_date"])
                self.infobar.show(f"Baseline loaded successfully: {os.path.basename(path)}", severity="success")
            except Exception as e:
                self.infobar.show(f"Failed to parse Baseline XER: {e}", severity="error")
                messagebox.showerror("Error Loading Baseline", str(e))

    def pick_excel(self):
        path = filedialog.askopenfilename(
            title="Choose Weekly Site Progress Excel (.XLSX)",
            filetypes=[("Excel Workbooks", "*.xlsx *.xls *.csv"), ("All Files", "*.*")]
        )
        if path:
            try:
                summary = self.state.load_site_excel(path)
                self.lbl_xls_status.configure(
                    text=f"✅ {os.path.basename(path)} ({summary.get('total_parsed', 0)} activities across {len(summary.get('sheets_processed', []))} sheets)",
                    fg=ACCENT_GREEN
                )
                self._log(f"Loaded Site Progress Excel: {path}")
                self._log(f"   Activities parsed: {summary.get('total_parsed')}")
                self._log(f"   Sheets processed: {', '.join(summary.get('sheets_processed', []))}")
                self._log(f"   Clusters detected: {', '.join(summary.get('clusters_found', []))}")
                self.infobar.show(f"Progress sheet parsed: {summary.get('total_parsed')} activities found across {len(summary.get('sheets_processed', []))} sheets.", severity="success")
            except Exception as e:
                self.infobar.show(f"Failed to parse Progress Excel: {e}", severity="error")
                messagebox.showerror("Error Loading Progress Sheet", str(e))

    def run_update(self):
        if not self.state.baseline_path:
            self.infobar.show("Please select a Baseline XER file first.", severity="warning")
            messagebox.showwarning("Baseline Missing", "Please select a Baseline XER file first.")
            return

        dd = self.ent_data_date.get().strip()
        if not dd:
            self.infobar.show("Please enter a valid Data Date (YYYY-MM-DD).", severity="warning")
            return

        try:
            self._log(f"\n=======================================================")
            self._log(f"Running Update Pipeline with Data Date: {dd}...")
            res = self.state.apply_update_pipeline(dd)

            stats = res.get("update_stats", {})
            a = res.get("analytics", {})
            out_xer = res.get("updated_xer_path", "")

            self._log(f"✅ Schedule Baseline Updated Successfully!")
            self._log(f"   Matched activities: {stats.get('matched_tasks', 0)}")
            self._log(f"   Completed tasks (100%): {stats.get('completed_tasks', 0)}")
            self._log(f"   Active tasks: {stats.get('active_tasks', 0)}")
            self._log(f"   Recalculated Earned Value (EV): {a.get('ev', 0)/1e6:.2f}M EGP (Overall Actual: {a.get('actual_pct', 0):.2f}%)")
            self._log(f"   Schedule Variance (SV): {a.get('sv', 0)/1e6:+.2f}M EGP | SPI: {a.get('spi', 0):.2f}")
            self._log(f"   Exported Updated XER to: {out_xer}")
            self._log(f"=======================================================\n")

            msg = f"Update applied successfully!\nExported updated XER:\n{out_xer}\n\nOverall Actual Progress: {a.get('actual_pct', 0):.2f}% (EV: {a.get('ev', 0)/1e6:.2f}M EGP)"
            self.infobar.show(msg, severity="success")

            if messagebox.askyesno("Update Complete", f"{msg}\n\nWould you like to open the Executive Dashboard now?"):
                if self.on_navigate_dashboard:
                    self.on_navigate_dashboard()

        except Exception as e:
            self.infobar.show(f"Update failed: {e}", severity="error")
            messagebox.showerror("Pipeline Execution Error", str(e))
