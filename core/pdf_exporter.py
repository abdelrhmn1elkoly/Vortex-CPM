"""Dedicated Pure-White Executive PDF Report Generator for Vortex Controls.
Generates multi-page, publication-quality executive construction reports directly via ReportLab
and Matplotlib on a crisp white canvas (#FFFFFF) with high-contrast typography, vector S-Curves,
executive EVM scorecards, cluster performance tables, and out-of-sequence logic risk audits.
"""

from __future__ import annotations
import os
import io
import tempfile
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas


# =========================================================================
# Numbered Canvas for "Page X of Y" and Running Header/Footer
# =========================================================================
class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to compute total page count and draw running header/footer on pure white pages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, total_pages: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        w, h = letter

        # Running Top Header (Pages 2+)
        if self._pageNumber > 1:
            self.drawString(36, h - 25, "VORTEX CONTROLS  |  EXECUTIVE PROJECT PROGRESS & EVM REPORT")
            self.drawRightString(w - 36, h - 25, datetime.now().strftime("%Y-%m-%d"))
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(36, h - 29, w - 36, h - 29)

        # Running Bottom Footer (All Pages)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(36, 32, w - 36, 32)

        self.drawString(36, 20, "CONFIDENTIAL  •  FOR EXECUTIVE & PROJECT MANAGEMENT USE ONLY")
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(w - 36, 20, page_str)

        self.restoreState()


# =========================================================================
# Vector S-Curve Generator (Pure White Canvas)
# =========================================================================
def generate_scurve_chart_image(scurve_data: List[Dict[str, Any]], data_date_str: str) -> Optional[io.BytesIO]:
    """Generates a high-contrast vector S-Curve plot with pure white background."""
    if not scurve_data or len(scurve_data) < 2:
        return None

    fig, ax = plt.subplots(figsize=(7.5, 3.0), dpi=220)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    dates = []
    pv_vals = []
    ev_vals = []

    for pt in scurve_data:
        try:
            d = datetime.strptime(pt["date"][:10], "%Y-%m-%d")
            dates.append(d)
            pv_vals.append(pt.get("pv_m", 0.0))
            ev_vals.append(pt.get("ev_m"))
        except Exception:
            continue

    if not dates:
        plt.close(fig)
        return None

    # Plot Planned Value (Blue)
    ax.plot(dates, pv_vals, color="#0078D4", linewidth=2.2, label="Planned Value (PV)", zorder=3)

    # Plot Earned Value (Green/Teal)
    valid_ev = [(d, v) for d, v in zip(dates, ev_vals) if v is not None]
    if valid_ev:
        ev_dates, ev_pts = zip(*valid_ev)
        ax.plot(ev_dates, ev_pts, color="#107C41", linewidth=2.6, marker="o", markersize=4, label="Earned Value (EV)", zorder=4)

    # Data Date vertical line
    try:
        dd = datetime.strptime(data_date_str[:10], "%Y-%m-%d")
        ax.axvline(dd, color="#D9381E", linestyle="--", linewidth=1.5, label=f"Data Date ({data_date_str[:10]})", zorder=5)
    except Exception:
        pass

    # Styling for pure white executive print
    ax.set_title("CUMULATIVE EARNED VALUE PROGRESS S-CURVE (EGP MILLIONS)", fontsize=9.5, fontweight="bold", color="#0F172A", pad=10)
    ax.set_ylabel("Budget (M EGP)", fontsize=8, color="#334155", fontweight="bold")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
    ax.tick_params(colors="#334155", labelsize=7.5)
    ax.grid(True, linestyle=":", color="#E2E8F0", linewidth=0.8, alpha=0.9, zorder=1)

    # Spines
    for spine in ax.spines.values():
        spine.set_color("#CBD5E1")
        spine.set_linewidth(0.8)

    ax.legend(loc="upper left", frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1", fontsize=7.5)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor="#FFFFFF", edgecolor="none", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


# =========================================================================
# Main PDF Exporter Class
# =========================================================================
class PDFExporter:
    """Exports executive dashboards directly into a pristine, white-background multi-page PDF."""

    @classmethod
    def export_pdf(cls, analytics: Dict[str, Any], output_pdf_path: str) -> Tuple[bool, str]:
        """
        Builds a dedicated, publication-quality PDF report using ReportLab.
        Returns: (success: bool, message: str)
        """
        try:
            output_pdf_path = os.path.abspath(output_pdf_path)
            os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)

            doc = SimpleDocTemplate(
                output_pdf_path,
                pagesize=letter,
                leftMargin=36,
                rightMargin=36,
                topMargin=38,
                bottomMargin=42
            )

            styles = getSampleStyleSheet()

            # Custom Crisp Typography Styles
            style_h1 = ParagraphStyle(
                "DocH1",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=18,
                leading=22,
                textColor=colors.HexColor("#0F172A"),
            )
            style_sub = ParagraphStyle(
                "DocSub",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=9,
                leading=12,
                textColor=colors.HexColor("#475569"),
            )
            style_sec = ParagraphStyle(
                "DocSec",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=11,
                leading=14,
                textColor=colors.HexColor("#0078D4"),
                spaceBefore=8,
                spaceAfter=4
            )
            style_meta_k = ParagraphStyle(
                "MetaK",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=8,
                leading=10,
                textColor=colors.HexColor("#64748B"),
            )
            style_meta_v = ParagraphStyle(
                "MetaV",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=11,
                textColor=colors.HexColor("#0F172A"),
            )
            style_tbl_hdr = ParagraphStyle(
                "TblHdr",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=7.5,
                leading=9,
                textColor=colors.white,
                alignment=1
            )
            style_tbl_cell = ParagraphStyle(
                "TblCell",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7.5,
                leading=9,
                textColor=colors.HexColor("#1E293B"),
            )
            style_tbl_cell_bold = ParagraphStyle(
                "TblCellBold",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=7.5,
                leading=9,
                textColor=colors.HexColor("#0F172A"),
            )
            style_tbl_cell_center = ParagraphStyle(
                "TblCellCenter",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7.5,
                leading=9,
                textColor=colors.HexColor("#1E293B"),
                alignment=1
            )
            style_tbl_cell_right = ParagraphStyle(
                "TblCellRight",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7.5,
                leading=9,
                textColor=colors.HexColor("#1E293B"),
                alignment=2
            )

            story = []

            # -------------------------------------------------------------
            # 1. Header Banner & Branding
            # -------------------------------------------------------------
            proj_name = analytics.get("project_name", "Vortex CPM Construction Project")
            data_date = analytics.get("data_date", datetime.now().strftime("%Y-%m-%d"))
            baseline_name = analytics.get("baseline_name", "Primavera P6 Baseline")
            bac = analytics.get("bac", 0.0)
            pv = analytics.get("pv", 0.0)
            ev = analytics.get("ev", 0.0)
            sv = analytics.get("sv", 0.0)
            spi = analytics.get("spi", 1.0)
            plan_pct = analytics.get("planned_pct", 0.0)
            act_pct = analytics.get("actual_pct", 0.0)
            var_pct = analytics.get("variance_pct", 0.0)
            fcst_finish = analytics.get("forecast_finish", "-")
            contract_finish = analytics.get("contract_finish", "-")
            slip_days = analytics.get("variance_days", 0)

            header_data = [
                [
                    Paragraph("<b>VORTEX CONTROLS</b>  •  CONSTRUCTION PROJECT CONTROLS", style_sub),
                    Paragraph(f"<b>REPORT DATE:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", ParagraphStyle("HdrR", parent=style_sub, alignment=2))
                ],
                [
                    Paragraph(f"<b>{proj_name.upper()}</b>", style_h1),
                    Paragraph(f"<b>DATA DATE:</b> {data_date}", ParagraphStyle("HdrR2", parent=style_sub, alignment=2))
                ],
                [
                    Paragraph(f"Baseline Schedule: <b>{baseline_name}</b>  •  Contract Finish: <b>{contract_finish}</b>", style_sub),
                    Paragraph(f"Status: <b>{'ON TRACK' if spi >= 0.98 else 'BEHIND SCHEDULE'}</b>", ParagraphStyle("HdrR3", parent=style_sub, alignment=2))
                ]
            ]
            t_hdr = Table(header_data, colWidths=[5.0 * inch, 2.5 * inch])
            t_hdr.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(t_hdr)
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0078D4"), spaceAfter=10))

            # -------------------------------------------------------------
            # 2. Executive EVM KPI Scorecards (Clean White / Light Slate Boxes)
            # -------------------------------------------------------------
            kpi_data = [
                [
                    Paragraph("TOTAL BUDGET (BAC)", style_meta_k),
                    Paragraph("PLANNED VALUE (PV)", style_meta_k),
                    Paragraph("EARNED VALUE (EV)", style_meta_k),
                    Paragraph("SCHEDULE INDEX (SPI)", style_meta_k),
                    Paragraph("FORECAST FINISH", style_meta_k),
                ],
                [
                    Paragraph(f"<b>{bac/1e6:.2f}M</b> EGP", style_meta_v),
                    Paragraph(f"<b>{pv/1e6:.2f}M</b> ({plan_pct:.1f}%)", style_meta_v),
                    Paragraph(f"<b>{ev/1e6:.2f}M</b> ({act_pct:.1f}%)", style_meta_v),
                    Paragraph(f"<font color='{'#107C41' if spi >= 0.98 else '#D9381E'}'><b>{spi:.2f}</b></font> ({sv/1e6:+.2f}M)", style_meta_v),
                    Paragraph(f"<b>{fcst_finish}</b> ({slip_days}d)", style_meta_v),
                ]
            ]
            t_kpi = Table(kpi_data, colWidths=[1.5 * inch] * 5)
            t_kpi.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(t_kpi)
            story.append(Spacer(1, 10))

            # -------------------------------------------------------------
            # 3. Vector S-Curve Plot (Pure White Canvas)
            # -------------------------------------------------------------
            scurve_buf = generate_scurve_chart_image(analytics.get("scurve", []), data_date)
            if scurve_buf:
                story.append(Image(scurve_buf, width=7.5 * inch, height=3.0 * inch))
                story.append(Spacer(1, 10))

            # -------------------------------------------------------------
            # 4. Cluster Performance Matrix (C08 - C18)
            # -------------------------------------------------------------
            clusters = analytics.get("clusters", [])
            if clusters:
                story.append(Paragraph("<b>CLUSTER PROGRESSION & EARNED VALUE BREAKDOWN</b>", style_sec))

                clust_headers = ["Cluster", "Budget (BAC)", "Weight", "Planned %", "Actual %", "Variance", "Earned (EV)", "SV (EGP)", "SPI", "Finish Date"]
                clust_rows = [[Paragraph(f"<b>{h}</b>", style_tbl_hdr) for h in clust_headers]]

                for c in clusters:
                    spi_val = c.get("spi", 1.0)
                    spi_col = "#107C41" if spi_val >= 0.98 else ("#D97706" if spi_val >= 0.85 else "#DC2626")

                    clust_rows.append([
                        Paragraph(c.get("cluster", ""), style_tbl_cell_bold),
                        Paragraph(f"{c.get('bac', 0)/1e6:.2f}M", style_tbl_cell_right),
                        Paragraph(f"{c.get('weight', 0):.1f}%", style_tbl_cell_center),
                        Paragraph(f"{c.get('planned_pct', 0):.1f}%", style_tbl_cell_right),
                        Paragraph(f"{c.get('actual_pct', 0):.1f}%", style_tbl_cell_right),
                        Paragraph(f"{c.get('variance_pct', 0):+.1f}%", style_tbl_cell_right),
                        Paragraph(f"{c.get('ev', 0)/1e6:.2f}M", style_tbl_cell_right),
                        Paragraph(f"{c.get('sv', 0)/1e6:+.2f}M", style_tbl_cell_right),
                        Paragraph(f"<font color='{spi_col}'><b>{spi_val:.2f}</b></font>", style_tbl_cell_center),
                        Paragraph(c.get("fcst_finish", "-")[:10], style_tbl_cell_center),
                    ])

                col_w = [0.8 * inch, 0.85 * inch, 0.6 * inch, 0.7 * inch, 0.7 * inch, 0.7 * inch, 0.85 * inch, 0.85 * inch, 0.6 * inch, 0.85 * inch]
                t_clust = Table(clust_rows, colWidths=col_w, repeatRows=1)
                t_clust.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(t_clust)
                story.append(Spacer(1, 14))

            # -------------------------------------------------------------
            # 5. Out-of-Sequence Risk Audit & Sign-off Block
            # -------------------------------------------------------------
            oos_ties = analytics.get("oos_ties", [])
            if oos_ties:
                story.append(Paragraph(f"<b>CRITICAL OUT-OF-SEQUENCE LOGIC AUDIT ({len(oos_ties)} TIES DETECTED)</b>", style_sec))
                story.append(Paragraph("Activities started or progressing prior to their predecessor completion violates critical path integrity:", style_sub))
                story.append(Spacer(1, 4))

                oos_headers = ["Predecessor ID", "Predecessor Name", "Tie", "Successor ID", "Successor Name", "Status", "Actual %"]
                oos_rows = [[Paragraph(f"<b>{h}</b>", style_tbl_hdr) for h in oos_headers]]

                for o in oos_ties[:12]:  # Show top 12 critical ties
                    oos_rows.append([
                        Paragraph(o.get("pred_id", ""), style_tbl_cell_bold),
                        Paragraph(o.get("pred_name", "")[:28], style_tbl_cell),
                        Paragraph(o.get("tie", "FS"), style_tbl_cell_center),
                        Paragraph(o.get("succ_id", ""), style_tbl_cell_bold),
                        Paragraph(o.get("succ_name", "")[:28], style_tbl_cell),
                        Paragraph(o.get("succ_status", ""), style_tbl_cell_center),
                        Paragraph(f"{o.get('succ_pct', 0):.1f}%", style_tbl_cell_right),
                    ])

                col_w_oos = [1.0 * inch, 1.8 * inch, 0.45 * inch, 1.0 * inch, 1.8 * inch, 0.8 * inch, 0.65 * inch]
                t_oos = Table(oos_rows, colWidths=col_w_oos, repeatRows=1)
                t_oos.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7F1D1D")),  # Dark red header
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FEF2F2")]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#FECACA")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(t_oos)
                story.append(Spacer(1, 14))

            # -------------------------------------------------------------
            # 6. Executive Sign-Off Block
            # -------------------------------------------------------------
            sig_data = [
                [
                    Paragraph("<b>PREPARED BY:</b>", style_meta_k),
                    Paragraph("<b>VERIFIED BY:</b>", style_meta_k),
                    Paragraph("<b>APPROVED BY:</b>", style_meta_k),
                ],
                [
                    Paragraph("Project Controls Engineer<br/><font color='#64748B'>Signature: _______________________</font>", style_sub),
                    Paragraph("Planning & Scheduling Manager<br/><font color='#64748B'>Signature: _______________________</font>", style_sub),
                    Paragraph("Project Director / VP Construction<br/><font color='#64748B'>Signature: _______________________</font>", style_sub),
                ]
            ]
            t_sig = Table(sig_data, colWidths=[2.5 * inch] * 3)
            t_sig.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(KeepTogether(t_sig))

            # Build Document using NumberedCanvas
            doc.build(story, canvasmaker=NumberedCanvas)

            if os.path.exists(output_pdf_path) and os.path.getsize(output_pdf_path) > 1000:
                return True, f"Pure-white executive PDF generated successfully ({os.path.getsize(output_pdf_path)/1024:.1f} KB):\n{output_pdf_path}"
            else:
                return False, "PDF file was created but appears empty."

        except Exception as e:
            import traceback
            return False, f"PDF export failed: {e}\n{traceback.format_exc()}"
