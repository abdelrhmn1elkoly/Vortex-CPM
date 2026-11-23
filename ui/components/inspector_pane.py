"""WinUI 3 Master-Detail Inspector Pane for Vortex Controls.
Directly replicates the right-hand inspection card from FluentDL,
providing live deep-dive audits for selected activities and clusters.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QSizePolicy
)
from ui.custom_icons import get_fluent_icon


class InspectorPane(QFrame):
    """Right-side Master-Detail Inspector card for activities and clusters."""

    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("InspectorCard")
        self.setFixedWidth(310)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.current_data: Optional[Dict[str, Any]] = None
        self.current_type: str = "none"  # "none", "activity", "cluster"

        self._init_ui()
        self.show_empty()

    def _init_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(16, 14, 16, 14)
        main_lay.setSpacing(10)

        # Header bar matching Vortex PT ELEMENT PROPERTIES
        header_bar = QHBoxLayout()
        header_bar.setContentsMargins(0, 0, 0, 0)
        header_bar.setSpacing(8)

        icon_target = QLabel()
        icon_target.setPixmap(get_fluent_icon("inspector", color="#60CDFF", size=18).pixmap(18, 18))
        header_bar.addWidget(icon_target)

        lbl_head = QLabel("ACTIVITY PROPERTIES")
        lbl_head.setObjectName("InspectorTitle")
        lbl_head.setStyleSheet("font-size: 13px; font-weight: 800; color: #FFFFFF; letter-spacing: 0.8px;")
        header_bar.addWidget(lbl_head)
        header_bar.addStretch()

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet("background: transparent; border: none; color: #9E9E9E; font-size: 13px; font-weight: bold; border-radius: 4px;")
        self.btn_close.clicked.connect(self.closed.emit)
        header_bar.addWidget(self.btn_close)

        main_lay.addLayout(header_bar)

        # Content Container (Scrollable)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("background: transparent; border: none;")

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.content_lay = QVBoxLayout(self.content_widget)
        self.content_lay.setContentsMargins(0, 4, 8, 4)
        self.content_lay.setSpacing(8)

        self.scroll.setWidget(self.content_widget)
        main_lay.addWidget(self.scroll)

    def clear_content(self):
        while self.content_lay.count():
            item = self.content_lay.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

    def show_empty(self):
        """Displays the authentic Vortex PT / FluentDL empty inspection state."""
        self.current_data = None
        self.current_type = "none"
        self.clear_content()

        self.content_lay.addStretch(1)

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setPixmap(get_fluent_icon("inspector", color="#60CDFF", size=42).pixmap(42, 42))
        self.content_lay.addWidget(icon_lbl)

        lbl_no = QLabel("Select Activity or Milestone")
        lbl_no.setAlignment(Qt.AlignCenter)
        lbl_no.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 700; margin-top: 10px; letter-spacing: 0.3px;")
        self.content_lay.addWidget(lbl_no)

        lbl_hint = QLabel("Click any element on the schedule tables or use the search bar above to view live CPM properties, float, and cost curves.")
        lbl_hint.setAlignment(Qt.AlignCenter)
        lbl_hint.setWordWrap(True)
        lbl_hint.setStyleSheet("color: #94A3B8; font-size: 11px; line-height: 16px; margin: 6px 14px;")
        self.content_lay.addWidget(lbl_hint)

        self.content_lay.addStretch(2)

    def inspect_activity(self, act: Dict[str, Any]):
        """Displays deep-dive schedule, float, and logic tie properties for an activity."""
        self.current_data = act
        self.current_type = "activity"
        self.clear_content()

        # 1. Top Badges Row
        badge_row = QHBoxLayout()
        badge_row.setContentsMargins(0, 0, 0, 0)

        act_id = act.get("act_id", "N/A")
        lbl_id = QLabel(act_id)
        lbl_id.setStyleSheet("background-color: #0078D4; color: #FFFFFF; font-weight: 700; font-size: 11px; padding: 3px 8px; border-radius: 4px;")
        badge_row.addWidget(lbl_id)

        status = act.get("status", "Not Started")
        st_color = "#107C41" if "comp" in status.lower() else ("#0078D4" if "prog" in status.lower() else "#64748B")
        lbl_st = QLabel(status)
        lbl_st.setStyleSheet(f"background-color: rgba(255,255,255,0.08); color: {st_color}; font-weight: 600; font-size: 11px; padding: 3px 8px; border-radius: 4px; border: 1px solid #383838;")
        badge_row.addWidget(lbl_st)
        badge_row.addStretch()

        self.content_lay.addLayout(badge_row)

        # 2. Activity Name
        lbl_name = QLabel(act.get("act_name", "Activity Name"))
        lbl_name.setWordWrap(True)
        lbl_name.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 700; margin: 4px 0;")
        self.content_lay.addWidget(lbl_name)

        # 3. Schedule Dates Card
        self._add_section_header("Schedule Dates & Float")
        dates_frame = self._create_card_container()
        d_lay = QVBoxLayout(dates_frame)
        d_lay.setContentsMargins(10, 8, 10, 8)
        d_lay.setSpacing(6)

        d_lay.addLayout(self._make_prop_row("Baseline Start:", act.get("target_start", "-")[:10]))
        d_lay.addLayout(self._make_prop_row("Baseline Finish:", act.get("bl_finish", "-")[:10]))
        d_lay.addLayout(self._make_prop_row("Actual / Forecast:", act.get("act_finish", act.get("bl_finish", "-"))[:10]))

        slip = act.get("late_days", 0)
        slip_text = f"+{slip} days (DELAY)" if slip > 0 else "0 days (ON TIME)"
        slip_color = "#DC2626" if slip > 0 else "#107C41"
        d_lay.addLayout(self._make_prop_row("Variance / Slip:", slip_text, val_color=slip_color))

        # Critical Path / Float Check
        total_float = act.get("total_float", 0)
        is_critical = total_float <= 0
        crit_text = f"{total_float}d (CRITICAL PATH)" if is_critical else f"{total_float}d (Non-Critical)"
        crit_color = "#DC2626" if is_critical else "#107C41"
        d_lay.addLayout(self._make_prop_row("Total Float:", crit_text, val_color=crit_color))

        self.content_lay.addWidget(dates_frame)

        # 4. Progress & Cost Card
        self._add_section_header("Progress & Earned Value")
        cost_frame = self._create_card_container()
        c_lay = QVBoxLayout(cost_frame)
        c_lay.setContentsMargins(10, 8, 10, 8)
        c_lay.setSpacing(6)

        pct = act.get("pct", 0.0)
        c_lay.addLayout(self._make_prop_row("Physical % Complete:", f"{pct:.1f}%"))
        c_lay.addLayout(self._make_prop_row("Cluster / Area:", act.get("cluster", "-")))
        c_lay.addLayout(self._make_prop_row("Discipline:", act.get("discipline", "-")))

        cost = act.get("target_cost", 0.0)
        if cost > 0:
            c_lay.addLayout(self._make_prop_row("Budget (BAC):", f"{cost:,.0f} EGP"))
            ev = cost * (pct / 100.0)
            c_lay.addLayout(self._make_prop_row("Earned Value (EV):", f"{ev:,.0f} EGP"))

        self.content_lay.addWidget(cost_frame)

        # 5. Logic Ties (Predecessors & Successors)
        preds = act.get("preds", [])
        succs = act.get("succs", [])

        self._add_section_header(f"Predecessors ({len(preds)})")
        if preds:
            p_frame = self._create_card_container()
            p_lay = QVBoxLayout(p_frame)
            p_lay.setContentsMargins(10, 8, 10, 8)
            p_lay.setSpacing(4)
            for p in preds:
                lbl_p = QLabel(f"• <b>{p.get('pred_id', '')}</b> ({p.get('type', 'FS')} {p.get('lag', 0)}d)")
                lbl_p.setStyleSheet("color: #CCCCCC; font-size: 11px;")
                p_lay.addWidget(lbl_p)
            self.content_lay.addWidget(p_frame)
        else:
            lbl_none = QLabel("No predecessors (Root Activity)")
            lbl_none.setStyleSheet("color: #64748B; font-size: 11px; padding-left: 4px;")
            self.content_lay.addWidget(lbl_none)

        self._add_section_header(f"Successors ({len(succs)})")
        if succs:
            s_frame = self._create_card_container()
            s_lay = QVBoxLayout(s_frame)
            s_lay.setContentsMargins(10, 8, 10, 8)
            s_lay.setSpacing(4)
            for s in succs:
                lbl_s = QLabel(f"• <b>{s.get('succ_id', '')}</b> ({s.get('type', 'FS')} {s.get('lag', 0)}d)")
                lbl_s.setStyleSheet("color: #CCCCCC; font-size: 11px;")
                s_lay.addWidget(lbl_s)
            self.content_lay.addWidget(s_frame)
        else:
            lbl_none_s = QLabel("No successors (End Milestone / Open End)")
            lbl_none_s.setStyleSheet("color: #64748B; font-size: 11px; padding-left: 4px;")
            self.content_lay.addWidget(lbl_none_s)

        self.content_lay.addStretch()

    def inspect_cluster(self, clust: Dict[str, Any]):
        """Displays cluster summary metrics and health audit."""
        self.current_data = clust
        self.current_type = "cluster"
        self.clear_content()

        # Header Badge
        badge_row = QHBoxLayout()
        lbl_id = QLabel(clust.get("cluster", "Cluster"))
        lbl_id.setStyleSheet("background-color: #0078D4; color: #FFFFFF; font-weight: 700; font-size: 12px; padding: 4px 10px; border-radius: 4px;")
        badge_row.addWidget(lbl_id)
        badge_row.addStretch()
        self.content_lay.addLayout(badge_row)

        lbl_name = QLabel(f"Cluster {clust.get('cluster')} Performance Breakdown")
        lbl_name.setWordWrap(True)
        lbl_name.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 700; margin: 4px 0;")
        self.content_lay.addWidget(lbl_name)

        # Performance Card
        self._add_section_header("Earned Value & Budget")
        c_frame = self._create_card_container()
        c_lay = QVBoxLayout(c_frame)
        c_lay.setContentsMargins(10, 8, 10, 8)
        c_lay.setSpacing(6)

        c_lay.addLayout(self._make_prop_row("Total Budget (BAC):", f"{clust.get('bac', 0)/1e6:.2f}M EGP"))
        c_lay.addLayout(self._make_prop_row("Project Weight:", f"{clust.get('weight', 0):.1f}%"))
        c_lay.addLayout(self._make_prop_row("Planned Progress:", f"{clust.get('planned_pct', 0):.1f}%"))
        c_lay.addLayout(self._make_prop_row("Actual Progress:", f"{clust.get('actual_pct', 0):.1f}%"))

        var = clust.get("variance_pct", 0.0)
        var_color = "#107C41" if var >= 0 else "#DC2626"
        c_lay.addLayout(self._make_prop_row("Progress Variance:", f"{var:+.1f}%", val_color=var_color))

        spi = clust.get("spi", 1.0)
        spi_color = "#107C41" if spi >= 0.98 else ("#D97706" if spi >= 0.85 else "#DC2626")
        c_lay.addLayout(self._make_prop_row("Schedule Index (SPI):", f"{spi:.2f}", val_color=spi_color))

        c_lay.addLayout(self._make_prop_row("Forecast Finish:", clust.get("fcst_finish", "-")[:10]))
        slip = clust.get("slip_days", 0)
        slip_color = "#DC2626" if slip > 0 else "#107C41"
        c_lay.addLayout(self._make_prop_row("Schedule Slip:", f"{slip} days", val_color=slip_color))

        self.content_lay.addWidget(c_frame)
        self.content_lay.addStretch()

    def _add_section_header(self, title: str):
        lbl = QLabel(title)
        lbl.setObjectName("InspectorSection")
        self.content_lay.addWidget(lbl)

    def _create_card_container(self) -> QFrame:
        f = QFrame()
        f.setStyleSheet("background-color: #252525; border: 1px solid #383838; border-radius: 6px;")
        return f

    def _make_prop_row(self, key: str, val: str, val_color: str = "#FFFFFF") -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        k_lbl = QLabel(key)
        k_lbl.setObjectName("InspectorPropKey")
        v_lbl = QLabel(val)
        v_lbl.setObjectName("InspectorPropVal")
        if val_color != "#FFFFFF":
            v_lbl.setStyleSheet(f"color: {val_color}; font-weight: 700; font-size: 12px;")
        row.addWidget(k_lbl)
        row.addStretch()
        row.addWidget(v_lbl)
        return row
