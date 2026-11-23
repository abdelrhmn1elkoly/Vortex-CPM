"""Authentic Vortex PT Status Footer Bar for Vortex Controls.
Replicates the status footer from the Vortex PT reference:
- Status Indicator Dot (Green Ready / Amber Calculating / Red Error)
- Status text label
- Active Selection label (No selection / Activity ID / Cluster)
- Live project and database metrics readout
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget


class StatusFooter(QFrame):
    """Bottom status bar with live status dot, active selection, and metrics."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("StatusFooter")
        self._init_ui()

    def _init_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(10)

        # 1. Left Status Dot & Text
        self.dot_lbl = QLabel("●")
        self.dot_lbl.setStyleSheet("color: #10B981; font-size: 11px; margin-right: -4px;")
        lay.addWidget(self.dot_lbl)

        self.status_lbl = QLabel("Ready - Import Baseline (.XER) and Site Progress (.XLSX) to analyze schedule")
        self.status_lbl.setObjectName("FooterStatusText")
        lay.addWidget(self.status_lbl)

        lay.addStretch(1)

        # 2. Middle Selection Label
        self.selection_lbl = QLabel("No selection")
        self.selection_lbl.setObjectName("FooterSelectionText")
        lay.addWidget(self.selection_lbl)

        lay.addStretch(1)

        # 3. Right Metrics Readout
        self.metrics_lbl = QLabel("BAC: - | EV: - | SPI: - | DB: Connected (vortex_controls.db)")
        self.metrics_lbl.setObjectName("FooterMetricsText")
        lay.addWidget(self.metrics_lbl)

    def set_status(self, text: str, state: str = "ready"):
        """Sets the status message and indicator dot color ('ready', 'working', 'warning', 'error')."""
        colors = {
            "ready": "#10B981",    # Green
            "working": "#38BDF8",  # Cyan
            "warning": "#F59E0B",  # Amber
            "error": "#EF4444",    # Red
        }
        color = colors.get(state, "#10B981")
        self.dot_lbl.setStyleSheet(f"color: {color}; font-size: 11px; margin-right: -4px;")
        self.status_lbl.setText(text)

    def set_selection(self, text: str):
        """Updates the active selection display."""
        if not text:
            self.selection_lbl.setText("No selection")
        else:
            self.selection_lbl.setText(text)

    def set_metrics(self, bac_m: float = 0.0, ev_m: float = 0.0, spi: float = 1.0, data_date: str = "", oos_count: int = 0):
        """Updates the live engineering and financial metrics readout."""
        parts = []
        if bac_m > 0:
            parts.append(f"BAC: {bac_m:.2f}M EGP")
        if ev_m > 0:
            parts.append(f"EV: {ev_m:.2f}M")
        if spi > 0:
            parts.append(f"SPI: {spi:.2f}")
        if data_date:
            parts.append(f"DD: {data_date}")
        if oos_count > 0:
            parts.append(f"OOS: {oos_count}")
        parts.append("DB: SQLite (Active)")

        self.metrics_lbl.setText(" | ".join(parts))
