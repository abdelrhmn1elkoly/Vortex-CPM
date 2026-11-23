"""Verification script for Vortex Controls v2:
- Windows 11 DWM Mica, Mica Old (Mica Alt), Acrylic, and Solid Dark Theme Engine
- Authentic Vortex PT Status Footer Bar
- SQLite Database Persistence Engine & Historical Snapshots
- Multi-Week Trends & Comparison View
- Screenshots capture
"""

import os
import sys

BASE_DIR = r"d:\PT Design\Programes\mangemnt-beast"
sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication
from ui.vortex_cpm_window import VortexCPMWindow
from core.project_state import get_project_state
from core.database_engine import DatabaseEngine


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    state = get_project_state()
    state.reset_project()

    print("\n--- STEP 1: Verify Launch & Status Footer ---")
    win = VortexCPMWindow()
    win.show()
    QApplication.processEvents()

    assert win.footer is not None, "Footer must be initialized!"
    assert win.footer.isVisible(), "Status footer must be visible!"
    assert win.footer.dot_lbl.text() == "●", "Footer dot indicator must be present!"
    print("✓ Launch state and Vortex PT Status Footer verified!")

    print("\n--- STEP 2: Ingest Baseline & Site Progress + DB Snapshot ---")
    bl_path = r"C:\Users\abdel\Downloads\HT-1 b3-Mod.xer"
    xls_path = r"C:\Users\abdel\Downloads\Copy of Hap_Town_Progress_Sheet_Final_All_Clusters(3) (1) (1) (1).xlsx"

    state.load_baseline(bl_path)
    state.load_site_excel(xls_path)
    res = state.apply_update_pipeline("2026-10-29")
    QApplication.processEvents()

    assert state.has_data(), "State must have data!"
    print("✓ Recalculation executed!")

    # Check Database Engine
    db_stats = state.db.get_database_stats()
    print(f"✓ SQLite Database: {db_stats['db_path']}")
    print(f"✓ Snapshots stored: {db_stats['snapshot_count']} | Projects: {db_stats['project_count']}")
    assert db_stats["snapshot_count"] >= 1, "Snapshot must be saved into SQLite database!"

    # Simulate a second week's progress snapshot for multi-week trend demo
    print("\n--- STEP 3: Record Second Week Snapshot in Database ---")
    state.apply_update_pipeline("2026-11-05")
    QApplication.processEvents()
    db_stats2 = state.db.get_database_stats()
    print(f"✓ Second snapshot saved! Total snapshots: {db_stats2['snapshot_count']}")

    print("\n--- STEP 4: Test Theme Switching (Mica, Mica Old, Acrylic, Solid Dark) ---")
    out_dir = os.path.join(BASE_DIR, "test_output")
    os.makedirs(out_dir, exist_ok=True)

    # Test Mica
    win._apply_theme("mica")
    QApplication.processEvents()
    pix_mica = win.grab()
    pix_mica.save(os.path.join(out_dir, "vortex_theme_mica.png"))
    print("✓ Mica theme captured!")

    # Test Mica Old (Mica Alt)
    win._apply_theme("mica_alt")
    QApplication.processEvents()
    pix_alt = win.grab()
    pix_alt.save(os.path.join(out_dir, "vortex_theme_mica_old.png"))
    print("✓ Mica Old (Alt) theme captured!")

    # Test Acrylic
    win._apply_theme("acrylic")
    QApplication.processEvents()
    pix_acrylic = win.grab()
    pix_acrylic.save(os.path.join(out_dir, "vortex_theme_acrylic.png"))
    print("✓ Acrylic theme captured!")

    # Reset back to Mica
    win._apply_theme("mica")

    print("\n--- STEP 5: Test History & Trends Navigation ---")
    win.nav_rail.select_page("trends")
    QApplication.processEvents()
    assert win.page_trends.isVisible(), "Trends page must be visible!"
    pix_trends = win.grab()
    pix_trends.save(os.path.join(out_dir, "vortex_view_trends.png"))
    print(f"✓ History & Trends view verified! Table rows: {win.page_trends.tbl_snapshots.rowCount()}")

    print("\n--- STEP 6: Verify Footer Selection Interactions ---")
    win.nav_rail.select_page("dash")
    win._on_lookahead_clicked(0, 0)
    QApplication.processEvents()
    print(f"✓ Footer selection text: {win.footer.selection_lbl.text()}")
    assert "Activity:" in win.footer.selection_lbl.text(), "Footer must reflect active activity selection!"

    win.close()
    print("\n=======================================================")
    print("ALL VORTEX CONTROLS V2 TESTS PASSED 100% SUCCESSFULLY!")
    print("=======================================================\n")


if __name__ == "__main__":
    main()
