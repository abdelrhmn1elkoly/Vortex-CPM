"""Executive Multi-Tab Excel Workbook Exporter.
Generates polished, formatted project controls workbooks with KPI tiles,
Cluster progress matrices, EVM financial tables, S-curves, and logic audits.
"""

from __future__ import annotations
import os
from typing import Dict, Any, List, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


class ExcelExporter:
    """Exports comprehensive project analytics into a beautifully styled multi-tab Excel workbook."""

    # Colors & Palettes (Fluent Slate / Navy)
    NAVY_HEADER = "0F172A"
    CARD_BG = "1E293B"
    SUBTLE_BG = "F8FAFC"
    BORDER_COLOR = "CBD5E1"
    ACCENT_CYAN = "00E5FF"
    ACCENT_BLUE = "2563EB"
    TEXT_WHITE = "FFFFFF"
    TEXT_MUTED = "64748B"
    TEXT_DARK = "0F172A"

    GREEN_FILL = "DCFCE7"
    GREEN_TEXT = "166534"
    AMBER_FILL = "FEF3C7"
    AMBER_TEXT = "92400E"
    RED_FILL = "FEE2E2"
    RED_TEXT = "991B1B"

    @classmethod
    def export_workbook(cls, analytics: Dict[str, Any], output_path: str) -> tuple[bool, str]:
        """Convenience method returning (success: bool, message: str)."""
        try:
            res = cls.export(analytics, output_path)
            return True, f"Excel workbook successfully written to:\n{res}"
        except Exception as e:
            return False, f"Excel export failed: {e}"

    @classmethod
    def export(cls, analytics: Dict[str, Any], output_path: str) -> str:
        """Generates the multi-sheet Excel workbook from analytics data."""
        wb = openpyxl.Workbook()
        # Remove default sheet
        wb.remove(wb.active)

        # 1. Executive Dashboard Sheet
        cls._build_dashboard_sheet(wb, analytics)

        # 2. Cluster Progress Matrix Sheet
        cls._build_cluster_sheet(wb, analytics)

        # 3. Discipline Performance Sheet
        cls._build_discipline_sheet(wb, analytics)

        # 4. Lookahead & Delays Sheet
        cls._build_lookahead_sheet(wb, analytics)

        # 5. Out-of-Sequence Ties Sheet
        cls._build_oos_sheet(wb, analytics)

        # 6. S-Curve Weekly Log Sheet
        cls._build_scurve_sheet(wb, analytics)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        wb.save(output_path)
        return output_path

    @classmethod
    def _style_header_cell(cls, cell, text, bg_hex=NAVY_HEADER, font_color="FFFFFF", font_size=11, bold=True):
        cell.value = text
        cell.fill = PatternFill(start_color=bg_hex, end_color=bg_hex, fill_type="solid")
        cell.font = Font(name="Segoe UI", size=font_size, bold=bold, color=font_color)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    @classmethod
    def _build_dashboard_sheet(cls, wb, a: Dict[str, Any]):
        ws = wb.create_sheet(title="Executive Dashboard")
        ws.views.sheetView[0].showGridLines = True

        thin = Side(style="thin", color="E2E8F0")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        # Title Banner
        ws.merge_cells("A1:H1")
        title_cell = ws["A1"]
        cls._style_header_cell(title_cell, f"PROJECT CONTROLS & EXECUTIVE DASHBOARD — {a.get('project_name', 'HAPTOWN')}", bg_hex=cls.NAVY_HEADER, font_size=13)
        ws.row_dimensions[1].height = 36

        # Subtitle
        ws.merge_cells("A2:H2")
        sub_cell = ws["A2"]
        sub_text = f"Data Date: {a.get('data_date')}   |   Commencement: {a.get('commencement')}   |   Contract Completion: {a.get('contract_finish')}   |   Baseline: {a.get('baseline_name')}"
        cls._style_header_cell(sub_cell, sub_text, bg_hex="1E293B", font_size=10, bold=False)
        ws.row_dimensions[2].height = 24

        # KPI Tiles Row (A4:H5)
        kpis = [
            ("OVERALL PHYSICAL PROGRESS", f"{a.get('actual_pct', 0):.2f}%", f"Planned: {a.get('planned_pct', 0):.2f}% (Var: {a.get('variance_pct', 0):+.2f}%)", "A4:B5"),
            ("EARNED VALUE (EV)", f"{a.get('ev', 0)/1e6:.2f}M EGP", f"PV: {a.get('pv', 0)/1e6:.2f}M  |  BAC: {a.get('bac', 0)/1e6:.2f}M", "C4:D5"),
            ("SCHEDULE INDEX (SPI)", f"{a.get('spi', 0):.2f}", f"SV: {a.get('sv', 0)/1e6:+.2f}M EGP", "E4:F5"),
            ("FORECAST COMPLETION", str(a.get("forecast_finish", "")), f"Contract Delay: {a.get('variance_days', 0)} days", "G4:H5")
        ]

        for title, val, sub, rng in kpis:
            c1, c2 = rng.split(":")
            ws.merge_cells(rng)
            top_cell = ws[c1]
            top_cell.value = f"{title}\n{val}\n{sub}"
            top_cell.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
            top_cell.font = Font(name="Segoe UI", size=10, bold=True, color="0F172A")
            top_cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        ws.row_dimensions[4].height = 30
        ws.row_dimensions[5].height = 30

        # Financial Summary Table
        ws["A7"] = "EVM & Financial Tracking Metrics"
        ws["A7"].font = Font(name="Segoe UI", size=12, bold=True, color="0F172A")

        headers = ["Metric Description", "Amount (EGP)", "% of BAC", "Benchmark / Threshold", "Health Status"]
        for col_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=8, column=col_idx)
            cls._style_header_cell(cell, h, bg_hex="334155", font_size=10)

        bac = a.get("bac", 0.0)
        pv = a.get("pv", 0.0)
        ev = a.get("ev", 0.0)
        sv = a.get("sv", 0.0)
        spi = a.get("spi", 0.0)

        rows_data = [
            ("Total Budget at Completion (BAC)", bac, 100.0, "Contract Baseline", "Baseline"),
            ("Planned Value (PV) to Data Date", pv, (pv / bac * 100) if bac else 0, "Target Schedule", "Schedule"),
            ("Earned Value (EV) Achieved", ev, (ev / bac * 100) if bac else 0, "Physical Performance", "Current"),
            ("Schedule Variance (SV = EV - PV)", sv, (sv / bac * 100) if bac else 0, "SV > 0 is Ahead", "Behind" if sv < 0 else "Ahead"),
            ("Schedule Performance Index (SPI)", spi, 0.0, "SPI >= 1.0 is on-schedule", "Critical" if spi < 0.4 else ("Delayed" if spi < 0.8 else "Healthy")),
            ("Remaining Work Budget (BAC - EV)", bac - ev, ((bac - ev) / bac * 100) if bac else 0, "Balance to Finish", "Pending")
        ]

        for r_idx, (m_desc, amt, pct_val, bench, status) in enumerate(rows_data, start=9):
            ws.cell(row=r_idx, column=1, value=m_desc).font = Font(name="Segoe UI", size=10, bold=(r_idx in (9, 11, 13)))
            c2 = ws.cell(row=r_idx, column=2, value=amt)
            if "Index" in m_desc:
                c2.number_format = "0.00"
            else:
                c2.number_format = "#,##0.00"

            c3 = ws.cell(row=r_idx, column=3, value=pct_val / 100.0)
            c3.number_format = "0.0%"

            ws.cell(row=r_idx, column=4, value=bench).font = Font(name="Segoe UI", size=9, color="64748B")
            st_cell = ws.cell(row=r_idx, column=5, value=status)
            st_cell.alignment = Alignment(horizontal="center")
            if status in ("Critical", "Behind"):
                st_cell.fill = PatternFill(start_color=cls.RED_FILL, end_color=cls.RED_FILL, fill_type="solid")
                st_cell.font = Font(name="Segoe UI", size=9, bold=True, color=cls.RED_TEXT)
            elif status in ("Delayed", "Attention"):
                st_cell.fill = PatternFill(start_color=cls.AMBER_FILL, end_color=cls.AMBER_FILL, fill_type="solid")
                st_cell.font = Font(name="Segoe UI", size=9, bold=True, color=cls.AMBER_TEXT)
            else:
                st_cell.fill = PatternFill(start_color=cls.GREEN_FILL, end_color=cls.GREEN_FILL, fill_type="solid")
                st_cell.font = Font(name="Segoe UI", size=9, bold=True, color=cls.GREEN_TEXT)

            for col in range(1, 6):
                ws.cell(row=r_idx, column=col).border = border

        # Auto-fit column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

    @classmethod
    def _build_cluster_sheet(cls, wb, a: Dict[str, Any]):
        ws = wb.create_sheet(title="Cluster Progress")
        ws.views.sheetView[0].showGridLines = True

        ws.merge_cells("A1:M1")
        title_cell = ws["A1"]
        cls._style_header_cell(title_cell, "CLUSTER PROGRESS & EARNED VALUE MATRIX (C08 to C18)", bg_hex=cls.NAVY_HEADER, font_size=12)
        ws.row_dimensions[1].height = 30

        headers = [
            "Cluster", "Budget (BAC)", "Weight %", "Planned %", "Actual %", "Variance %",
            "PV (EGP)", "EV (EGP)", "SV (EGP)", "SPI", "Baseline Finish", "Forecast Finish", "Slip (Days)"
        ]

        for col_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=2, column=col_idx)
            cls._style_header_cell(cell, h, bg_hex="1E293B", font_size=9)
        ws.row_dimensions[2].height = 24

        thin = Side(style="thin", color="E2E8F0")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        for r_idx, c in enumerate(a.get("clusters", []), start=3):
            ws.cell(row=r_idx, column=1, value=c["cluster"]).font = Font(name="Segoe UI", size=10, bold=True)
            c2 = ws.cell(row=r_idx, column=2, value=c["bac"])
            c2.number_format = "#,##0.00"

            c3 = ws.cell(row=r_idx, column=3, value=c["weight"] / 100.0)
            c3.number_format = "0.0%"

            c4 = ws.cell(row=r_idx, column=4, value=c["planned_pct"] / 100.0)
            c4.number_format = "0.0%"

            c5 = ws.cell(row=r_idx, column=5, value=c["actual_pct"] / 100.0)
            c5.number_format = "0.0%"

            c6 = ws.cell(row=r_idx, column=6, value=c["variance_pct"] / 100.0)
            c6.number_format = "+0.0%;-0.0%;0.0%"

            c7 = ws.cell(row=r_idx, column=7, value=c["pv"])
            c7.number_format = "#,##0.00"

            c8 = ws.cell(row=r_idx, column=8, value=c["ev"])
            c8.number_format = "#,##0.00"

            c9 = ws.cell(row=r_idx, column=9, value=c["sv"])
            c9.number_format = "+#,##0.00;-#,##0.00;0.00"

            spi_cell = ws.cell(row=r_idx, column=10, value=c["spi"])
            spi_cell.number_format = "0.00"
            spi_cell.alignment = Alignment(horizontal="center")
            if c["spi"] < 0.4:
                spi_cell.fill = PatternFill(start_color=cls.RED_FILL, end_color=cls.RED_FILL, fill_type="solid")
                spi_cell.font = Font(name="Segoe UI", size=9, bold=True, color=cls.RED_TEXT)
            elif c["spi"] < 0.8:
                spi_cell.fill = PatternFill(start_color=cls.AMBER_FILL, end_color=cls.AMBER_FILL, fill_type="solid")
                spi_cell.font = Font(name="Segoe UI", size=9, bold=True, color=cls.AMBER_TEXT)
            else:
                spi_cell.fill = PatternFill(start_color=cls.GREEN_FILL, end_color=cls.GREEN_FILL, fill_type="solid")
                spi_cell.font = Font(name="Segoe UI", size=9, bold=True, color=cls.GREEN_TEXT)

            ws.cell(row=r_idx, column=11, value=c.get("bl_finish", ""))
            ws.cell(row=r_idx, column=12, value=c.get("fcst_finish", ""))
            slip_cell = ws.cell(row=r_idx, column=13, value=c.get("slip_days", 0))
            slip_cell.number_format = "#,##0"

            for col in range(1, 14):
                ws.cell(row=r_idx, column=col).border = border

        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    @classmethod
    def _build_discipline_sheet(cls, wb, a: Dict[str, Any]):
        ws = wb.create_sheet(title="Discipline Breakdown")
        ws.views.sheetView[0].showGridLines = True

        ws.merge_cells("A1:H1")
        title_cell = ws["A1"]
        cls._style_header_cell(title_cell, "ENGINEERING DISCIPLINE PERFORMANCE & EARNED VALUE", bg_hex=cls.NAVY_HEADER, font_size=12)
        ws.row_dimensions[1].height = 30

        headers = ["Discipline", "Budget (BAC)", "Planned Value (PV)", "Planned %", "Earned Value (EV)", "Actual %", "Schedule Variance", "SPI"]
        for col_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=2, column=col_idx)
            cls._style_header_cell(cell, h, bg_hex="1E293B", font_size=9)

        thin = Side(style="thin", color="E2E8F0")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        for r_idx, d in enumerate(a.get("disciplines", []), start=3):
            ws.cell(row=r_idx, column=1, value=d["discipline"]).font = Font(name="Segoe UI", size=10, bold=True)
            ws.cell(row=r_idx, column=2, value=d["bac"]).number_format = "#,##0.00"
            ws.cell(row=r_idx, column=3, value=d["pv"]).number_format = "#,##0.00"
            ws.cell(row=r_idx, column=4, value=d["pv_pct"] / 100.0).number_format = "0.0%"
            ws.cell(row=r_idx, column=5, value=d["ev"]).number_format = "#,##0.00"
            ws.cell(row=r_idx, column=6, value=d["ev_pct"] / 100.0).number_format = "0.0%"
            ws.cell(row=r_idx, column=7, value=d["sv"]).number_format = "+#,##0.00;-#,##0.00;0.00"
            spi_c = ws.cell(row=r_idx, column=8, value=d["spi"])
            spi_c.number_format = "0.00"
            spi_c.alignment = Alignment(horizontal="center")

            for col in range(1, 9):
                ws.cell(row=r_idx, column=col).border = border

        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

    @classmethod
    def _build_lookahead_sheet(cls, wb, a: Dict[str, Any]):
        ws = wb.create_sheet(title="Lookahead & Delays")
        ws.views.sheetView[0].showGridLines = True

        ws.merge_cells("A1:I1")
        title_cell = ws["A1"]
        cls._style_header_cell(title_cell, "ACTIVE, DELAYED & 30-DAY LOOKAHEAD ACTIVITIES", bg_hex=cls.NAVY_HEADER, font_size=12)

        headers = ["Activity ID", "Activity Name", "Cluster", "Discipline", "Status", "Progress %", "Target Start", "Baseline Finish", "Delay (Days)"]
        for col_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=2, column=col_idx)
            cls._style_header_cell(cell, h, bg_hex="1E293B", font_size=9)

        thin = Side(style="thin", color="E2E8F0")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        for r_idx, act in enumerate(a.get("activities", []), start=3):
            ws.cell(row=r_idx, column=1, value=act["act_id"]).font = Font(name="Consolas", size=9)
            ws.cell(row=r_idx, column=2, value=act["act_name"])
            ws.cell(row=r_idx, column=3, value=act["cluster"])
            ws.cell(row=r_idx, column=4, value=act["discipline"])
            ws.cell(row=r_idx, column=5, value=act["status"])
            ws.cell(row=r_idx, column=6, value=act["pct"] / 100.0).number_format = "0.0%"
            ws.cell(row=r_idx, column=7, value=act.get("target_start", ""))
            ws.cell(row=r_idx, column=8, value=act.get("bl_finish", ""))
            ws.cell(row=r_idx, column=9, value=act.get("late_days", 0)).number_format = "#,##0"

            for col in range(1, 10):
                ws.cell(row=r_idx, column=col).border = border

        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(40, max(max_len + 3, 12))

    @classmethod
    def _build_oos_sheet(cls, wb, a: Dict[str, Any]):
        ws = wb.create_sheet(title="Out-of-Seq Ties")
        ws.views.sheetView[0].showGridLines = True

        ws.merge_cells("A1:G1")
        title_cell = ws["A1"]
        cls._style_header_cell(title_cell, "OUT-OF-SEQUENCE LOGIC TIE AUDIT (Predecessor Not Started → Successor In-Progress)", bg_hex=cls.NAVY_HEADER, font_size=12)

        headers = ["Predecessor ID", "Predecessor Name", "Tie", "Successor ID", "Successor Name", "Successor Status", "Successor %"]
        for col_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=2, column=col_idx)
            cls._style_header_cell(cell, h, bg_hex="1E293B", font_size=9)

        thin = Side(style="thin", color="E2E8F0")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        for r_idx, o in enumerate(a.get("oos_ties", []), start=3):
            ws.cell(row=r_idx, column=1, value=o["pred_id"]).font = Font(name="Consolas", size=9)
            ws.cell(row=r_idx, column=2, value=o["pred_name"])
            ws.cell(row=r_idx, column=3, value=o["tie"]).alignment = Alignment(horizontal="center")
            ws.cell(row=r_idx, column=4, value=o["succ_id"]).font = Font(name="Consolas", size=9)
            ws.cell(row=r_idx, column=5, value=o["succ_name"])
            ws.cell(row=r_idx, column=6, value=o["succ_status"])
            ws.cell(row=r_idx, column=7, value=o["succ_pct"] / 100.0).number_format = "0.0%"

            for col in range(1, 8):
                ws.cell(row=r_idx, column=col).border = border

        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(40, max(max_len + 3, 12))

    @classmethod
    def _build_scurve_sheet(cls, wb, a: Dict[str, Any]):
        ws = wb.create_sheet(title="S-Curve")
        ws.views.sheetView[0].showGridLines = True

        ws.merge_cells("A1:D1")
        title_cell = ws["A1"]
        cls._style_header_cell(title_cell, "WEEKLY CUMULATIVE S-CURVE DATA LOG (M EGP)", bg_hex=cls.NAVY_HEADER, font_size=12)

        headers = ["Week", "Date", "Cumulative PV (M EGP)", "Cumulative EV (M EGP)"]
        for col_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=2, column=col_idx)
            cls._style_header_cell(cell, h, bg_hex="1E293B", font_size=9)

        thin = Side(style="thin", color="E2E8F0")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        for r_idx, pt in enumerate(a.get("scurve", []), start=3):
            ws.cell(row=r_idx, column=1, value=pt["week"]).alignment = Alignment(horizontal="center")
            ws.cell(row=r_idx, column=2, value=pt["date"])
            ws.cell(row=r_idx, column=3, value=pt["pv_m"]).number_format = "#,##0.00"
            c4 = ws.cell(row=r_idx, column=4, value=pt["ev_m"])
            if pt["ev_m"] is not None:
                c4.number_format = "#,##0.00"

            for col in range(1, 5):
                ws.cell(row=r_idx, column=col).border = border

        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 16)
