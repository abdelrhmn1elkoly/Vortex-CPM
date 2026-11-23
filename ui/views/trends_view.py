"""Multi-Week Progress Trends & SQLite Database Snapshot Dashboard for Vortex Controls.
Allows project controls engineers and managers to track earned value progression over time,
compare historical weekly progress updates, and inspect database snapshots.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QFrame,
    QScrollArea, QMessageBox
)

from core.database_engine import DatabaseEngine
from ui.custom_icons import get_fluent_icon


class MultiWeekTrendWidget(QWidget):
    """Plots multi-week Earned Value and Planned Value progression across database snapshots."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.snapshots: List[Dict[str, Any]] = []
        self.setMinimumHeight(180)

    def set_data(self, snapshots: List[Dict[str, Any]]):
        self.snapshots = snapshots
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        if not self.snapshots or len(self.snapshots) < 1:
            painter.setPen(QColor("#64748B"))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(
                self.rect(),
                Qt.AlignCenter,
                "No historical database snapshots recorded yet.\nRun recalculations to accumulate weekly progress snapshots in SQLite."
            )
            return

        pad_l, pad_r = 60, 30
        pad_t, pad_b = 30, 35
        plot_w = w - pad_l - pad_r
        plot_h = h - pad_t - pad_b

        # Compute max EV and PV
        max_val = max(
            [s.get("pv", 0) / 1e6 for s in self.snapshots] +
            [s.get("ev", 0) / 1e6 for s in self.snapshots] +
            [10.0]
        ) * 1.1

        # Draw gridlines
        grid_pen = QPen(QColor("#383838"), 1, Qt.DashLine)
        text_pen = QColor("#94A3B8")
        font = QFont("Segoe UI", 8)
        painter.setFont(font)

        for i in range(5):
            ratio = i / 4.0
            y = pad_t + plot_h * (1.0 - ratio)
            val = max_val * ratio
            painter.setPen(grid_pen)
            painter.drawLine(pad_l, y, w - pad_r, y)
            painter.setPen(text_pen)
            painter.drawText(pad_l - 55, y + 4, f"{val:.0f}M")

        n = len(self.snapshots)
        step = plot_w / max(1, n - 1) if n > 1 else plot_w / 2

        # 1. Planned Value Curve
        painter.setPen(QPen(QColor("#0078D4"), 2.5))
        for i in range(n - 1):
            x1 = pad_l + i * step
            y1 = pad_t + plot_h * (1.0 - ((self.snapshots[i].get("pv", 0) / 1e6) / max_val))
            x2 = pad_l + (i + 1) * step
            y2 = pad_t + plot_h * (1.0 - ((self.snapshots[i + 1].get("pv", 0) / 1e6) / max_val))
            painter.drawLine(x1, y1, x2, y2)

        # 2. Earned Value Curve
        painter.setPen(QPen(QColor("#10B981"), 3))
        for i in range(n - 1):
            x1 = pad_l + i * step
            y1 = pad_t + plot_h * (1.0 - ((self.snapshots[i].get("ev", 0) / 1e6) / max_val))
            x2 = pad_l + (i + 1) * step
            y2 = pad_t + plot_h * (1.0 - ((self.snapshots[i + 1].get("ev", 0) / 1e6) / max_val))
            painter.drawLine(x1, y1, x2, y2)

        # Draw points and x-axis labels
        painter.setBrush(QColor("#10B981"))
        for i, s in enumerate(self.snapshots):
            x = pad_l + i * step if n > 1 else pad_l + plot_w / 2
            y = pad_t + plot_h * (1.0 - ((s.get("ev", 0) / 1e6) / max_val))
            painter.drawEllipse(x - 4, y - 4, 8, 8)

            # Date label below axis
            dt = s.get("data_date", "")[:10]
            painter.setPen(text_pen)
            painter.drawText(x - 30, h - 12, dt)

        # Legend
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#0078D4"))
        painter.drawRect(w - 180, 10, 12, 5)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(w - 163, 16, "Planned (PV)")

        painter.setBrush(QColor("#10B981"))
        painter.drawRect(w - 80, 10, 12, 5)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(w - 63, 16, "Earned (EV)")


class TrendsView(QWidget):
    """View showing historical database snapshots and multi-week progression analytics."""

    snapshot_selected = Signal(int)

    def __init__(self, db: DatabaseEngine, parent=None):
        super().__init__(parent)
        self.db = db
        self._init_ui()
        self.reload_data()

    def _init_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(14)

        # Top Header
        hdr = QHBoxLayout()
        lbl_head = QLabel("Historical Progress Trends & Database Snapshots")
        lbl_head.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF;")
        hdr.addWidget(lbl_head)
        hdr.addStretch()

        btn_refresh = QPushButton("  Refresh Database")
        btn_refresh.setObjectName("ActionBtn")
        btn_refresh.setIcon(get_fluent_icon("refresh", color="#FFFFFF", size=16))
        btn_refresh.clicked.connect(self.reload_data)
        hdr.addWidget(btn_refresh)
        lay.addLayout(hdr)

        # KPI Tiles Row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(10)

        self.card_snaps = self._make_card("Recorded Snapshots", "0 Updates", "Database: SQLite")
        self.card_ev = self._make_card("Latest Earned Value", "0.00M", "Cumulative EV")
        self.card_spi = self._make_card("Latest SPI", "1.00", "Schedule Index")
        self.card_velocity = self._make_card("Progress Velocity", "0.0%", "Avg % gain per week")

        for c in [self.card_snaps, self.card_ev, self.card_spi, self.card_velocity]:
            kpi_row.addWidget(c)
        lay.addLayout(kpi_row)

        # Multi-Week Trend Chart Card
        chart_card = QFrame()
        chart_card.setObjectName("Card")
        cc_lay = QVBoxLayout(chart_card)
        cc_lay.setContentsMargins(14, 10, 14, 10)

        c_title = QLabel("Historical Earned Value vs Planned Value Growth (M EGP)")
        c_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #FFFFFF;")
        cc_lay.addWidget(c_title)

        self.trend_widget = MultiWeekTrendWidget()
        cc_lay.addWidget(self.trend_widget)
        lay.addWidget(chart_card)

        # Historical Snapshots Table Card
        tbl_card = QFrame()
        tbl_card.setObjectName("Card")
        tc_lay = QVBoxLayout(tbl_card)
        tc_lay.setContentsMargins(14, 12, 14, 12)

        tc_title = QLabel("Database Snapshot Log (Click any row to inspect)")
        tc_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #FFFFFF;")
        tc_lay.addWidget(tc_title)

        self.tbl_snapshots = QTableWidget(0, 9)
        self.tbl_snapshots.setHorizontalHeaderLabels([
            "ID", "Data Date", "Planned %", "Actual %", "Variance %",
            "PV (EGP)", "EV (EGP)", "SPI", "Recorded At"
        ])
        self.tbl_snapshots.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_snapshots.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_snapshots.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_snapshots.cellClicked.connect(self._on_snapshot_clicked)
        tc_lay.addWidget(self.tbl_snapshots)

        lay.addWidget(tbl_card, 1)

    def _make_card(self, title: str, val: str, sub: str) -> QFrame:
        card = QFrame()
        card.setObjectName("KpiCard")
        card.setFixedHeight(84)
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

    def reload_data(self):
        """Reloads snapshots from the SQLite database."""
        snaps = self.db.get_all_snapshots()
        self.trend_widget.set_data(snaps)

        count = len(snaps)
        self.card_snaps.findChild(QLabel, "KpiVal").setText(f"{count} Updates")
        self.card_snaps.findChild(QLabel, "KpiSub").setText(f"{self.db.get_database_stats()['db_size_kb']:.1f} KB SQLite")

        if snaps:
            latest = snaps[-1]
            self.card_ev.findChild(QLabel, "KpiVal").setText(f"{latest.get('ev', 0)/1e6:.2f}M")
            self.card_ev.findChild(QLabel, "KpiSub").setText(f"Date: {latest.get('data_date')}")

            spi = latest.get("spi", 1.0)
            self.card_spi.findChild(QLabel, "KpiVal").setText(f"{spi:.2f}")
            self.card_spi.findChild(QLabel, "KpiSub").setText(f"Variance: {latest.get('variance_pct', 0):+.1f}%")

            if count > 1:
                first = snaps[0]
                gain = latest.get("actual_pct", 0) - first.get("actual_pct", 0)
                self.card_velocity.findChild(QLabel, "KpiVal").setText(f"{gain/max(1, count-1):+.2f}%/wk")
                self.card_velocity.findChild(QLabel, "KpiSub").setText(f"Total Gain: {gain:+.1f}%")
            else:
                self.card_velocity.findChild(QLabel, "KpiVal").setText(f"{latest.get('actual_pct', 0):.1f}%")
                self.card_velocity.findChild(QLabel, "KpiSub").setText("Initial Snapshot")
        else:
            self.card_ev.findChild(QLabel, "KpiVal").setText("0.00M")
            self.card_spi.findChild(QLabel, "KpiVal").setText("1.00")
            self.card_velocity.findChild(QLabel, "KpiVal").setText("0.0%")

        # Populate table
        self.tbl_snapshots.setRowCount(count)
        for i, s in enumerate(snaps):
            row_vals = [
                str(s.get("id", i + 1)),
                str(s.get("data_date", "-")),
                f"{s.get('planned_pct', 0):.2f}%",
                f"{s.get('actual_pct', 0):.2f}%",
                f"{s.get('variance_pct', 0):+.2f}%",
                f"{s.get('pv', 0)/1e6:.2f}M",
                f"{s.get('ev', 0)/1e6:.2f}M",
                f"{s.get('spi', 1.0):.2f}",
                str(s.get("snapshot_time", "-"))[:19]
            ]
            for j, val in enumerate(row_vals):
                item = QTableWidgetItem(val)
                self.tbl_snapshots.setItem(i, j, item)

    def _on_snapshot_clicked(self, row: int, col: int):
        snaps = self.db.get_all_snapshots()
        if 0 <= row < len(snaps):
            snap_id = snaps[row].get("id")
            if snap_id:
                self.snapshot_selected.emit(snap_id)
