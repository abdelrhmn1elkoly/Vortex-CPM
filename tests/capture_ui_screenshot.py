"""Captures high-DPI screenshots of Vortex Controls in WinUI 3 Fluent Dark mode."""

import os
import sys

BASE_DIR = r"d:\PT Design\Programes\mangemnt-beast"
sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSize
from ui.vortex_cpm_window import VortexCPMWindow
from core.project_state import get_project_state


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    state = get_project_state()

    bl_path = r"C:\Users\abdel\Downloads\New folder (2)\Rev_0_HAP_Town_baseline_UPDATED_2026-11-19.xer"
    xls_path = r"C:\Users\abdel\Downloads\New folder (2)\HPT_Weekly_Progress_Report_12-Nov_2026.xlsx"

    out_dir = os.path.join(BASE_DIR, "test_output")
    os.makedirs(out_dir, exist_ok=True)

    # 1. Capture Pristine Empty Launch State (matching Vortex PT Hero Workspace)
    state.reset_project()
    win = VortexCPMWindow()
    win.resize(1500, 920)
    win.show()
    QApplication.processEvents()
    win.grab().save(os.path.join(out_dir, "vortex_controls_empty.png"))
    print("Saved empty launch screenshot!")

    # 2. Ingest Schedule & Site Progress (HAP Town Update 12-Nov-2026)
    upd_path = r"C:\Users\abdel\Downloads\New folder (2)\Rev_0_HAP_Town_UPD_12_Nov_2026_R2.xer"
    state.load_baseline(upd_path)
    win.refresh_views()
    QApplication.processEvents()

    # Select an activity in the inspector
    if state.analytics and state.analytics.get("activities"):
        win.inspector.inspect_activity(state.analytics["activities"][0])
    QApplication.processEvents()

    # 3. Expanded Navigation Rail screenshot
    win.grab().save(os.path.join(out_dir, "vortex_controls_expanded.png"))
    print("Saved expanded UI screenshot!")

    # 4. Compact Navigation Rail screenshot
    win.nav_rail.toggle()
    QApplication.processEvents()
    win.grab().save(os.path.join(out_dir, "vortex_controls_compact.png"))
    print("Saved compact UI screenshot!")

    win.close()


if __name__ == "__main__":
    main()
