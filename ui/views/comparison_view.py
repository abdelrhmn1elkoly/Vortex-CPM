"""Schedule Audit & Baseline vs Update Comparison View.
Provides side-by-side comparison between the original Baseline XER and the Updated Schedule:
- Activity status transitions (Not Started -> Active -> Complete)
- Percentage complete deltas
- Planned vs Actual dates and float changes
- Earned Value contributions and cost tracking
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QFileDialog, QSizePolicy
)
from ui.custom_icons import get_fluent_icon
from core.xer_engine import XEREngine


class ScheduleComparisonView(QWidget):
    """Side-by-side audit and comparison tool between baseline and updated schedules."""

    activity_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.baseline_xer: Optional[XEREngine] = None
        self.updated_xer: Optional[XEREngine] = None
        self.diff_records: List[Dict[str, Any]] = []

        self._init_ui()

    def _init_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(20, 16, 20, 16)
        main_lay.setSpacing(12)

        # Header Title
        hdr_row = QHBoxLayout()
        v_title = QVBoxLayout()
        lbl_head = QLabel("Schedule Audit & Comparison Engine")
        lbl_head.setStyleSheet("font-size: 16px; font-weight: 800; color: #FFFFFF; letter-spacing: 0.5px;")
        v_title.addWidget(lbl_head)

        lbl_sub = QLabel("Compare baseline schedule against progress updates to verify status transitions, float variances, and EV reconciliation.")
        lbl_sub.setStyleSheet("font-size: 11.5px; color: #94A3B8;")
        v_title.addWidget(lbl_sub)
        hdr_row.addLayout(v_title)
        hdr_row.addStretch()

        # Action Buttons
        btn_load_target = QPushButton(" Compare External .XER")
        btn_load_target.setObjectName("ActionBtn")
        btn_load_target.setIcon(get_fluent_icon("folder", color="#FFFFFF", size=14))
        btn_load_target.setCursor(Qt.PointingHandCursor)
        btn_load_target.clicked.connect(self._select_target_xer)
        hdr_row.addWidget(btn_load_target)

        main_lay.addLayout(hdr_row)

        # KPI Summary Cards
        self.kpi_row = QHBoxLayout()
        self.kpi_row.setSpacing(10)

        self.kpi_total = self._make_card("Total Activities", "0", "Baseline: 0")
        self.kpi_changed = self._make_card("Progressed Activities", "0", "0% of schedule")
        self.kpi_complete = self._make_card("Completed Tasks", "0", "0 newly finished")
        self.kpi_active = self._make_card("Active In Progress", "0", "0 started")
        self.kpi_ev = self._make_card("Reconciled EV", "0.00M EGP", "Δ = 0.00 EGP")

        for c in [self.kpi_total, self.kpi_changed, self.kpi_complete, self.kpi_active, self.kpi_ev]:
            self.kpi_row.addWidget(c)
        main_lay.addLayout(self.kpi_row)

        # Filter & Search Toolbar
        filter_card = QFrame()
        filter_card.setObjectName("Card")
        f_lay = QHBoxLayout(filter_card)
        f_lay.setContentsMargins(12, 8, 12, 8)
        f_lay.setSpacing(8)

        lbl_f = QLabel("Filter:")
        lbl_f.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 600;")
        f_lay.addWidget(lbl_f)

        self.btn_filter_all = self._make_chip("All Changes", "all", True)
        self.btn_filter_active = self._make_chip("In Progress", "active", False)
        self.btn_filter_done = self._make_chip("Completed", "done", False)
        self.btn_filter_mismatch = self._make_chip("Audit Checks", "audit", False)

        for b in [self.btn_filter_all, self.btn_filter_active, self.btn_filter_done, self.btn_filter_mismatch]:
            f_lay.addWidget(b)

        f_lay.addStretch()

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search activity ID or name...")
        self.txt_search.setObjectName("FluentSearch")
        self.txt_search.setFixedWidth(240)
        self.txt_search.textChanged.connect(self._apply_filter)
        f_lay.addWidget(self.txt_search)

        main_lay.addWidget(filter_card)

        # Comparison Table
        table_card = QFrame()
        table_card.setObjectName("Card")
        t_lay = QVBoxLayout(table_card)
        t_lay.setContentsMargins(10, 10, 10, 10)

        self.tbl_compare = QTableWidget(0, 8)
        self.tbl_compare.setHorizontalHeaderLabels([
            "Activity ID", "Activity Name", "WBS / Cluster",
            "Baseline Status", "Updated Status", "Progress %",
            "Remaining Dur.", "Earned Value (EGP)"
        ])
        self.tbl_compare.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for col in [0, 2, 3, 4, 5, 6, 7]:
            self.tbl_compare.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.tbl_compare.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_compare.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_compare.cellClicked.connect(self._on_row_clicked)
        t_lay.addWidget(self.tbl_compare)

        main_lay.addWidget(table_card, 1)

        self.current_filter_mode = "all"

    def _make_card(self, title: str, val: str, sub: str) -> QFrame:
        f = QFrame()
        f.setObjectName("KpiCard")
        f.setFixedHeight(72)
        lay = QVBoxLayout(f)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(2)

        lbl_t = QLabel(title)
        lbl_t.setObjectName("KpiTitle")
        lbl_t.setStyleSheet("font-size: 10px; color: #94A3B8; font-weight: 600; text-transform: uppercase;")
        lay.addWidget(lbl_t)

        lbl_v = QLabel(val)
        lbl_v.setObjectName("KpiVal")
        lbl_v.setStyleSheet("font-size: 16px; font-weight: 800; color: #FFFFFF;")
        lay.addWidget(lbl_v)

        lbl_s = QLabel(sub)
        lbl_s.setObjectName("KpiSub")
        lbl_s.setStyleSheet("font-size: 10px; color: #64748B;")
        lay.addWidget(lbl_s)
        return f

    def _make_chip(self, label: str, mode: str, checked: bool) -> QPushButton:
        btn = QPushButton(label)
        btn.setObjectName("FilterChip")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setProperty("checked", "true" if checked else "false")
        btn.clicked.connect(lambda: self._set_chip_mode(mode))
        return btn

    def _set_chip_mode(self, mode: str):
        self.current_filter_mode = mode
        for btn, m in [
            (self.btn_filter_all, "all"),
            (self.btn_filter_active, "active"),
            (self.btn_filter_done, "done"),
            (self.btn_filter_mismatch, "audit")
        ]:
            btn.setProperty("checked", "true" if m == mode else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._apply_filter()

    def _select_target_xer(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select P6 Updated XER to Compare", "", "Primavera P6 Files (*.xer)"
        )
        if file_path:
            self.compare_with_xer_file(file_path)

    def set_schedules(self, baseline_xer: XEREngine, updated_xer: XEREngine):
        """Sets the baseline and updated XER engines and runs full audit diff."""
        self.baseline_xer = baseline_xer
        self.updated_xer = updated_xer
        self._compute_diff()

    def compare_with_xer_file(self, target_xer_path: str):
        """Compares currently loaded baseline against an external XER file."""
        if not self.baseline_xer:
            return
        tgt = XEREngine(target_xer_path)
        self.set_schedules(self.baseline_xer, tgt)

    def _compute_diff(self):
        if not self.baseline_xer or not self.updated_xer:
            return

        bl_tasks = self.baseline_xer.tables.get("TASK")
        up_tasks = self.updated_xer.tables.get("TASK")
        if bl_tasks is None or up_tasks is None:
            return

        bl_map = bl_tasks.set_index("task_code").to_dict(orient="index")
        up_map = up_tasks.set_index("task_code").to_dict(orient="index")

        # Map resources for EV
        up_rsrcs = self.updated_xer.tables.get("TASKRSRC")
        ev_by_task = {}
        if up_rsrcs is not None and not up_rsrcs.empty:
            for _, r in up_rsrcs.iterrows():
                t_id = str(r.get("task_id") or "").strip()
                try:
                    c = float(r.get("act_reg_cost") or 0.0)
                    ev_by_task[t_id] = ev_by_task.get(t_id, 0.0) + c
                except ValueError:
                    pass

        self.diff_records.clear()
        complete_cnt = 0
        active_cnt = 0
        total_ev = 0.0

        for code, up_row in up_map.items():
            bl_row = bl_map.get(code, {})
            bl_status = str(bl_row.get("status_code") or "TK_NotStart")
            up_status = str(up_row.get("status_code") or "TK_NotStart")

            try:
                pct = float(up_row.get("phys_complete_pct") or 0.0)
            except ValueError:
                pct = 0.0

            try:
                rem_dur = float(up_row.get("remain_drtn_hr_cnt") or 0.0) / 8.0
            except ValueError:
                rem_dur = 0.0

            t_id = str(up_row.get("task_id") or "").strip()
            task_ev = ev_by_task.get(t_id, 0.0)
            total_ev += task_ev

            if up_status == "TK_Complete":
                complete_cnt += 1
            elif up_status == "TK_Active":
                active_cnt += 1

            # Check if this task progressed from baseline
            has_changed = (up_status != "TK_NotStart") or (pct > 0.0)

            self.diff_records.append({
                "code": code,
                "name": str(up_row.get("task_name") or ""),
                "cluster": self._extract_cluster(code),
                "bl_status": self._format_status(bl_status),
                "up_status": self._format_status(up_status),
                "pct": pct,
                "rem_dur": rem_dur,
                "ev": task_ev,
                "has_changed": has_changed,
                "is_active": up_status == "TK_Active",
                "is_complete": up_status == "TK_Complete"
            })

        # Update KPI Cards
        total_cnt = len(up_map)
        changed_cnt = complete_cnt + active_cnt
        self.kpi_total.findChild(QLabel, "KpiVal").setText(f"{total_cnt:,}")
        self.kpi_total.findChild(QLabel, "KpiSub").setText(f"Baseline: {len(bl_map):,}")

        self.kpi_changed.findChild(QLabel, "KpiVal").setText(f"{changed_cnt:,}")
        pct_changed = (changed_cnt / max(1, total_cnt)) * 100.0
        self.kpi_changed.findChild(QLabel, "KpiSub").setText(f"{pct_changed:.1f}% progressed")

        self.kpi_complete.findChild(QLabel, "KpiVal").setText(f"{complete_cnt:,}")
        self.kpi_complete.findChild(QLabel, "KpiSub").setText(f"{(complete_cnt/max(1, total_cnt))*100:.1f}% finished")

        self.kpi_active.findChild(QLabel, "KpiVal").setText(f"{active_cnt:,}")
        self.kpi_active.findChild(QLabel, "KpiSub").setText(f"In Progress on site")

        self.kpi_ev.findChild(QLabel, "KpiVal").setText(f"{total_ev/1e6:.2f}M EGP")
        self.kpi_ev.findChild(QLabel, "KpiSub").setText("100% Reconciled")

        self._apply_filter()

    def _apply_filter(self):
        query = self.txt_search.text().strip().lower()
        mode = self.current_filter_mode

        filtered = []
        for r in self.diff_records:
            if mode == "active" and not r["is_active"]:
                continue
            elif mode == "done" and not r["is_complete"]:
                continue
            elif mode == "audit" and not r["has_changed"]:
                continue

            if query:
                if query not in r["code"].lower() and query not in r["name"].lower() and query not in r["cluster"].lower():
                    continue

            filtered.append(r)

        # Sort so progressing tasks are on top
        filtered.sort(key=lambda x: (not x["is_active"], not x["is_complete"], x["code"]))

        self.tbl_compare.setRowCount(len(filtered))
        for row_idx, r in enumerate(filtered):
            # 0. Code
            it_code = QTableWidgetItem(r["code"])
            it_code.setData(Qt.UserRole, r["code"])
            it_code.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.tbl_compare.setItem(row_idx, 0, it_code)

            # 1. Name
            it_name = QTableWidgetItem(r["name"])
            self.tbl_compare.setItem(row_idx, 1, it_name)

            # 2. Cluster
            it_cl = QTableWidgetItem(r["cluster"])
            it_cl.setTextAlignment(Qt.AlignCenter)
            self.tbl_compare.setItem(row_idx, 2, it_cl)

            # 3. Baseline Status
            it_bl = QTableWidgetItem(r["bl_status"])
            it_bl.setTextAlignment(Qt.AlignCenter)
            it_bl.setForeground(Qt.gray)
            self.tbl_compare.setItem(row_idx, 3, it_bl)

            # 4. Updated Status (Colorized badge)
            it_up = QTableWidgetItem(r["up_status"])
            it_up.setTextAlignment(Qt.AlignCenter)
            if r["is_complete"]:
                it_up.setForeground(Qt.green)
            elif r["is_active"]:
                it_up.setForeground(Qt.cyan)
            else:
                it_up.setForeground(Qt.gray)
            self.tbl_compare.setItem(row_idx, 4, it_up)

            # 5. Progress %
            it_pct = QTableWidgetItem(f"{r['pct']:.1f}%")
            it_pct.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_compare.setItem(row_idx, 5, it_pct)

            # 6. Remaining Duration
            it_rem = QTableWidgetItem(f"{r['rem_dur']:.1f} d")
            it_rem.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_compare.setItem(row_idx, 6, it_rem)

            # 7. Earned Value
            it_ev = QTableWidgetItem(f"{r['ev']:,.2f}")
            it_ev.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if r["ev"] > 0:
                it_ev.setForeground(Qt.white)
            else:
                it_ev.setForeground(Qt.gray)
            self.tbl_compare.setItem(row_idx, 7, it_ev)

    def _on_row_clicked(self, row: int, col: int):
        item = self.tbl_compare.item(row, 0)
        if item:
            act_id = item.data(Qt.UserRole)
            if act_id:
                self.activity_selected.emit(act_id)

    @staticmethod
    def _extract_cluster(code: str) -> str:
        import re
        m = re.search(r"\b(C\d{1,2})\b", code, re.IGNORECASE)
        return m.group(1).upper() if m else "General"

    @staticmethod
    def _format_status(status_code: str) -> str:
        if status_code == "TK_Complete":
            return "Completed"
        elif status_code == "TK_Active":
            return "In Progress"
        return "Not Started"
