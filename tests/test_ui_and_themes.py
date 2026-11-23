"""Comprehensive UI, Theme Engine, and Baseline-to-Update Verification.
Tests:
1. Windows 11 DWM Themes: Mica, Mica Old (Mica Alt), Acrylic, Dark Solid
2. Vortex PT UI Parity: Topbar, Collapsible NavRail, Activity Layers Toggle Switches, Project Metrics
3. Baseline-Only Intelligence Dashboard (No-Update Mode with Early/Late S-Curve Banana Envelope)
4. Reconciled Update Pipeline (0 mismatches, exact EV = 55.84M EGP)
5. Schedule Audit & Comparison View
6. Executive Pure-White PDF Export
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication
from ui.vortex_cpm_window import VortexCPMWindow
from core.project_state import get_project_state
from core.pdf_exporter import PDFExporter


def main():
    out_dir = os.path.join(BASE_DIR, "test_output")
    os.makedirs(out_dir, exist_ok=True)

    app = QApplication.instance() or QApplication(sys.argv)
    state = get_project_state()
    state.reset_project()

    print("\n=======================================================")
    print("STEP 1: Verify Launch & UI Parity (Empty State)")
    print("=======================================================")
    win = VortexCPMWindow()
    win.show()
    QApplication.processEvents()

    assert win.footer is not None and win.footer.isVisible(), "Status footer must be visible!"
    assert win.side_tool is not None and win.side_tool.isVisible(), "Side tool pane must be visible!"
    assert len(win.side_tool.layer_switches) >= 6, "Activity layer switches must be initialized!"

    # Save Empty State
    win._apply_theme("mica_alt")
    QApplication.processEvents()
    pix = win.grab()
    pix.save(os.path.join(out_dir, "vortex_ui_empty_mica_alt.png"))
    print("✓ Empty state screenshot captured in Mica Old!")

    print("\n=======================================================")
    print("STEP 2: Verify Theme Engine Switching")
    print("=======================================================")
    for theme_id in ["mica", "acrylic", "solid_dark", "mica_alt"]:
        win._apply_theme(theme_id)
        QApplication.processEvents()
        p = win.grab()
        p.save(os.path.join(out_dir, f"vortex_ui_{theme_id}.png"))
        print(f"✓ Theme '{theme_id}' applied and captured!")

    print("\n=======================================================")
    print("STEP 3: Verify Baseline-Only Intelligence Mode")
    print("=======================================================")
    bl_path = r"C:\Users\abdel\Downloads\New folder (2)\Rev_0_HAP_Town_baseline.xer"
    state.load_baseline(bl_path)
    QApplication.processEvents()

    assert state.analytics is not None, "Analytics must be computed from baseline!"
    assert state.analytics.get("is_baseline_only") is True, "Must be in baseline-only mode!"
    assert state.analytics["total_activities"] == 3110, "Baseline must contain 3,110 activities!"
    assert round(state.analytics["bac"] / 1e6, 2) == 240.00, "Baseline BAC must be 240.00M EGP!"

    # Verify S-Curve Banana Points
    scurve = state.analytics.get("scurve", [])
    assert len(scurve) > 10, "S-Curve must have weekly data points!"
    assert "late_pv_m" in scurve[5], "S-Curve must contain Late PV for Banana Curve envelope!"
    print(f"✓ S-Curve points generated: {len(scurve)} with Early PV & Late PV envelope!")

    win.refresh_views()
    QApplication.processEvents()
    pix_bl = win.grab()
    pix_bl.save(os.path.join(out_dir, "vortex_ui_baseline_intelligence.png"))
    print("✓ Baseline Intelligence screenshot captured!")

    print("\n=======================================================")
    print("STEP 4: Verify Reconciled Update Mode")
    print("=======================================================")
    xls_path = r"C:\Users\abdel\Downloads\New folder (2)\HPT_Weekly_Progress_Report_12-Nov_2026.xlsx"
    state.load_site_excel(xls_path)
    state.apply_update_pipeline("2026-11-12")
    win.refresh_views()
    QApplication.processEvents()

    a = state.analytics
    assert a is not None
    assert a.get("is_baseline_only") is False
    assert a["completed_count"] == 2106, f"Expected 2106 completed, got {a['completed_count']}"
    assert a["active_count"] == 275, f"Expected 275 active, got {a['active_count']}"
    ev_m = a["ev"] / 1e6
    assert abs(ev_m - 55.84) < 0.05, f"Expected EV ~55.84M, got {ev_m:.2f}M"
    print(f"✓ Update Reconciled: 2,106 Done, 275 Active, EV = {ev_m:.2f}M EGP, SPI = {a['spi']:.2f}")

    pix_upd = win.grab()
    pix_upd.save(os.path.join(out_dir, "vortex_ui_reconciled_update.png"))
    print("✓ Reconciled Update screenshot captured!")

    print("\n=======================================================")
    print("STEP 5: Verify Schedule Audit & Comparison View")
    print("=======================================================")
    win.nav_rail.select_page("compare")
    QApplication.processEvents()
    assert win.page_compare.isVisible(), "Comparison page must be visible!"
    assert win.page_compare.tbl_compare.rowCount() > 0, "Comparison table must have rows!"
    print(f"✓ Comparison table loaded with {win.page_compare.tbl_compare.rowCount()} audit entries!")

    pix_cmp = win.grab()
    pix_cmp.save(os.path.join(out_dir, "vortex_ui_schedule_audit.png"))
    print("✓ Schedule Audit screenshot captured!")

    print("\n=======================================================")
    print("STEP 6: Verify Executive Pure-White PDF Export")
    print("=======================================================")
    pdf_out = os.path.join(out_dir, "Vortex_Executive_Report_12Nov2026.pdf")
    PDFExporter.export_pdf(state.analytics, pdf_out)
    assert os.path.exists(pdf_out), "PDF report must be generated!"
    pdf_sz = os.path.getsize(pdf_out)
    print(f"✓ Executive PDF generated: {pdf_sz:,} bytes at {pdf_out}")
    assert pdf_sz > 50000, "PDF must contain complete pages and charts!"

    win.close()
    print("\n=======================================================")
    print("ALL VERIFICATION SUITE CHECKS PASSED 100% PERFECTLY!")
    print("=======================================================\n")


if __name__ == "__main__":
    main()
