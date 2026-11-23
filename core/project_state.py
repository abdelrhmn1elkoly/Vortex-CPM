"""Central Project State Management for Vortex CPM.
Coordinates loaded baseline XER files, site progress Excel sheets,
computed analytics, and triggers reactive UI updates across views.
Starts completely empty with zero pre-loaded data.
"""

from __future__ import annotations
import os
from typing import Dict, Any, List, Optional, Callable
from .xer_engine import XEREngine
from .excel_importer import ExcelProgressImporter
from .analytics_engine import AnalyticsEngine
from .database_engine import DatabaseEngine


class ProjectState:
    """Singleton-style reactive state manager for the active project controls session."""

    _instance: Optional[ProjectState] = None

    def __new__(cls) -> ProjectState:
        if cls._instance is None:
            cls._instance = super(ProjectState, cls).__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        # Starts 100% clean with NO preloaded files or data
        self.baseline_path: Optional[str] = None
        self.site_excel_path: Optional[str] = None
        self.updated_xer_path: Optional[str] = None
        self.data_date: str = "2026-10-29"
        self.project_title: str = "Vortex CPM - Project Controls Suite"
        self.contractor: str = ""
        self.engineer: str = ""
        self.client: str = ""
        self.currency: str = "EGP"

        self.xer_engine: Optional[XEREngine] = None
        self.progress_map: Dict[str, Dict[str, Any]] = {}
        self.excel_summary: Dict[str, Any] = {}
        self.analytics: Optional[Dict[str, Any]] = None
        self.db = DatabaseEngine()

        self._listeners: List[Callable[[], None]] = []

    def has_data(self) -> bool:
        """Returns True if a baseline schedule has been loaded and analyzed."""
        return self.analytics is not None and self.xer_engine is not None

    def reset_project(self):
        """Resets the state back to a pristine empty state."""
        self.baseline_path = None
        self.site_excel_path = None
        self.updated_xer_path = None
        self.xer_engine = None
        self.progress_map = {}
        self.excel_summary = {}
        self.analytics = None
        self.notify_listeners()

    def register_listener(self, callback: Callable[[], None]):
        """Registers a callback to be invoked whenever project state changes."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unregister_listener(self, callback: Callable[[], None]):
        """Removes a previously registered callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notify_listeners(self):
        """Notifies all registered views that the project state has updated."""
        for cb in self._listeners:
            try:
                cb()
            except Exception as e:
                print(f"[ProjectState] Listener error: {e}")

    def load_baseline(self, xer_path: str) -> Dict[str, Any]:
        """Loads and parses a baseline P6 .XER file."""
        if not os.path.exists(xer_path):
            raise FileNotFoundError(f"Baseline file does not exist: {xer_path}")

        self.baseline_path = xer_path
        self.xer_engine = XEREngine(xer_path)
        summary = self.xer_engine.get_project_summary()

        if summary.get("project_name"):
            self.project_title = summary["project_name"]
        if summary.get("data_date"):
            self.data_date = summary["data_date"]

        # Compute initial analytics from baseline
        self.recalculate_analytics()
        self.notify_listeners()
        return summary

    def load_site_excel(self, excel_path: str) -> Dict[str, Any]:
        """Loads and parses a weekly site progress Excel workbook."""
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Excel file does not exist: {excel_path}")

        self.site_excel_path = excel_path
        self.progress_map, self.excel_summary = ExcelProgressImporter.parse_file(
            excel_path, data_date=self.data_date
        )
        self.notify_listeners()
        return self.excel_summary

    def load_site_csv_text(self, csv_text: str) -> Dict[str, Any]:
        """Loads and parses pasted weekly site progress CSV / TSV text."""
        self.progress_map, self.excel_summary = ExcelProgressImporter.parse_csv_text(
            csv_text, data_date=self.data_date
        )
        self.site_excel_path = "Pasted_Progress_CSV"
        self.notify_listeners()
        return self.excel_summary

    def apply_update_pipeline(self, data_date: str) -> Dict[str, Any]:
        """Applies loaded progress map to baseline XER and recalculates all analytics."""
        if not self.xer_engine:
            raise ValueError("No baseline XER loaded. Please load a baseline first.")

        self.data_date = data_date

        update_stats = {}
        if self.progress_map:
            update_stats = self.xer_engine.apply_progress_updates(self.progress_map, data_date)

        # Recalculate full analytics
        self.recalculate_analytics()

        # Save to SQLite Database as an immutable weekly snapshot
        if self.analytics:
            try:
                self.db.save_analytics_snapshot(self.analytics, notes="Schedule Recalculation")
            except Exception as e:
                print(f"[ProjectState] DB save error: {e}")

        # Prepare default updated XER output path
        if self.baseline_path:
            base_dir = os.path.dirname(self.baseline_path)
            base_name = os.path.splitext(os.path.basename(self.baseline_path))[0]
            self.updated_xer_path = os.path.join(base_dir, f"{base_name}_UPDATED_{data_date}.xer")
            self.xer_engine.export_xer(self.updated_xer_path)

        self.notify_listeners()
        return {
            "update_stats": update_stats,
            "analytics": self.analytics,
            "updated_xer_path": self.updated_xer_path
        }

    def run_update(self, data_date: str) -> bool:
        """Executes the update pipeline and returns True on success."""
        try:
            res = self.apply_update_pipeline(data_date)
            return bool(res and self.analytics)
        except Exception as e:
            print(f"[ProjectState] run_update error: {e}")
            return False

    def export_updated_xer(self, output_path: str) -> tuple[bool, str]:
        """Serializes current in-memory schedule to a standard Primavera P6 .XER file."""
        if not self.xer_engine:
            return False, "No schedule loaded."
        try:
            self.xer_engine.export_xer(output_path)
            return True, f"Updated P6 schedule written to:\n{output_path}"
        except Exception as e:
            return False, str(e)

    def recalculate_analytics(self):
        """Recomputes analytics based on current in-memory tables."""
        if not self.xer_engine or not self.xer_engine.tables:
            return

        self.analytics = AnalyticsEngine.analyze(
            tables=self.xer_engine.tables,
            data_date_str=self.data_date
        )
        if self.baseline_path:
            self.analytics["baseline_name"] = os.path.basename(self.baseline_path)
        self.analytics["project_name"] = self.project_title


def get_project_state() -> ProjectState:
    """Convenience getter for the global ProjectState singleton."""
    return ProjectState()
