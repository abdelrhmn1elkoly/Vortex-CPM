import sys
import os

BASE_DIR = r"d:\PT Design\Programes\mangemnt-beast"
sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication
from ui.vortex_cpm_window import VortexCPMWindow
from core.project_state import get_project_state

def run_tests():
    app = QApplication.instance() or QApplication(sys.argv)
    state = get_project_state()

    print("--- Test 1: Pristine Launch State ---")
    assert not state.has_data(), "State must start with zero data!"
    win = VortexCPMWindow()
    win.show()
    QApplication.processEvents()

    assert win.hero_empty.isVisible(), "Hero empty card must be visible on clean start!"
    assert not win.live_dash.isVisible(), "Live dashboard must be hidden on clean start!"
    print("Pristine empty state verified!")

    print("--- Test 2: Ingest Baseline & Site Progress ---")
    bl_path = r"C:\Users\abdel\Downloads\HT-1 b3-Mod.xer"
    xls_path = r"C:\Users\abdel\Downloads\Copy of Hap_Town_Progress_Sheet_Final_All_Clusters(3) (1) (1) (1).xlsx"

    state.load_baseline(bl_path)
    state.load_site_excel(xls_path)
    state.apply_update_pipeline("2026-10-29")
    QApplication.processEvents()

    assert state.has_data(), "State must have data after pipeline!"
    assert not win.hero_empty.isVisible(), "Hero empty card must hide after data loaded!"
    assert win.live_dash.isVisible(), "Live dashboard must show after data loaded!"
    print(f"Live dashboard verified! BAC: {state.analytics['bac']/1e6:.2f}M | EV: {state.analytics['ev']/1e6:.2f}M")

    print("--- Test 3: Navigate all pages ---")
    for pid in ["dash", "updater", "clusters", "lookahead", "oos", "export", "settings"]:
        win.navigate_to(pid)
        QApplication.processEvents()
        print(f"   Page {pid} active: OK")

    print("--- Test 4: Reset Project to Pristine ---")
    state.reset_project()
    win.navigate_to("dash")
    QApplication.processEvents()
    assert not state.has_data(), "State must be clean after reset!"
    assert not win.hero_empty.isHidden(), "Hero empty card must be shown on dashboard after reset!"
    assert win.live_dash.isHidden(), "Live dashboard must be hidden on dashboard after reset!"
    print("Reset to pristine verified!")

    win.close()
    print("All PySide6 Vortex CPM tests passed successfully!")

if __name__ == "__main__":
    run_tests()
