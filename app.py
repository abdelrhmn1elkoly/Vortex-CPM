"""Vortex Controls — Construction Project Management & Critical Path Method.
Main desktop launcher and application entry point.
Launches cleanly with zero pre-loaded project data in authentic Windows 11 Fluent Dark mode.
"""

from __future__ import annotations
import os
import sys
import traceback

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication
from ui.vortex_cpm_window import VortexCPMWindow


def main():
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Vortex Controls")
        app.setOrganizationName("Vortex Engineering")

        # Launch main window cleanly with zero pre-loaded data
        win = VortexCPMWindow()
        win.show()

        sys.exit(app.exec())

    except Exception as e:
        err = traceback.format_exc()
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                f"Error launching Vortex Controls:\n\n{err}",
                "Vortex Controls Error",
                0x10
            )
        except Exception:
            print(err)


if __name__ == "__main__":
    main()
