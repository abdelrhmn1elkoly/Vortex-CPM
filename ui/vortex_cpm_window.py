"""Vortex Controls — Construction Project Management & Critical Path Method.
Main desktop application window built with PySide6 and authentic Windows 11 WinUI 3 Fluent Design.
Features:
- Live Windows 11 DWM Backdrop Switching (Mica, Mica Old / Mica Alt, Acrylic, Dark Solid)
- Authentic Vortex PT Status Footer Bar with live status dot, active selection tag, and real-time metrics
- Embedded SQLite Database Persistence Engine with multi-week snapshot tracking
- Historical Trends & Progress Comparison Dashboard
- Collapsible Navigation Rail (48px compact ↔ 210px expanded) with active vertical accent indicator
- Right-Docked Master-Detail Inspector Pane (Live inspection of Critical Path, Float, and Logic Ties)
- Direct One-Click Pure-White Executive PDF Report Generator
- Multi-Tab Formatted Excel Exporter & Round-Trip P6 XER Serializer
- Pristine Zero-Data Launch with Drag-and-Drop Ingestion Support
"""

from __future__ import annotations
import os
import sys
import ctypes
from datetime import datetime
from typing import Optional, Dict, Any, List

from PySide6.QtCore import Qt, QDate, QUrl, Signal, QPoint
from PySide6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush, QDragEnterEvent, QDropEvent
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QDateEdit, QFrame, QStackedWidget, QLineEdit, QComboBox,
    QMessageBox, QTextEdit, QScrollArea, QSizePolicy, QToolTip, QDialog
)

from core.project_state import get_project_state
from core.excel_exporter import ExcelExporter
from core.pdf_exporter import PDFExporter
from .theme import apply_dwm_backdrop, generate_theme_qss, THEME_PALETTES
from .custom_icons import get_fluent_icon, ensure_icon_files
from .components.nav_rail import NavRail
from .components.side_tool_pane import SideToolPane
from .components.inspector_pane import InspectorPane
from .components.status_footer import StatusFooter
from .views.trends_view import TrendsView
from .views.comparison_view import ScheduleComparisonView


# =========================================================================
# High-DPI Vector S-Curve Widget with Crosshair & Tooltips
# =========================================================================
class ScurveWidget(QWidget):
    """High-DPI vector drawing widget for cumulative Planned Value vs Earned Value with hover crosshair."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.points: List[Dict[str, Any]] = []
        self.data_date: str = ""
        self.setMinimumHeight(190)
        self.setMouseTracking(True)
        self.hover_idx: Optional[int] = None

    def set_data(self, points: List[Dict[str, Any]], data_date: str = ""):
        self.points = points
        self.data_date = data_date
        self.update()

    def mouseMoveEvent(self, event):
        if not self.points or len(self.points) < 2:
            return
        w = self.width()
        pad_l, pad_r = 50, 20
        plot_w = w - pad_l - pad_r
        x = event.position().x()

        if pad_l <= x <= w - pad_r:
            ratio = (x - pad_l) / plot_w
            n = len(self.points)
            idx = min(n - 1, max(0, int(round(ratio * (n - 1)))))
            if idx != self.hover_idx:
                self.hover_idx = idx
                pt = self.points[idx]
                dt = pt.get("date", "")[:10]
                pv = pt.get("pv_m", 0.0)
                late_pv = pt.get("late_pv_m", pv)
                ev = pt.get("ev_m")
                ev_str = f"{ev:.2f}M EGP" if ev is not None else "Not Recorded"
                tip = f"Date: {dt}\nPlanned Early (PV): {pv:.2f}M EGP\nPlanned Late (PV): {late_pv:.2f}M EGP\nEarned (EV): {ev_str}"
                QToolTip.showText(event.globalPosition().toPoint(), tip, self)
                self.update()
        else:
            if self.hover_idx is not None:
                self.hover_idx = None
                self.update()

    def leaveEvent(self, event):
        self.hover_idx = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        if not self.points:
            painter.setPen(QColor("#64748B"))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(self.rect(), Qt.AlignCenter, "No schedule data loaded.\nImport a baseline XER to render S-Curve.")
            return

        pad_l, pad_r = 50, 20
        pad_t, pad_b = 25, 25
        plot_w = w - pad_l - pad_r
        plot_h = h - pad_t - pad_b

        max_val = max([p.get("pv_m", 0) for p in self.points] + [p.get("ev_m", 0) or 0 for p in self.points] + [10.0])
        max_val = max(10.0, max_val * 1.05)

        # Draw gridlines
        grid_pen = QPen(QColor("#383838"), 1, Qt.DashLine)
        text_pen = QColor("#9E9E9E")
        font = QFont("Segoe UI", 8)
        painter.setFont(font)

        for i in range(5):
            ratio = i / 4.0
            y = pad_t + plot_h * (1.0 - ratio)
            val = max_val * ratio
            painter.setPen(grid_pen)
            painter.drawLine(pad_l, y, w - pad_r, y)
            painter.setPen(text_pen)
            painter.drawText(pad_l - 45, y + 4, f"{val:.0f}M")

        n = len(self.points)
        if n < 2:
            return

        def get_pos(val, idx):
            x = pad_l + (idx / (n - 1)) * plot_w
            y = pad_t + plot_h * (1.0 - (val / max_val))
            return x, y

        # Check if late PV is present (Banana Curve)
        has_late = any("late_pv_m" in p for p in self.points)

        # 0. Fill Banana Curve envelope between Early PV and Late PV
        if has_late:
            from PySide6.QtGui import QPolygonF
            poly = QPolygonF()
            for idx in range(n):
                x, y = get_pos(self.points[idx].get("pv_m", 0), idx)
                poly.append(QPoint(int(x), int(y)))
            for idx in reversed(range(n)):
                x, y = get_pos(self.points[idx].get("late_pv_m", self.points[idx].get("pv_m", 0)), idx)
                poly.append(QPoint(int(x), int(y)))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(96, 205, 255, 35))
            painter.drawPolygon(poly)

        # 1. Planned Early Value Curve (WinUI Cyan #60CDFF)
        painter.setPen(QPen(QColor("#60CDFF"), 2.5))
        for idx in range(n - 1):
            x1, y1 = get_pos(self.points[idx].get("pv_m", 0), idx)
            x2, y2 = get_pos(self.points[idx + 1].get("pv_m", 0), idx + 1)
            painter.drawLine(x1, y1, x2, y2)

        # 2. Planned Late Value Curve (Amber #F59E0B dashed)
        if has_late:
            painter.setPen(QPen(QColor("#F59E0B"), 1.8, Qt.DashLine))
            for idx in range(n - 1):
                x1, y1 = get_pos(self.points[idx].get("late_pv_m", self.points[idx].get("pv_m", 0)), idx)
                x2, y2 = get_pos(self.points[idx + 1].get("late_pv_m", self.points[idx + 1].get("pv_m", 0)), idx + 1)
                painter.drawLine(x1, y1, x2, y2)

        # 3. Earned Value Curve (Emerald #10B981)
        ev_pts = [(idx, p.get("ev_m")) for idx, p in enumerate(self.points) if p.get("ev_m") is not None]
        if ev_pts:
            painter.setPen(QPen(QColor("#10B981"), 3))
            for i in range(len(ev_pts) - 1):
                idx1, ev1 = ev_pts[i]
                idx2, ev2 = ev_pts[i + 1]
                x1, y1 = get_pos(ev1, idx1)
                x2, y2 = get_pos(ev2, idx2)
                painter.drawLine(x1, y1, x2, y2)

            # Draw EV dots
            painter.setBrush(QColor("#10B981"))
            painter.setPen(QColor("#202020"))
            for idx, ev in ev_pts:
                x, y = get_pos(ev, idx)
                painter.drawEllipse(x - 3, y - 3, 6, 6)

        # Hover crosshair
        if self.hover_idx is not None and 0 <= self.hover_idx < n:
            hx = pad_l + (self.hover_idx / (n - 1)) * plot_w
            painter.setPen(QPen(QColor("#60CDFF"), 1, Qt.DotLine))
            painter.drawLine(hx, pad_t, hx, h - pad_b)

        # Legend
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#60CDFF"))
        painter.drawRect(w - 290, 8, 12, 5)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(w - 273, 14, "Early PV")

        painter.setBrush(QColor("#F59E0B"))
        painter.drawRect(w - 200, 8, 12, 5)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(w - 183, 14, "Late PV")

        painter.setBrush(QColor("#10B981"))
        painter.drawRect(w - 110, 8, 12, 5)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(w - 93, 14, "Earned EV")


# =========================================================================
# Modal: Paste Progress CSV / TSV Dialog
# =========================================================================
class PasteProgressDialog(QDialog):
    """WinUI 3 styled modal dialog for pasting weekly site progress CSV / TSV text."""

    def __init__(self, parent=None, default_date: str = "2026-11-12"):
        super().__init__(parent)
        self.setWindowTitle("Paste Weekly Site Progress (CSV / TSV)")
        self.resize(720, 520)
        self.setMinimumSize(550, 400)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        lbl_head = QLabel("Paste Weekly Site Progress Records")
        lbl_head.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")
        lay.addWidget(lbl_head)

        lbl_sub = QLabel("Paste copied rows directly from Excel or CSV text (columns: Activity ID, Activity Name, % Complete, Actual Start, Actual Finish):")
        lbl_sub.setStyleSheet("font-size: 11.5px; color: #94A3B8;")
        lbl_sub.setWordWrap(True)
        lay.addWidget(lbl_sub)

        # Date Row
        row_date = QHBoxLayout()
        lbl_d = QLabel("Data Date:")
        lbl_d.setStyleSheet("color: #E2E8F0; font-size: 12px; font-weight: 600;")
        row_date.addWidget(lbl_d)

        self.txt_date = QLineEdit(default_date)
        self.txt_date.setObjectName("FluentSearch")
        self.txt_date.setFixedWidth(140)
        row_date.addWidget(self.txt_date)
        row_date.addStretch()
        lay.addLayout(row_date)

        # Text Edit
        self.txt_content = QTextEdit()
        self.txt_content.setObjectName("FluentTextEdit")
        self.txt_content.setPlaceholderText("HT.CO.Tie.C16.070\tTie Beams\t80%\t2026-10-15\nHT.CO.Civil.C18.030\tPlain Concrete\t90%\t2026-10-20\n...")
        self.txt_content.setStyleSheet("font-family: 'Consolas', 'Segoe UI Mono', monospace; font-size: 11px; background: #18191B; color: #E2E8F0; border: 1px solid #36383D; border-radius: 6px; padding: 8px;")
        lay.addWidget(self.txt_content, 1)

        # Action Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("ActionBtn")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_apply = QPushButton("Apply Progress Updates")
        btn_apply.setObjectName("PrimaryBtn")
        btn_apply.setCursor(Qt.PointingHandCursor)
        btn_apply.clicked.connect(self.accept)
        btn_box.addWidget(btn_apply)

        lay.addLayout(btn_box)

    def get_data(self) -> tuple[str, str]:
        return self.txt_content.toPlainText().strip(), self.txt_date.text().strip()


# =========================================================================
# Main Window: Vortex Controls
# =========================================================================
class VortexCPMWindow(QMainWindow):
    """Main Application Window for Vortex Controls."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vortex Controls — Construction Project Management & Critical Path Method")
        self.resize(1440, 900)
        self.setMinimumSize(1100, 700)

        # Ensure vector assets exist
        ensure_icon_files()

        self.current_theme = "mica"
        self.setStyleSheet(generate_theme_qss(self.current_theme))

        self.state = get_project_state()
        self.state.register_listener(self.on_state_changed)

        # Enable Drag & Drop
        self.setAcceptDrops(True)

        self._init_ui()
        self._apply_theme(self.current_theme)
        self.refresh_views()

    def _apply_theme(self, theme_id: str):
        """Applies Windows 11 DWM backdrop material and updates QSS styling."""
        self.current_theme = theme_id
        if sys.platform.startswith("win"):
            try:
                apply_dwm_backdrop(self, theme_id)
            except Exception:
                pass
        self.setStyleSheet(generate_theme_qss(theme_id))

    def _on_theme_changed(self, idx: int):
        theme_id = self.cb_theme.currentData()
        self._apply_theme(theme_id)
        pal = THEME_PALETTES.get(theme_id, {})
        self.footer.set_status(f"Active Theme: {pal.get('name', 'Mica')} ({pal.get('description', '')})", "working")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                ext = os.path.splitext(url.toLocalFile())[1].lower()
                if ext in [".xer", ".xlsx", ".xls"]:
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            ext = os.path.splitext(filepath)[1].lower()
            if ext == ".xer":
                self.load_baseline_path(filepath)
            elif ext in [".xlsx", ".xls"]:
                self.load_excel_path(filepath)
        event.acceptProposedAction()

    def _init_ui(self):
        root = QWidget()
        root.setObjectName("MainRoot")
        self.setCentralWidget(root)

        # Main Vertical Layout: Body on top, StatusFooter at the bottom
        root_vbox = QVBoxLayout(root)
        root_vbox.setContentsMargins(0, 0, 0, 0)
        root_vbox.setSpacing(0)

        # Body Layout: Nav Rail + Center Area + Right Inspector Pane
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # 1. Left Navigation Rail (Collapsible WinUI 3 Rail)
        self.nav_rail = NavRail(self)
        self.nav_rail.page_changed.connect(self.navigate_to)
        body_layout.addWidget(self.nav_rail)

        # 2. Secondary Sidebar: Layers & Project Metrics (Matching Vortex PT)
        self.side_tool = SideToolPane(self)
        self.side_tool.change_project_requested.connect(self.select_baseline_file)
        self.side_tool.layer_toggled.connect(self._on_layer_filter_toggled)
        body_layout.addWidget(self.side_tool)

        # 3. Center Content Area (Topbar + Stacked Pages)
        center_area = QWidget()
        c_layout = QVBoxLayout(center_area)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)

        # Topbar (Matching Vortex PT Action Bar & FluentDL Search)
        topbar = QFrame()
        topbar.setObjectName("Topbar")
        topbar.setFixedHeight(50)
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(14, 0, 14, 0)
        tb_layout.setSpacing(8)

        # Quick Action Buttons (Matching Vortex PT toolbar)
        self.btn_top_xer = QPushButton(" Open")
        self.btn_top_xer.setObjectName("ActionBtn")
        self.btn_top_xer.setIcon(get_fluent_icon("folder", color="#FFFFFF", size=14))
        self.btn_top_xer.setToolTip("Open Primavera P6 baseline schedule (.xer)")
        self.btn_top_xer.clicked.connect(self.select_baseline_file)
        tb_layout.addWidget(self.btn_top_xer)

        self.btn_top_xls = QPushButton(" Update")
        self.btn_top_xls.setObjectName("ActionBtn")
        self.btn_top_xls.setIcon(get_fluent_icon("excel", color="#FFFFFF", size=14))
        self.btn_top_xls.setToolTip("Import weekly site progress update (.xlsx)")
        self.btn_top_xls.clicked.connect(self.select_excel_file)
        tb_layout.addWidget(self.btn_top_xls)

        self.btn_top_paste = QPushButton(" Paste")
        self.btn_top_paste.setObjectName("ActionBtn")
        self.btn_top_paste.setIcon(get_fluent_icon("updater", color="#00E5FF", size=14))
        self.btn_top_paste.setToolTip("Paste weekly site progress CSV or copied Excel cells directly")
        self.btn_top_paste.clicked.connect(self.open_paste_progress_dialog)
        tb_layout.addWidget(self.btn_top_paste)

        self.btn_top_cpm = QPushButton(" Recalc")
        self.btn_top_cpm.setObjectName("ActionBtn")
        self.btn_top_cpm.setIcon(get_fluent_icon("updater", color="#00F2FE", size=14))
        self.btn_top_cpm.setToolTip("Recalculate Critical Path & Forecast Dates (F9)")
        self.btn_top_cpm.clicked.connect(self.run_cpm_update)
        tb_layout.addWidget(self.btn_top_cpm)

        self.btn_top_pdf = QPushButton(" PDF")
        self.btn_top_pdf.setObjectName("PrimaryBtn")
        self.btn_top_pdf.setIcon(get_fluent_icon("pdf", color="#0F172A", size=14))
        self.btn_top_pdf.setToolTip("Export Publication-Quality Pure-White Executive PDF")
        self.btn_top_pdf.clicked.connect(self.quick_export_pdf)
        tb_layout.addWidget(self.btn_top_pdf)

        tb_layout.addStretch(1)

        # Search Bar (Pill input matching FluentDL & Vortex PT)
        self.top_search_input = QLineEdit()
        self.top_search_input.setPlaceholderText("Search Activity...")
        self.top_search_input.setObjectName("FluentSearch")
        self.top_search_input.setFixedWidth(170)
        self.top_search_input.textChanged.connect(self._on_search_query_changed)
        tb_layout.addWidget(self.top_search_input)

        # Theme Selector ComboBox (Mica, Mica Old, Acrylic, Dark Solid)
        self.cb_theme = QComboBox()
        self.cb_theme.addItem("🎨 Mica Old", "mica_alt")
        self.cb_theme.addItem("🎨 Mica", "mica")
        self.cb_theme.addItem("🎨 Acrylic", "acrylic")
        self.cb_theme.addItem("🎨 Solid Dark", "solid_dark")
        self.cb_theme.setFixedWidth(120)
        self.cb_theme.setToolTip("Switch Windows 11 DWM Material & Theme")
        self.cb_theme.currentIndexChanged.connect(self._on_theme_changed)
        tb_layout.addWidget(self.cb_theme)

        self.btn_top_inspector = QPushButton()
        self.btn_top_inspector.setObjectName("ActionBtn")
        self.btn_top_inspector.setIcon(get_fluent_icon("inspector", color="#60CDFF", size=16))
        self.btn_top_inspector.setToolTip("Toggle Right Activity Properties Pane")
        self.btn_top_inspector.setFixedWidth(34)
        self.btn_top_inspector.clicked.connect(self.toggle_inspector)
        tb_layout.addWidget(self.btn_top_inspector)

        c_layout.addWidget(topbar)

        # Title Sub-header for Project Status
        self.lbl_top_title = QLabel("Vortex Controls — Construction Project Controls")
        self.lbl_top_title.setObjectName("TopbarTitle")
        self.lbl_top_title.setVisible(False)
        self.lbl_top_sub = QLabel("Import your baseline XER and weekly progress Excel to initialize dashboard")
        self.lbl_top_sub.setObjectName("TopbarSub")
        self.lbl_top_sub.setVisible(False)

        # Stacked Pages
        self.stack = QStackedWidget()
        c_layout.addWidget(self.stack, 1)

        # Build Pages
        self.page_dash = self._build_dashboard_page()
        self.stack.addWidget(self.page_dash)

        self.page_updater = self._build_updater_page()
        self.stack.addWidget(self.page_updater)

        self.page_clusters = self._build_clusters_page()
        self.stack.addWidget(self.page_clusters)

        self.page_lookahead = self._build_lookahead_page()
        self.stack.addWidget(self.page_lookahead)

        self.page_oos = self._build_oos_page()
        self.stack.addWidget(self.page_oos)

        # Schedule Audit & Comparison View
        self.page_compare = ScheduleComparisonView(self)
        self.page_compare.activity_selected.connect(self.inspect_activity)
        self.stack.addWidget(self.page_compare)

        # Historical Trends & Database Snapshots
        self.page_trends = TrendsView(self.state.db, self)
        self.page_trends.snapshot_selected.connect(self._on_historical_snapshot_inspected)
        self.stack.addWidget(self.page_trends)

        self.page_export = self._build_export_page()
        self.stack.addWidget(self.page_export)

        self.page_help = self._build_help_page()
        self.stack.addWidget(self.page_help)

        self.page_settings = self._build_settings_page()
        self.stack.addWidget(self.page_settings)

        body_layout.addWidget(center_area, 1)

        # 4. Right Master-Detail Inspector Pane (Activity Properties)
        self.inspector = InspectorPane(self)
        self.inspector.closed.connect(lambda: self.inspector.setVisible(False))
        body_layout.addWidget(self.inspector)

        root_vbox.addLayout(body_layout, 1)

        # 4. Authentic Vortex PT Status Footer Bar
        self.footer = StatusFooter(self)
        root_vbox.addWidget(self.footer)

    def toggle_inspector(self):
        self.inspector.setVisible(not self.inspector.isVisible())

    def navigate_to(self, page_id: str):
        page_map = {
            "dash": 0, "updater": 1, "clusters": 2,
            "lookahead": 3, "oos": 4, "compare": 5, "trends": 6, "export": 7,
            "help": 8, "settings": 9
        }
        idx = page_map.get(page_id, 0)
        self.stack.setCurrentIndex(idx)
        if page_id == "trends":
            self.page_trends.reload_data()

    # =========================================================================
    # Page 0: Dashboard
    # =========================================================================
    def _build_dashboard_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(14)

        # Empty Hero State (Zero-Data Start)
        self.hero_empty = QFrame()
        self.hero_empty.setObjectName("Card")
        hero_lay = QVBoxLayout(self.hero_empty)
        hero_lay.setContentsMargins(32, 40, 32, 40)
        hero_lay.setSpacing(12)
        hero_lay.setAlignment(Qt.AlignCenter)

        # Vector art / Graphic matching Vortex PT hero workspace
        h_art = QLabel()
        h_art.setAlignment(Qt.AlignCenter)
        h_art.setFixedSize(360, 60)
        # Custom mini SVG-like curve illustration
        pix = get_fluent_icon("dashboard", color="#00E5FF", size=54).pixmap(54, 54)
        h_art.setPixmap(pix)
        hero_lay.addWidget(h_art)

        h_title = QLabel("VORTEX CONTROLS — CONSTRUCTION WORKSPACE")
        h_title.setStyleSheet("font-size: 16px; font-weight: 900; color: #FFFFFF; letter-spacing: 1px;")
        h_title.setAlignment(Qt.AlignCenter)
        hero_lay.addWidget(h_title)

        h_desc = QLabel(
            "Open a Primavera P6 Baseline (.xer) and Weekly Site Progress (.xlsx) to automatically compute\n"
            "Earned Value (EVM), inspect critical path drivers, resolve procurement gating delays, and generate executive deliverables."
        )
        h_desc.setStyleSheet("font-size: 12.5px; color: #94A3B8; text-align: center; line-height: 18px;")
        h_desc.setAlignment(Qt.AlignCenter)
        hero_lay.addWidget(h_desc)
        hero_lay.addSpacing(10)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(14)
        btn_box.setAlignment(Qt.AlignCenter)

        btn_hero_bl = QPushButton("  Open Baseline (.xer)")
        btn_hero_bl.setObjectName("PrimaryBtn")
        btn_hero_bl.setIcon(get_fluent_icon("folder", color="#0F172A", size=16))
        btn_hero_bl.clicked.connect(self.select_baseline_file)
        btn_box.addWidget(btn_hero_bl)

        btn_hero_up = QPushButton("  Load Progress (.xlsx)")
        btn_hero_up.setObjectName("ActionBtn")
        btn_hero_up.setIcon(get_fluent_icon("excel", color="#FFFFFF", size=16))
        btn_hero_up.clicked.connect(self.select_excel_file)
        btn_box.addWidget(btn_hero_up)

        btn_hero_csv = QPushButton("  Paste Progress (CSV)")
        btn_hero_csv.setObjectName("ActionBtn")
        btn_hero_csv.setIcon(get_fluent_icon("updater", color="#00E5FF", size=16))
        btn_hero_csv.clicked.connect(self.open_paste_progress_dialog)
        btn_box.addWidget(btn_hero_csv)

        hero_lay.addLayout(btn_box)
        lay.addWidget(self.hero_empty)

        # Populated Dashboard Container
        self.dash_content = QWidget()
        self.live_dash = self.dash_content  # Alias for backward compatibility
        dc_lay = QVBoxLayout(self.dash_content)
        dc_lay.setContentsMargins(0, 0, 0, 0)
        dc_lay.setSpacing(14)

        # 1. KPI Cards Row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(10)

        self.kpi_actual = self._make_kpi_card("Actual Progress", "0.00%", "Planned: 0.00%")
        self.kpi_ev = self._make_kpi_card("Earned Value (EV)", "0.00M", "PV: 0.00M")
        self.kpi_spi = self._make_kpi_card("Schedule Index (SPI)", "1.00", "SV: 0.00M")
        self.kpi_fcst = self._make_kpi_card("Forecast Finish", "-", "Contract: -")
        self.kpi_acts = self._make_kpi_card("Activity Progress", "0 Active", "0 OOS Ties")

        for k in [self.kpi_actual, self.kpi_ev, self.kpi_spi, self.kpi_fcst, self.kpi_acts]:
            kpi_row.addWidget(k)
        dc_lay.addLayout(kpi_row)

        # 2. Native Vector S-Curve Card
        scurve_card = QFrame()
        scurve_card.setObjectName("Card")
        sc_lay = QVBoxLayout(scurve_card)
        sc_lay.setContentsMargins(14, 10, 14, 10)

        sc_title_row = QHBoxLayout()
        sc_lbl = QLabel("Cumulative Earned Value S-Curve (Planned PV vs Earned EV)")
        sc_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #FFFFFF;")
        sc_title_row.addWidget(sc_lbl)
        sc_title_row.addStretch()
        sc_lay.addLayout(sc_title_row)

        self.scurve_widget = ScurveWidget()
        sc_lay.addWidget(self.scurve_widget)
        dc_lay.addWidget(scurve_card)

        # 3. Quick Clusters Overview Table Card
        quick_card = QFrame()
        quick_card.setObjectName("Card")
        qc_lay = QVBoxLayout(quick_card)
        qc_lay.setContentsMargins(14, 10, 14, 10)

        qc_title_row = QHBoxLayout()
        qc_lbl = QLabel("Cluster Performance Summary (Click any row to inspect)")
        qc_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #FFFFFF;")
        qc_title_row.addWidget(qc_lbl)
        qc_title_row.addStretch()

        btn_view_all_clust = QPushButton("View Full Matrix →")
        btn_view_all_clust.setObjectName("ActionBtn")
        btn_view_all_clust.clicked.connect(lambda: self.nav_rail.select_page("clusters"))
        qc_title_row.addWidget(btn_view_all_clust)
        qc_lay.addLayout(qc_title_row)

        self.tbl_quick = QTableWidget(0, 7)
        self.tbl_quick.setHorizontalHeaderLabels([
            "Cluster", "BAC (EGP)", "Weight", "Planned %", "Actual %", "SV (EGP)", "SPI"
        ])
        self.tbl_quick.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_quick.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_quick.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_quick.cellClicked.connect(self._on_quick_cluster_clicked)
        qc_lay.addWidget(self.tbl_quick)

        dc_lay.addWidget(quick_card, 1)

        lay.addWidget(self.dash_content)
        self.dash_content.setVisible(False)
        return w

    def _make_kpi_card(self, title: str, val: str, sub: str) -> QFrame:
        card = QFrame()
        card.setObjectName("KpiCard")
        card.setFixedHeight(86)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(2)

        lbl_t = QLabel(title)
        lbl_t.setObjectName("KpiTitle")
        lbl_v = QLabel(val)
        lbl_v.setObjectName("KpiVal")
        lbl_s = QLabel(sub)
        lbl_s.setObjectName("KpiSub")

        lay.addWidget(lbl_t)
        lay.addWidget(lbl_v)
        lay.addWidget(lbl_s)
        return card

    # =========================================================================
    # Page 1: XER & Site Updater
    # =========================================================================
    def _build_updater_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(14)

        card = QFrame()
        card.setObjectName("Card")
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(20, 16, 20, 16)
        c_lay.setSpacing(12)

        lbl_head = QLabel("Primavera P6 Baseline & Weekly Site Updater")
        lbl_head.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")
        c_lay.addWidget(lbl_head)

        lbl_sub = QLabel("Select your Primavera P6 baseline schedule (.XER) and multi-cluster progress sheet (.XLSX) to execute full EVM update:")
        lbl_sub.setStyleSheet("font-size: 12px; color: #9E9E9E;")
        c_lay.addWidget(lbl_sub)

        # Baseline file row
        bl_row = QHBoxLayout()
        self.txt_bl_path = QLineEdit()
        self.txt_bl_path.setObjectName("PillSearch")
        self.txt_bl_path.setPlaceholderText("Select Primavera P6 Baseline (.XER)...")
        self.txt_bl_path.setReadOnly(True)
        btn_bl_browse = QPushButton("Browse .XER")
        btn_bl_browse.setObjectName("ActionBtn")
        btn_bl_browse.clicked.connect(self.select_baseline_file)
        bl_row.addWidget(QLabel("Baseline File:"))
        bl_row.addWidget(self.txt_bl_path, 1)
        bl_row.addWidget(btn_bl_browse)
        c_lay.addLayout(bl_row)

        # Site Excel file row
        up_row = QHBoxLayout()
        self.txt_excel_path = QLineEdit()
        self.txt_excel_path.setObjectName("PillSearch")
        self.txt_excel_path.setPlaceholderText("Select Weekly Site Progress Sheet (.XLSX)...")
        self.txt_excel_path.setReadOnly(True)
        btn_excel_browse = QPushButton("Browse .XLSX")
        btn_excel_browse.setObjectName("ActionBtn")
        btn_excel_browse.clicked.connect(self.select_excel_file)
        up_row.addWidget(QLabel("Progress File:"))
        up_row.addWidget(self.txt_excel_path, 1)
        up_row.addWidget(btn_excel_browse)
        c_lay.addLayout(up_row)

        # Data Date picker row
        dd_row = QHBoxLayout()
        self.dt_picker = QDateEdit()
        self.dt_picker.setCalendarPopup(True)
        self.dt_picker.setDate(QDate.currentDate())
        self.dt_picker.setDisplayFormat("yyyy-MM-dd")
        dd_row.addWidget(QLabel("Data Date:"))
        dd_row.addWidget(self.dt_picker)
        dd_row.addStretch()

        self.btn_run_update = QPushButton("  Execute Progress Recalculation")
        self.btn_run_update.setObjectName("PrimaryBtn")
        self.btn_run_update.setIcon(get_fluent_icon("refresh", color="#0F172A", size=16))
        self.btn_run_update.clicked.connect(self.execute_recalculation)
        dd_row.addWidget(self.btn_run_update)
        c_lay.addLayout(dd_row)

        lay.addWidget(card)

        # Execution Logs Card
        log_card = QFrame()
        log_card.setObjectName("Card")
        lc_lay = QVBoxLayout(log_card)
        lc_lay.setContentsMargins(16, 12, 16, 12)
        lc_lbl = QLabel("Schedule Ingestion & Update Execution Log:")
        lc_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #60CDFF;")
        lc_lay.addWidget(lc_lbl)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("background-color: #1F1F1F; border: 1px solid #383838; border-radius: 6px; font-family: 'Consolas', monospace; font-size: 12px; color: #D1D5DB;")
        lc_lay.addWidget(self.txt_log, 1)
        lay.addWidget(log_card, 1)

        return w

    # =========================================================================
    # Page 2: Clusters Matrix (C08 - C18)
    # =========================================================================
    def _build_clusters_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        hdr_row = QHBoxLayout()
        lbl_head = QLabel("Cluster Progression & Earned Value Matrix (C08–C18)")
        lbl_head.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")
        hdr_row.addWidget(lbl_head)
        hdr_row.addStretch()
        lay.addLayout(hdr_row)

        card = QFrame()
        card.setObjectName("Card")
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(14, 12, 14, 12)

        self.tbl_clusters = QTableWidget(0, 13)
        self.tbl_clusters.setHorizontalHeaderLabels([
            "Cluster", "BAC (EGP)", "Weight %", "Planned %", "Actual %", "Variance %",
            "PV (EGP)", "EV (EGP)", "SV (EGP)", "SPI", "Baseline Finish", "Forecast Finish", "Slip"
        ])
        self.tbl_clusters.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_clusters.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_clusters.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_clusters.cellClicked.connect(self._on_full_cluster_clicked)
        c_lay.addWidget(self.tbl_clusters)

        lay.addWidget(card, 1)
        return w

    # =========================================================================
    # Page 3: Lookahead Schedule & Activities
    # =========================================================================
    def _build_lookahead_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        lbl_head = QLabel("Lookahead Schedule & Critical Activities")
        lbl_head.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")
        lay.addWidget(lbl_head)

        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(8)

        self.txt_look_search = QLineEdit()
        self.txt_look_search.setObjectName("PillSearch")
        self.txt_look_search.setPlaceholderText("Find activity ID, name, cluster, or discipline...")
        self.txt_look_search.textChanged.connect(self.filter_lookahead)
        filter_bar.addWidget(self.txt_look_search, 1)

        self.btn_chip_all = QPushButton("All")
        self.btn_chip_all.setObjectName("FilterChip")
        self.btn_chip_all.setProperty("checked", "true")
        self.btn_chip_all.clicked.connect(lambda: self._set_active_filter_chip("ALL"))
        filter_bar.addWidget(self.btn_chip_all)

        self.btn_chip_crit = QPushButton("Critical Path (Float ≤ 0)")
        self.btn_chip_crit.setObjectName("FilterChip")
        self.btn_chip_crit.clicked.connect(lambda: self._set_active_filter_chip("CRITICAL"))
        filter_bar.addWidget(self.btn_chip_crit)

        self.btn_chip_delay = QPushButton("Delayed Only")
        self.btn_chip_delay.setObjectName("FilterChip")
        self.btn_chip_delay.clicked.connect(lambda: self._set_active_filter_chip("DELAYED"))
        filter_bar.addWidget(self.btn_chip_delay)

        self.btn_chip_prog = QPushButton("In Progress")
        self.btn_chip_prog.setObjectName("FilterChip")
        self.btn_chip_prog.clicked.connect(lambda: self._set_active_filter_chip("IN_PROGRESS"))
        filter_bar.addWidget(self.btn_chip_prog)

        self.active_filter_chip = "ALL"
        lay.addLayout(filter_bar)

        card = QFrame()
        card.setObjectName("Card")
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(14, 12, 14, 12)

        self.tbl_lookahead = QTableWidget(0, 10)
        self.tbl_lookahead.setHorizontalHeaderLabels([
            "Activity ID", "Activity Name", "Cluster", "Discipline",
            "Status", "Actual %", "Planned Start", "Baseline Finish", "Total Float", "Delay"
        ])
        self.tbl_lookahead.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_lookahead.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_lookahead.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_lookahead.cellClicked.connect(self._on_lookahead_clicked)
        c_lay.addWidget(self.tbl_lookahead)

        lay.addWidget(card, 1)
        return w

    def _set_active_filter_chip(self, chip_mode: str):
        self.active_filter_chip = chip_mode
        # Update topbar chips
        if hasattr(self, "chip_all"):
            for chip, mode in [
                (self.chip_all, "all"),
                (self.chip_active, "active"),
                (self.chip_crit, "critical"),
                (self.chip_delayed, "delayed"),
                (self.chip_oos, "oos"),
            ]:
                is_active = (mode == chip_mode)
                chip.setProperty("active", "true" if is_active else "false")
                chip.style().unpolish(chip)
                chip.style().polish(chip)
        # Update lookahead chips if present
        if hasattr(self, "btn_chip_all"):
            for btn, mode in [
                (self.btn_chip_all, "all"),
                (self.btn_chip_crit, "critical"),
                (self.btn_chip_delay, "delayed"),
                (self.btn_chip_prog, "active"),
            ]:
                btn.setProperty("checked", "true" if mode == chip_mode else "false")
                btn.style().unpolish(btn)
                btn.style().polish(btn)
        self.filter_lookahead()

    # =========================================================================
    # Page 4: Out-of-Sequence Audit
    # =========================================================================
    def _build_oos_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        lbl_head = QLabel("Out-of-Sequence Logic Violation Audit")
        lbl_head.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")
        lay.addWidget(lbl_head)

        lbl_sub = QLabel("Activities that have started or completed before their predecessors are finished violate network logic:")
        lbl_sub.setStyleSheet("font-size: 12px; color: #9E9E9E;")
        lay.addWidget(lbl_sub)

        card = QFrame()
        card.setObjectName("Card")
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(14, 12, 14, 12)

        self.tbl_oos = QTableWidget(0, 7)
        self.tbl_oos.setHorizontalHeaderLabels([
            "Predecessor ID", "Predecessor Name", "Tie",
            "Successor ID", "Successor Name", "Successor Status", "Successor %"
        ])
        self.tbl_oos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_oos.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_oos.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_oos.cellClicked.connect(self._on_oos_clicked)
        c_lay.addWidget(self.tbl_oos)

        lay.addWidget(card, 1)
        return w

    # =========================================================================
    # Page 5: Deliverables & Reports
    # =========================================================================
    def _build_export_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(14)

        lbl_head = QLabel("Deliverables & Report Generation")
        lbl_head.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")
        lay.addWidget(lbl_head)

        grid = QHBoxLayout()
        grid.setSpacing(14)

        # 1. Pure White PDF Report
        card_pdf = QFrame()
        card_pdf.setObjectName("Card")
        cp_lay = QVBoxLayout(card_pdf)
        cp_lay.setContentsMargins(18, 16, 18, 16)
        cp_lay.setSpacing(10)

        cp_icon = QLabel()
        cp_icon.setPixmap(get_fluent_icon("pdf", color="#60CDFF", size=32).pixmap(32, 32))
        cp_lay.addWidget(cp_icon)

        cp_title = QLabel("Executive PDF Report")
        cp_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #FFFFFF;")
        cp_lay.addWidget(cp_title)

        cp_desc = QLabel("Pure-white background vector report with high contrast dark typography, S-Curve chart, EVM scorecards, and cluster breakdown.")
        cp_desc.setStyleSheet("font-size: 12px; color: #9E9E9E;")
        cp_desc.setWordWrap(True)
        cp_lay.addWidget(cp_desc)
        cp_lay.addStretch()

        btn_pdf = QPushButton("Generate White PDF")
        btn_pdf.setObjectName("PrimaryBtn")
        btn_pdf.clicked.connect(self.quick_export_pdf)
        cp_lay.addWidget(btn_pdf)
        grid.addWidget(card_pdf)

        # 2. Excel Formatted Workbook
        card_xls = QFrame()
        card_xls.setObjectName("Card")
        cx_lay = QVBoxLayout(card_xls)
        cx_lay.setContentsMargins(18, 16, 18, 16)
        cx_lay.setSpacing(10)

        cx_icon = QLabel()
        cx_icon.setPixmap(get_fluent_icon("excel", color="#107C41", size=32).pixmap(32, 32))
        cx_lay.addWidget(cx_icon)

        cx_title = QLabel("Multi-Tab Excel Workbook")
        cx_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #FFFFFF;")
        cx_lay.addWidget(cx_title)

        cx_desc = QLabel("Comprehensive 6-tab formatted workbook: Executive Dashboard, Cluster Progress, Disciplines, Lookahead & Delays, Out-of-Sequence Ties, and S-Curve.")
        cx_desc.setStyleSheet("font-size: 12px; color: #9E9E9E;")
        cx_desc.setWordWrap(True)
        cx_lay.addWidget(cx_desc)
        cx_lay.addStretch()

        btn_xls = QPushButton("Export Excel (.xlsx)")
        btn_xls.setObjectName("ActionBtn")
        btn_xls.clicked.connect(self.export_excel)
        cx_lay.addWidget(btn_xls)
        grid.addWidget(card_xls)

        # 3. Updated Primavera Schedule XER
        card_xer = QFrame()
        card_xer.setObjectName("Card")
        cxr_lay = QVBoxLayout(card_xer)
        cxr_lay.setContentsMargins(18, 16, 18, 16)
        cxr_lay.setSpacing(10)

        cxr_icon = QLabel()
        cxr_icon.setPixmap(get_fluent_icon("updater", color="#0078D4", size=32).pixmap(32, 32))
        cxr_lay.addWidget(cxr_icon)

        cxr_title = QLabel("Updated Primavera P6 (.XER)")
        cxr_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #FFFFFF;")
        cxr_lay.addWidget(cxr_title)

        cxr_desc = QLabel("Direct P6 schedule export with actual start/finish dates, remaining durations, completion percentages, and recalculated resource costs.")
        cxr_desc.setStyleSheet("font-size: 12px; color: #9E9E9E;")
        cxr_desc.setWordWrap(True)
        cxr_lay.addWidget(cxr_desc)
        cxr_lay.addStretch()

        btn_xer = QPushButton("Export Updated P6 (.XER)")
        btn_xer.setObjectName("ActionBtn")
        btn_xer.clicked.connect(self.export_updated_xer)
        cxr_lay.addWidget(btn_xer)
        grid.addWidget(card_xer)

        lay.addLayout(grid)
        lay.addStretch(1)
        return w

    # =========================================================================
    # Page 6: Help & Guidance
    # =========================================================================
    def _build_help_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 16, 20, 16)

        card = QFrame()
        card.setObjectName("Card")
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(24, 20, 24, 20)
        c_lay.setSpacing(12)

        lbl_head = QLabel("Vortex Controls — User Manual & EVM Reference")
        lbl_head.setStyleSheet("font-size: 16px; font-weight: 800; color: #FFFFFF;")
        c_lay.addWidget(lbl_head)

        txt_help = QTextEdit()
        txt_help.setReadOnly(True)
        txt_help.setStyleSheet("background: transparent; border: none; color: #D1D5DB; font-size: 13px; line-height: 1.6;")
        txt_help.setHtml("""
        <h3 style="color:#60CDFF;">1. Workflow Overview</h3>
        <p>1. <b>Import Baseline (.XER)</b>: Loads your Primavera P6 schedule (TASK, TASKRSRC, TASKPRED, PROJECT, PROJWBS).<br/>
        2. <b>Import Site Progress (.XLSX)</b>: Reads multi-sheet actual dates, remaining durations, and % complete.<br/>
        3. <b>Data Date Recalculation</b>: Computes earned value, schedule slip, critical path float, and out-of-sequence logic violations.<br/>
        4. <b>Deliverables</b>: Export to a pure-white executive PDF, 6-tab formatted Excel, or updated Primavera .XER.</p>
        
        <h3 style="color:#60CDFF;">2. WinUI 3 Navigation, Themes & Footer</h3>
        <p>• <b>Live Themes</b>: Switch between <b>Mica</b>, <b>Mica Old (Mica Alt)</b>, <b>Acrylic</b>, and <b>Dark Solid</b> in the topbar or settings.<br/>
        • <b>Status Footer</b>: Live status dot, selection inspector, and real-time project metrics at the bottom.<br/>
        • <b>Historical Trends</b>: Check the <b>History & Trends</b> tab to review historical weekly progress updates stored in SQLite.</p>
        
        <h3 style="color:#60CDFF;">3. Earned Value Management (EVM) Formulas</h3>
        <p>• <b>Planned Value (PV)</b> = Planned % × BAC<br/>
        • <b>Earned Value (EV)</b> = Actual Physical % × BAC<br/>
        • <b>Schedule Variance (SV)</b> = EV - PV (Negative means behind schedule)<br/>
        • <b>Schedule Performance Index (SPI)</b> = EV / PV (> 1.0 means ahead, &lt; 1.0 means behind)</p>
        """)
        c_lay.addWidget(txt_help)

        lay.addWidget(card, 1)
        return w

    # =========================================================================
    # Page 7: Project Settings
    # =========================================================================
    def _build_settings_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(14)

        card = QFrame()
        card.setObjectName("Card")
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(20, 16, 20, 16)
        c_lay.setSpacing(14)

        lbl_head = QLabel("Project & Application Settings")
        lbl_head.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")
        c_lay.addWidget(lbl_head)

        # 1. Theme Configuration
        lbl_thm = QLabel("Windows 11 Fluent Material & Theme:")
        lbl_thm.setStyleSheet("font-weight: 600; color: #60CDFF;")
        c_lay.addWidget(lbl_thm)

        thm_box = QHBoxLayout()
        thm_box.setSpacing(10)
        for tid, tname in [
            ("mica", "Mica (Wallpaper)"),
            ("mica_alt", "Mica Old (Tabbed)"),
            ("acrylic", "Acrylic (Translucent)"),
            ("solid_dark", "Dark Solid")
        ]:
            btn_t = QPushButton(f"  {tname}")
            btn_t.setObjectName("ActionBtn")
            btn_t.clicked.connect(lambda ch, t=tid: self._set_theme_from_settings(t))
            thm_box.addWidget(btn_t)
        thm_box.addStretch()
        c_lay.addLayout(thm_box)

        c_lay.addSpacing(10)

        # 2. Database Diagnostics
        lbl_db = QLabel("SQLite Database Diagnostics:")
        lbl_db.setStyleSheet("font-weight: 600; color: #60CDFF;")
        c_lay.addWidget(lbl_db)

        self.lbl_db_info = QLabel("Database Path: vortex_controls.db | Stored Snapshots: 0")
        self.lbl_db_info.setStyleSheet("color: #9E9E9E; font-size: 12px;")
        c_lay.addWidget(self.lbl_db_info)

        c_lay.addSpacing(10)

        # 3. Session Reset
        lbl_sess = QLabel("Active Project Session Management:")
        lbl_sess.setStyleSheet("font-weight: 600; color: #60CDFF;")
        c_lay.addWidget(lbl_sess)

        btn_reset = QPushButton("  Reset Project Session (Clear Loaded Data)")
        btn_reset.setObjectName("ActionBtn")
        btn_reset.setIcon(get_fluent_icon("refresh", color="#EF4444", size=16))
        btn_reset.clicked.connect(self.reset_session)
        c_lay.addWidget(btn_reset)

        c_lay.addStretch(1)
        lay.addWidget(card, 1)
        return w

    def _set_theme_from_settings(self, theme_id: str):
        for i in range(self.cb_theme.count()):
            if self.cb_theme.itemData(i) == theme_id:
                self.cb_theme.setCurrentIndex(i)
                break

    # =========================================================================
    # State Listeners & View Refresh
    # =========================================================================
    def on_state_changed(self):
        self.refresh_views()

    def _on_layer_filter_toggled(self, layer_key: str, enabled: bool):
        """Applies layer visibility switches to lookahead and dashboard tables."""
        self.filter_lookahead()

    def _on_search_query_changed(self, text: str):
        """Live search filter matching activity ID or name."""
        query = text.strip().lower()
        if hasattr(self, "tb_lookahead") and self.tb_lookahead:
            for r in range(self.tb_lookahead.rowCount()):
                id_item = self.tb_lookahead.item(r, 0)
                name_item = self.tb_lookahead.item(r, 1)
                t_id = id_item.text().lower() if id_item else ""
                t_name = name_item.text().lower() if name_item else ""
                matches = (query in t_id) or (query in t_name) or not query
                self.tb_lookahead.setRowHidden(r, not matches)
        if query:
            self.footer.set_selection(f"Search: '{text.strip()}'")
        else:
            self.footer.set_selection("No selection")

    def run_cpm_update(self):
        """Runs CPM recalculation (F9) on the active project schedule."""
        self.footer.set_status("Recalculating CPM schedule and critical chains (F9)...", "working")
        try:
            self.state.apply_update_pipeline(data_date=self.state.data_date or "2026-11-12")
            self.refresh_views()
            self.footer.set_status(f"CPM Recalculated: Forecast completion is {self.state.analytics.get('forecast_finish')} (+{abs(self.state.analytics.get('variance_days', 0))}d)", "ready")
        except Exception as e:
            self.footer.set_status(f"CPM Recalculation error: {str(e)}", "error")

    def refresh_views(self):
        has_data = self.state.has_data()

        # Update empty hero vs dashboard content
        self.hero_empty.setVisible(not has_data)
        self.dash_content.setVisible(has_data)

        # Update Secondary Sidebar Metrics
        self.side_tool.update_metrics(self.state.analytics if has_data else None)

        # Update database settings text
        stats = self.state.db.get_database_stats()
        self.lbl_db_info.setText(
            f"Database: {stats['db_path']}\n"
            f"Size: {stats['db_size_kb']:.1f} KB | Snapshots: {stats['snapshot_count']} | Projects: {stats['project_count']}"
        )

        if not has_data:
            self.lbl_top_title.setText("Vortex Controls — Construction Project Controls")
            self.lbl_top_sub.setText("Import your baseline XER and weekly progress Excel to initialize dashboard")
            self.inspector.show_empty()
            self.footer.set_status("Ready - Import Baseline (.XER) and Site Progress (.XLSX) to analyze schedule", "ready")
            self.footer.set_selection("No selection")
            self.footer.set_metrics()
            return

        a = self.state.analytics
        is_baseline_only = bool(a.get("is_baseline_only", False))

        self.lbl_top_title.setText(f"{a.get('project_name', 'Vortex Controls Project')}")
        if is_baseline_only:
            self.lbl_top_sub.setText(f"Baseline Schedule Active  •  Data Date: {a.get('data_date')}  •  Contract Budget: {a.get('bac', 0)/1e6:.2f}M EGP  •  Ready for Weekly Progress")
            self.footer.set_status(f"Baseline Schedule Loaded: {a.get('baseline_name')} | BAC: {a.get('bac', 0)/1e6:.2f}M EGP | Ready for site progress update", "ready")
            self.footer.set_metrics(
                bac_m=a.get("bac", 0)/1e6,
                ev_m=0.0,
                spi=1.0,
                data_date=a.get("data_date", ""),
                oos_count=0
            )

            # Update KPIs for Baseline Intelligence Mode
            self.kpi_actual.findChild(QLabel, "KpiVal").setText("0.00%")
            self.kpi_actual.findChild(QLabel, "KpiSub").setText("Baseline Scope (No Actuals)")

            self.kpi_ev.findChild(QLabel, "KpiVal").setText(f"{a.get('bac', 0)/1e6:.2f}M EGP")
            self.kpi_ev.findChild(QLabel, "KpiSub").setText(f"Total Contract Budget (BAC)")

            self.kpi_spi.findChild(QLabel, "KpiVal").setText("1.00")
            self.kpi_spi.findChild(QLabel, "KpiSub").setText("Baseline Schedule Index")

            self.kpi_fcst.findChild(QLabel, "KpiVal").setText(f"{a.get('contract_finish', '-')}")
            self.kpi_fcst.findChild(QLabel, "KpiSub").setText(f"Contract Finish Date")

            self.kpi_acts.findChild(QLabel, "KpiVal").setText(f"{a.get('total_activities', 0):,} Activities")
            self.kpi_acts.findChild(QLabel, "KpiSub").setText(f"Across {len(a.get('clusters', []))} Clusters")
        else:
            self.lbl_top_sub.setText(f"Data Date: {a.get('data_date')}  •  Baseline: {a.get('baseline_name')}  •  Total Budget: {a.get('bac', 0)/1e6:.2f}M EGP")

            # Update Footer
            self.footer.set_status(f"Active Schedule: {a.get('baseline_name')} | Data Date: {a.get('data_date')}", "ready")
            self.footer.set_metrics(
                bac_m=a.get("bac", 0)/1e6,
                ev_m=a.get("ev", 0)/1e6,
                spi=a.get("spi", 1.0),
                data_date=a.get("data_date", ""),
                oos_count=a.get("oos_count", 0)
            )

            # Update KPIs
            self.kpi_actual.findChild(QLabel, "KpiVal").setText(f"{a.get('actual_pct', 0):.2f}%")
            self.kpi_actual.findChild(QLabel, "KpiSub").setText(f"Planned: {a.get('planned_pct', 0):.2f}% ({a.get('variance_pct', 0):+.2f}%)")

            self.kpi_ev.findChild(QLabel, "KpiVal").setText(f"{a.get('ev', 0)/1e6:.2f}M EGP")
            self.kpi_ev.findChild(QLabel, "KpiSub").setText(f"PV: {a.get('pv', 0)/1e6:.2f}M / BAC: {a.get('bac', 0)/1e6:.2f}M")

            self.kpi_spi.findChild(QLabel, "KpiVal").setText(f"{a.get('spi', 0):.2f}")
            self.kpi_spi.findChild(QLabel, "KpiSub").setText(f"SV: {a.get('sv', 0)/1e6:+.2f}M EGP")

            self.kpi_fcst.findChild(QLabel, "KpiVal").setText(f"{a.get('forecast_finish', '-')}")
            self.kpi_fcst.findChild(QLabel, "KpiSub").setText(f"Contract: {a.get('contract_finish', '-')} ({a.get('variance_days', 0)}d)")

            self.kpi_acts.findChild(QLabel, "KpiVal").setText(f"{a.get('active_count', 0)} Act / {a.get('completed_count', 0)} Done")
            self.kpi_acts.findChild(QLabel, "KpiSub").setText(f"{a.get('oos_count', 0)} Out-of-Sequence Ties")

        # Update Comparison View if present
        if hasattr(self, "page_compare") and self.state.xer_engine:
            self.page_compare.set_schedules(self.state.xer_engine, self.state.xer_engine)

        # Update S-Curve
        if a.get("scurve"):
            self.scurve_widget.set_data(a["scurve"], a.get("data_date", ""))

        # Update Quick Table & Clusters Table
        clusters = a.get("clusters", [])
        self.tbl_quick.setRowCount(len(clusters))
        self.tbl_clusters.setRowCount(len(clusters))

        for i, c in enumerate(clusters):
            # Quick Table
            row_q = [
                c["cluster"], f"{c['bac']/1e6:.2f}M", f"{c['weight']:.1f}%",
                f"{c['planned_pct']:.1f}%", f"{c['actual_pct']:.1f}%",
                f"{c['sv']/1e6:+.2f}M", f"{c['spi']:.2f}"
            ]
            for j, val in enumerate(row_q):
                item = QTableWidgetItem(val)
                self.tbl_quick.setItem(i, j, item)

            # Full Clusters Table
            row_f = [
                c["cluster"], f"{c['bac']/1e6:.2f}M", f"{c['weight']:.1f}%",
                f"{c['planned_pct']:.1f}%", f"{c['actual_pct']:.1f}%", f"{c['variance_pct']:+.1f}%",
                f"{c['pv']/1e6:.2f}M", f"{c['ev']/1e6:.2f}M", f"{c['sv']/1e6:+.2f}M",
                f"{c['spi']:.2f}", c.get("bl_finish", "-")[:10], c.get("fcst_finish", "-")[:10], f"{c.get('slip_days', 0)}d"
            ]
            for j, val in enumerate(row_f):
                item = QTableWidgetItem(val)
                self.tbl_clusters.setItem(i, j, item)

        # Update OOS Table
        oos_list = a.get("oos_ties", [])
        self.tbl_oos.setRowCount(len(oos_list))
        for i, o in enumerate(oos_list):
            row_oos = [
                o["pred_id"], o["pred_name"], o["tie"],
                o["succ_id"], o["succ_name"], o["succ_status"], f"{o['succ_pct']:.1f}%"
            ]
            for j, val in enumerate(row_oos):
                self.tbl_oos.setItem(i, j, QTableWidgetItem(val))

        self.filter_lookahead()
        self.page_trends.reload_data()

    def filter_lookahead(self):
        a = self.state.analytics
        if not a or not a.get("activities"):
            self.tbl_lookahead.setRowCount(0)
            return

        q = self.txt_look_search.text().strip().lower()
        mode = getattr(self, "active_filter_chip", "ALL")

        filtered = []
        for act in a["activities"]:
            # Chip filter
            if mode == "CRITICAL" and act.get("total_float", 999) > 0:
                continue
            if mode == "DELAYED" and act.get("late_days", 0) <= 0:
                continue
            if mode == "IN_PROGRESS" and "prog" not in act.get("status", "").lower():
                continue

            # Text search filter
            if q:
                match = (
                    q in act.get("act_id", "").lower()
                    or q in act.get("act_name", "").lower()
                    or q in act.get("cluster", "").lower()
                    or q in act.get("discipline", "").lower()
                )
                if not match:
                    continue

            filtered.append(act)

        self.filtered_activities = filtered
        self.tbl_lookahead.setRowCount(len(filtered))
        for i, act in enumerate(filtered):
            late_d = act.get("late_days", 0)
            tf = act.get("total_float", 0)
            row_vals = [
                act["act_id"], act["act_name"], act.get("cluster", ""),
                act.get("discipline", ""), act.get("status", ""), f"{act.get('pct', 0):.1f}%",
                act.get("target_start", "-")[:10], act.get("bl_finish", "-")[:10],
                f"{tf}d" if tf is not None else "-",
                f"{late_d}d" if late_d > 0 else "-"
            ]
            for j, val in enumerate(row_vals):
                item = QTableWidgetItem(val)
                if j == 8 and tf <= 0:
                    item.setForeground(QColor("#EF4444"))  # Critical path red
                if j == 9 and late_d > 0:
                    item.setForeground(QColor("#EF4444"))  # Late red
                self.tbl_lookahead.setItem(i, j, item)

    # =========================================================================
    # Selection Event Handlers & Footer Updates
    # =========================================================================
    def inspect_activity(self, act_id: str):
        """Inspects an activity by ID in the right properties inspector."""
        a = self.state.analytics
        if a and "activities" in a:
            for act in a.get("activities", []):
                if act.get("act_id") == act_id:
                    self.inspector.setVisible(True)
                    self.inspector.inspect_activity(act)
                    self.footer.set_selection(f"Activity: {act.get('act_id')} ({act.get('act_name', '')[:25]})")
                    return
        self.inspector.setVisible(True)
        self.inspector.inspect_activity({"act_id": act_id, "act_name": act_id, "status": "Active"})
        self.footer.set_selection(f"Activity: {act_id}")

    def _on_lookahead_clicked(self, row: int, col: int):
        if hasattr(self, "filtered_activities") and 0 <= row < len(self.filtered_activities):
            act = self.filtered_activities[row]
            self.inspector.setVisible(True)
            self.inspector.inspect_activity(act)
            self.footer.set_selection(f"Activity: {act.get('act_id')} ({act.get('act_name', '')[:25]})")

    def _on_quick_cluster_clicked(self, row: int, col: int):
        a = self.state.analytics
        if a and "clusters" in a and 0 <= row < len(a["clusters"]):
            clust = a["clusters"][row]
            self.inspector.setVisible(True)
            self.inspector.inspect_cluster(clust)
            self.footer.set_selection(f"Cluster: {clust.get('cluster')} (BAC: {clust.get('bac', 0)/1e6:.2f}M EGP)")

    def _on_full_cluster_clicked(self, row: int, col: int):
        self._on_quick_cluster_clicked(row, col)

    def _on_oos_clicked(self, row: int, col: int):
        a = self.state.analytics
        if a and "oos_ties" in a and 0 <= row < len(a["oos_ties"]):
            tie = a["oos_ties"][row]
            self.footer.set_selection(f"OOS Tie: {tie.get('pred_id')} ➔ {tie.get('succ_id')}")
            succ_id = tie.get("succ_id")
            for act in a.get("activities", []):
                if act.get("act_id") == succ_id:
                    self.inspector.setVisible(True)
                    self.inspector.inspect_activity(act)
                    return

    def _on_historical_snapshot_inspected(self, snapshot_id: int):
        snap = self.state.db.get_snapshot_by_id(snapshot_id)
        if snap:
            self.footer.set_selection(f"DB Snapshot #{snap.get('id')} ({snap.get('data_date')})")
            QMessageBox.information(
                self,
                f"Database Snapshot #{snapshot_id}",
                f"Project: {snap.get('project_name')}\n"
                f"Data Date: {snap.get('data_date')}\n"
                f"Planned: {snap.get('planned_pct', 0):.2f}% | Actual: {snap.get('actual_pct', 0):.2f}%\n"
                f"Earned Value (EV): {snap.get('ev', 0)/1e6:.2f}M EGP\n"
                f"Schedule Performance Index (SPI): {snap.get('spi', 1.0):.2f}\n"
                f"Recorded at: {snap.get('snapshot_time')}"
            )

    # =========================================================================
    # File Operations & Recalculation
    # =========================================================================
    def select_baseline_file(self):
        fpath, _ = QFileDialog.getOpenFileName(self, "Select Primavera P6 Baseline (.XER)", "", "P6 Schedule Files (*.xer)")
        if fpath:
            self.load_baseline_path(fpath)

    def load_baseline_path(self, fpath: str):
        self.txt_bl_path.setText(fpath)
        self.state.load_baseline(fpath)
        self.txt_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Loaded Baseline: {fpath}")
        self.footer.set_status(f"Loaded Baseline: {os.path.basename(fpath)}", "working")

    def select_excel_file(self):
        fpath, _ = QFileDialog.getOpenFileName(self, "Select Weekly Site Progress (.XLSX)", "", "Excel Spreadsheets (*.xlsx *.xls)")
        if fpath:
            self.load_excel_path(fpath)

    def load_excel_path(self, fpath: str):
        self.txt_excel_path.setText(fpath)
        self.state.load_site_excel(fpath)
        self.txt_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Loaded Progress Sheet: {fpath}")
        self.footer.set_status(f"Loaded Progress: {os.path.basename(fpath)}", "working")

    def open_paste_progress_dialog(self):
        """Opens modal dialog allowing user to paste progress CSV text directly."""
        dlg = PasteProgressDialog(self, default_date=self.state.data_date)
        if dlg.exec():
            csv_text, dd = dlg.get_data()
            if not csv_text:
                return
            if not self.state.xer_engine:
                QMessageBox.warning(self, "No Baseline Loaded", "Please load a baseline schedule (.xer) first before applying site progress.")
                return
            self.footer.set_status("Parsing pasted site progress and recalculating CPM...", "working")
            QApplication.processEvents()
            self.state.load_site_csv_text(csv_text)
            self.state.apply_update_pipeline(dd or "2026-11-12")
            self.refresh_views()
            self.footer.set_status("Site progress applied successfully from pasted CSV!", "ready")

    def execute_recalculation(self):
        dd = self.dt_picker.date().toString("yyyy-MM-dd")
        self.txt_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Recalculating schedule for Data Date: {dd}...")
        self.footer.set_status(f"Recalculating EVM for Data Date: {dd}...", "working")
        success = self.state.run_update(dd)
        if success:
            self.txt_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Update pipeline finished & snapshot saved to SQLite!")
            self.nav_rail.select_page("dash")
            self.footer.set_status(f"Update Finished & Saved to SQLite | Data Date: {dd}", "ready")
        else:
            self.txt_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Update failed. Ensure both baseline .XER and progress .XLSX are selected.")
            self.footer.set_status("Update failed - check files", "error")
            QMessageBox.warning(self, "Update Failed", "Please load both a baseline .XER and site progress .XLSX file first.")

    def quick_export_pdf(self):
        if not self.state.has_data():
            QMessageBox.information(self, "No Schedule Loaded", "Please load a baseline schedule before exporting.")
            return

        proj_name = self.state.analytics.get("project_name", "Vortex_Report").replace(" ", "_")
        dd = self.state.analytics.get("data_date", "Report")
        default_name = f"{proj_name}_{dd}.pdf"

        fpath, _ = QFileDialog.getSaveFileName(self, "Save Executive Pure-White PDF Report", default_name, "PDF Documents (*.pdf)")
        if fpath:
            success, msg = PDFExporter.export_pdf(self.state.analytics, fpath)
            if success:
                self.footer.set_status(f"Exported Pure-White PDF: {os.path.basename(fpath)}", "ready")
                QMessageBox.information(self, "Export Complete", f"Pure-white executive PDF successfully generated:\n\n{fpath}")
            else:
                self.footer.set_status("PDF Export Error", "error")
                QMessageBox.critical(self, "Export Error", f"PDF export failed:\n\n{msg}")

    def export_excel(self):
        if not self.state.has_data():
            QMessageBox.information(self, "No Schedule Loaded", "Please load a baseline schedule before exporting.")
            return

        proj_name = self.state.analytics.get("project_name", "Vortex_Report").replace(" ", "_")
        dd = self.state.analytics.get("data_date", "Report")
        default_name = f"{proj_name}_{dd}.xlsx"

        fpath, _ = QFileDialog.getSaveFileName(self, "Save Multi-Tab Excel Workbook", default_name, "Excel Spreadsheets (*.xlsx)")
        if fpath:
            success, msg = ExcelExporter.export_workbook(self.state.analytics, fpath)
            if success:
                self.footer.set_status(f"Exported Excel: {os.path.basename(fpath)}", "ready")
                QMessageBox.information(self, "Export Complete", f"Excel workbook successfully generated:\n\n{fpath}")
            else:
                self.footer.set_status("Excel Export Error", "error")
                QMessageBox.critical(self, "Export Error", f"Excel export failed:\n\n{msg}")

    def export_updated_xer(self):
        if not self.state.has_data():
            QMessageBox.information(self, "No Schedule Loaded", "Please load a baseline schedule before exporting.")
            return

        proj_name = self.state.analytics.get("project_name", "Vortex_Schedule").replace(" ", "_")
        dd = self.state.analytics.get("data_date", "Updated")
        default_name = f"{proj_name}_{dd}.xer"

        fpath, _ = QFileDialog.getSaveFileName(self, "Save Updated Primavera P6 Schedule", default_name, "Primavera P6 Files (*.xer)")
        if fpath:
            success, msg = self.state.export_updated_xer(fpath)
            if success:
                self.footer.set_status(f"Exported Updated XER: {os.path.basename(fpath)}", "ready")
                QMessageBox.information(self, "Export Complete", f"Updated P6 schedule successfully written:\n\n{fpath}")
            else:
                self.footer.set_status("XER Export Error", "error")
                QMessageBox.critical(self, "Export Error", f"P6 export failed:\n\n{msg}")

    def reset_session(self):
        reply = QMessageBox.question(
            self,
            "Reset Project Session",
            "Are you sure you want to unload the current schedule and reset the application to a pristine empty state?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.state.reset_project()
            self.txt_bl_path.clear()
            self.txt_excel_path.clear()
            self.txt_log.clear()
            self.nav_rail.select_page("dash")
            self.footer.set_status("Project session reset to pristine empty state", "ready")
            self.footer.set_selection("No selection")
            self.footer.set_metrics()
