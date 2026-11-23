"""Authentic Vortex PT Secondary Sidebar (Layers & Project Metrics).
Replicates the left-hand Drawing Layers and Project Metrics cards from Vortex PT:
- Activity Layers toggle switches with color dots (Critical Path, Active, Completed, Not Started, Milestones, E&P)
- Project Controls live metrics card (Project, Data Date, Contract Finish, Forecast Finish, BAC, PV, EV, SV, SPI)
- Quick 'Change' action button to switch baseline schedules
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QSizePolicy
)
from qfluentwidgets import SwitchButton
from ui.custom_icons import get_fluent_icon


class SideToolPane(QFrame):
    """Secondary left panel providing activity layers/filters and live project metrics."""

    layer_toggled = Signal(str, bool)
    change_project_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SideToolPane")
        self.setFixedWidth(240)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.layer_switches: Dict[str, SwitchButton] = {}
        self.metric_labels: Dict[str, QLabel] = {}

        self._init_ui()

    def _init_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(10, 10, 10, 10)
        main_lay.setSpacing(10)

        # -------------------------------------------------------------
        # 1. Activity Layers & Filters Card
        # -------------------------------------------------------------
        card_layers = QFrame()
        card_layers.setObjectName("SidebarCard")
        lay_layers = QVBoxLayout(card_layers)
        lay_layers.setContentsMargins(10, 10, 10, 10)
        lay_layers.setSpacing(6)

        hdr_layers = QHBoxLayout()
        lbl_layers_title = QLabel("ACTIVITY LAYERS")
        lbl_layers_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #FFFFFF; letter-spacing: 0.8px;")
        hdr_layers.addWidget(lbl_layers_title)
        hdr_layers.addStretch()

        btn_all = QPushButton("All")
        btn_all.setObjectName("SubtleLinkBtn")
        btn_all.setCursor(Qt.PointingHandCursor)
        btn_all.clicked.connect(self._layers_all_on)
        hdr_layers.addWidget(btn_all)

        btn_none = QPushButton("None")
        btn_none.setObjectName("SubtleLinkBtn")
        btn_none.setCursor(Qt.PointingHandCursor)
        btn_none.clicked.connect(self._layers_all_off)
        hdr_layers.addWidget(btn_none)

        lay_layers.addLayout(hdr_layers)

        # Subtle divider
        div1 = QFrame()
        div1.setFixedHeight(1)
        div1.setStyleSheet("background: rgba(255, 255, 255, 0.08); margin-bottom: 4px;")
        lay_layers.addWidget(div1)

        # Layer definitions: (key, name, color, default_on)
        layers = [
            ("critical", "Critical Path", "#EF4444", True),
            ("active", "In Progress", "#00F2FE", True),
            ("complete", "Completed", "#10B981", True),
            ("not_started", "Not Started", "#64748B", True),
            ("milestones", "Milestone Gates", "#F59E0B", True),
            ("ep", "Eng. & Procurement", "#8B5CF6", True),
        ]

        for key, name, color, default_on in layers:
            row_f = QFrame()
            row_lay = QHBoxLayout(row_f)
            row_lay.setContentsMargins(2, 2, 2, 2)
            row_lay.setSpacing(8)

            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 11px;")
            row_lay.addWidget(dot)

            lbl = QLabel(name)
            lbl.setStyleSheet("color: #E2E8F0; font-size: 11px; font-weight: 500;")
            row_lay.addWidget(lbl, 1)

            sb = SwitchButton()
            sb.setChecked(default_on)
            sb.setCursor(Qt.PointingHandCursor)
            sb.checkedChanged.connect(lambda state, k=key: self.layer_toggled.emit(k, state))
            row_lay.addWidget(sb)

            self.layer_switches[key] = sb
            lay_layers.addWidget(row_f)

        main_lay.addWidget(card_layers)

        # -------------------------------------------------------------
        # 2. Project Controls Metrics Card (Matching Vortex PT)
        # -------------------------------------------------------------
        card_metrics = QFrame()
        card_metrics.setObjectName("SidebarCard")
        lay_metrics = QVBoxLayout(card_metrics)
        lay_metrics.setContentsMargins(10, 10, 10, 10)
        lay_metrics.setSpacing(5)

        hdr_metrics = QHBoxLayout()
        lbl_metrics_title = QLabel("PROJECT METRICS")
        lbl_metrics_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #FFFFFF; letter-spacing: 0.8px;")
        hdr_metrics.addWidget(lbl_metrics_title)
        hdr_metrics.addStretch()

        btn_change = QPushButton("Change")
        btn_change.setObjectName("SubtleLinkBtn")
        btn_change.setCursor(Qt.PointingHandCursor)
        btn_change.setToolTip("Change or load a new Primavera P6 schedule (.xer)")
        btn_change.clicked.connect(self.change_project_requested.emit)
        hdr_metrics.addWidget(btn_change)

        lay_metrics.addLayout(hdr_metrics)

        div2 = QFrame()
        div2.setFixedHeight(1)
        div2.setStyleSheet("background: rgba(255, 255, 255, 0.08); margin-bottom: 4px;")
        lay_metrics.addWidget(div2)

        # Metric keys
        metric_defs = [
            ("project", "Project", "None"),
            ("data_date", "Data Date", "None"),
            ("contract_fin", "Contract Finish", "None"),
            ("fcst_fin", "P6 Forecast", "None"),
            ("delay", "Critical Delay", "0 days"),
            ("bac", "Total BAC", "0.00 M EGP"),
            ("pv", "Planned Value", "0.00 M EGP"),
            ("ev", "Earned Value", "0.00 M EGP"),
            ("sv", "Schedule Var.", "0.00 M EGP"),
            ("spi", "SPI (EV/PV)", "1.00"),
        ]

        for m_key, m_label, default_val in metric_defs:
            row_f = QFrame()
            r_lay = QHBoxLayout(row_f)
            r_lay.setContentsMargins(2, 1, 2, 1)
            r_lay.setSpacing(4)

            k_lbl = QLabel(m_label)
            k_lbl.setStyleSheet("color: #94A3B8; font-size: 10.5px;")
            r_lay.addWidget(k_lbl)
            r_lay.addStretch()

            v_lbl = QLabel(default_val)
            v_lbl.setStyleSheet("color: #FFFFFF; font-size: 10.5px; font-weight: 600; font-family: 'Consolas', 'Segoe UI Mono', monospace;")
            r_lay.addWidget(v_lbl)

            self.metric_labels[m_key] = v_lbl
            lay_metrics.addWidget(row_f)

        main_lay.addWidget(card_metrics)
        main_lay.addStretch(1)

    def _layers_all_on(self):
        for sw in self.layer_switches.values():
            sw.setChecked(True)

    def _layers_all_off(self):
        for sw in self.layer_switches.values():
            sw.setChecked(False)

    def update_metrics(self, data: Optional[Dict[str, Any]]):
        """Updates the live metrics readout from analytics state."""
        if not data:
            for lbl in self.metric_labels.values():
                lbl.setText("—")
            return

        proj_name = str(data.get("project_name") or "HAP Town")
        if len(proj_name) > 14:
            proj_name = proj_name[:12] + ".."

        self.metric_labels["project"].setText(proj_name)
        self.metric_labels["data_date"].setText(str(data.get("data_date") or "—"))
        self.metric_labels["contract_fin"].setText(str(data.get("contract_finish") or "—"))
        self.metric_labels["fcst_fin"].setText(str(data.get("forecast_finish") or "—"))

        var_days = data.get("variance_days", 0)
        if var_days < 0:
            self.metric_labels["delay"].setText(f"+{abs(var_days)}d late")
            self.metric_labels["delay"].setStyleSheet("color: #EF4444; font-size: 10.5px; font-weight: 700;")
        else:
            self.metric_labels["delay"].setText(f"{var_days}d")
            self.metric_labels["delay"].setStyleSheet("color: #10B981; font-size: 10.5px; font-weight: 600;")

        # Extract EVM metrics directly from data or fallback to kpis dict
        kpis = data.get("kpis", {}) if isinstance(data.get("kpis"), dict) else {}
        bac_val = float(data.get("bac") if data.get("bac") is not None else kpis.get("bac", 0.0))
        pv_val = float(data.get("pv") if data.get("pv") is not None else kpis.get("pv", 0.0))
        ev_val = float(data.get("ev") if data.get("ev") is not None else kpis.get("ev", 0.0))
        sv_val = float(data.get("sv") if data.get("sv") is not None else kpis.get("sv", 0.0))
        spi_val = float(data.get("spi") if data.get("spi") is not None else kpis.get("spi", 1.0))

        bac = bac_val / 1e6
        pv = pv_val / 1e6
        ev = ev_val / 1e6
        sv = sv_val / 1e6
        spi = spi_val

        self.metric_labels["bac"].setText(f"{bac:.2f}M EGP")
        self.metric_labels["pv"].setText(f"{pv:.2f}M EGP")
        self.metric_labels["ev"].setText(f"{ev:.2f}M EGP")
        self.metric_labels["sv"].setText(f"{sv:.2f}M EGP")

        spi_str = f"{spi:.2f}"
        self.metric_labels["spi"].setText(spi_str)
        if spi < 0.8:
            self.metric_labels["spi"].setStyleSheet("color: #EF4444; font-size: 10.5px; font-weight: 700;")
        elif spi < 1.0:
            self.metric_labels["spi"].setStyleSheet("color: #F59E0B; font-size: 10.5px; font-weight: 700;")
        else:
            self.metric_labels["spi"].setStyleSheet("color: #10B981; font-size: 10.5px; font-weight: 700;")
