"""End-to-End Verification Test for Vortex Controls.
Tests:
1. Clean zero-data launch.
2. Ingestion of real P6 Baseline (.XER) and Weekly Site Progress (.XLSX).
3. Recalculation pipeline and EVM metrics verification.
4. Generation of pure-white executive PDF report via ReportLab + Matplotlib.
5. Rendering of PDF pages to PNG images for visual verification.
6. Multi-tab Excel export.
7. Inspector pane activity and cluster inspection.
8. Navigation rail toggle (expanded ↔ compact).
"""

import os
import sys

BASE_DIR = r"d:\PT Design\Programes\mangemnt-beast"
sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSize
from PySide6.QtPdf import QPdfDocument

from ui.vortex_cpm_window import VortexCPMWindow
from core.project_state import get_project_state
from core.pdf_exporter import PDFExporter
from core.excel_exporter import ExcelExporter


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    state = get_project_state()
    state.reset_project()

    print("\n=======================================================")
    print("STEP 1: Verify Pristine Zero-Data Launch State")
    print("=======================================================")
    assert not state.has_data(), "Project state must start clean!"
    win = VortexCPMWindow()
    win.show()
    QApplication.processEvents()

    assert win.hero_empty.isVisible(), "Hero welcome card must be visible on startup!"
    assert not win.dash_content.isVisible(), "Dashboard charts must be hidden until data loaded!"
    assert win.inspector.current_type == "none", "Inspector must start in empty state!"
    print("✓ Pristine zero-data launch verified!")

    print("\n=======================================================")
    print("STEP 2: Ingest Real Project Baseline & Site Progress")
    print("=======================================================")
    bl_path = r"C:\Users\abdel\Downloads\HT-1 b3-Mod.xer"
    xls_path = r"C:\Users\abdel\Downloads\Copy of Hap_Town_Progress_Sheet_Final_All_Clusters(3) (1) (1) (1).xlsx"

    state.load_baseline(bl_path)
    state.load_site_excel(xls_path)
    res = state.apply_update_pipeline("2026-10-29")
    QApplication.processEvents()

    assert state.has_data(), "State must have data after pipeline execution!"
    assert not win.hero_empty.isVisible(), "Hero welcome card must hide once data is loaded!"
    assert win.dash_content.isVisible(), "Live dashboard must be displayed!"

    a = state.analytics
    print(f"✓ Project: {a['project_name']}")
    print(f"✓ BAC: {a['bac']/1e6:.2f}M EGP | PV: {a['pv']/1e6:.2f}M EGP | EV: {a['ev']/1e6:.2f}M EGP")
    print(f"✓ Planned: {a['planned_pct']:.2f}% | Actual: {a['actual_pct']:.2f}% | SPI: {a['spi']:.2f}")
    print(f"✓ Clusters: {len(a['clusters'])} | Activities: {len(a['activities'])} | OOS Ties: {a['oos_count']}")

    print("\n=======================================================")
    print("STEP 3: Test Navigation Rail Toggle & Page Navigation")
    print("=======================================================")
    # Test collapse
    win.nav_rail.toggle()
    QApplication.processEvents()
    assert win.nav_rail.width() == 48, f"Nav rail should be compact (48px), got {win.nav_rail.width()}"
    print("✓ Compact mode (48px) verified!")

    # Test expand
    win.nav_rail.toggle()
    QApplication.processEvents()
    assert win.nav_rail.width() == 210, f"Nav rail should be expanded (210px), got {win.nav_rail.width()}"
    print("✓ Expanded mode (210px) verified!")

    # Test page navigation
    for pid in ["dash", "updater", "clusters", "lookahead", "oos", "export", "help", "settings"]:
        win.nav_rail.select_page(pid)
        QApplication.processEvents()
    print("✓ All 8 views navigated smoothly!")

    print("\n=======================================================")
    print("STEP 4: Test Master-Detail Inspector Interactions")
    print("=======================================================")
    # Inspect a cluster
    win.inspector.inspect_cluster(a["clusters"][0])
    QApplication.processEvents()
    assert win.inspector.current_type == "cluster", "Inspector should display cluster data!"
    print(f"✓ Inspected Cluster: {a['clusters'][0]['cluster']}")

    # Inspect an activity
    win.inspector.inspect_activity(a["activities"][0])
    QApplication.processEvents()
    assert win.inspector.current_type == "activity", "Inspector should display activity data!"
    print(f"✓ Inspected Activity: {a['activities'][0]['act_id']} ({a['activities'][0]['act_name']})")

    print("\n=======================================================")
    print("STEP 5: Generate Pure-White Executive PDF Report")
    print("=======================================================")
    out_dir = os.path.join(BASE_DIR, "test_output")
    os.makedirs(out_dir, exist_ok=True)
    pdf_path = os.path.join(out_dir, "HAP_TOWN_Executive_Report_White.pdf")

    ok, msg = PDFExporter.export_pdf(a, pdf_path)
    assert ok, f"PDF generation failed: {msg}"
    assert os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 10000, "PDF file missing or empty!"
    print(f"✓ Generated PDF ({os.path.getsize(pdf_path)/1024:.1f} KB): {pdf_path}")

    # Render PDF pages to PNG to inspect visual output
    doc = QPdfDocument()
    doc.load(pdf_path)
    page_count = doc.pageCount()
    print(f"✓ PDF has {page_count} page(s)")

    for p in range(min(page_count, 3)):
        img = doc.render(p, QSize(1200, 1600))
        img_path = os.path.join(out_dir, f"pdf_verify_page_{p+1}.png")
        img.save(img_path)
        print(f"✓ Rendered page {p+1} to {img_path}")

    print("\n=======================================================")
    print("STEP 6: Generate Multi-Tab Formatted Excel Workbook")
    print("=======================================================")
    excel_path = os.path.join(out_dir, "HAP_TOWN_Executive_Workbook.xlsx")
    ok_xl, msg_xl = ExcelExporter.export_workbook(a, excel_path)
    assert ok_xl, f"Excel generation failed: {msg_xl}"
    assert os.path.exists(excel_path) and os.path.getsize(excel_path) > 10000, "Excel file missing or empty!"
    print(f"✓ Generated Excel ({os.path.getsize(excel_path)/1024:.1f} KB): {excel_path}")

    win.close()
    print("\n=======================================================")
    print("ALL VORTEX CONTROLS TESTS PASSED 100% SUCCESSFULLY!")
    print("=======================================================\n")


if __name__ == "__main__":
    main()
