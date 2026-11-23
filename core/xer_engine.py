"""Primavera P6 XER Schedule File Engine.
Handles high-fidelity parsing, modification, progress updates, and serialization of P6 .XER files.
"""

from __future__ import annotations
import os
import re
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np


class XEREngine:
    """Robust parser, modifier, and serializer for Oracle Primavera P6 .XER files."""

    def __init__(self, xer_path: Optional[str] = None):
        self.xer_path = xer_path
        self.header_lines: List[str] = []
        self.tables: Dict[str, pd.DataFrame] = {}
        self.table_order: List[str] = []
        self.table_fields: Dict[str, List[str]] = {}
        self.encoding: str = "cp1252"

        if xer_path and os.path.exists(xer_path):
            self.load(xer_path)

    def load(self, xer_path: str):
        """Loads and parses an existing .XER file into in-memory pandas DataFrames."""
        self.xer_path = xer_path
        self.header_lines = []
        self.tables = {}
        self.table_order = []
        self.table_fields = {}

        # Detect or default to cp1252
        for enc in ("cp1252", "utf-8", "latin-1"):
            try:
                with open(xer_path, "r", encoding=enc, errors="replace") as f:
                    first_line = f.readline()
                    if "ERMHDR" in first_line:
                        self.encoding = enc
                        break
            except Exception:
                continue

        curr_t: Optional[str] = None
        fields: List[str] = []
        rows: List[List[str]] = []

        with open(self.xer_path, "r", encoding=self.encoding, errors="replace") as f:
            for line in f:
                raw = line.rstrip("\r\n")
                if raw.startswith("ERMHDR"):
                    self.header_lines.append(raw)
                elif raw.startswith("%T\t"):
                    if curr_t is not None:
                        self.tables[curr_t] = pd.DataFrame(rows, columns=fields)
                    curr_t = raw.split("\t")[1]
                    if curr_t not in self.table_order:
                        self.table_order.append(curr_t)
                    fields, rows = [], []
                elif raw.startswith("%F\t"):
                    fields = raw.split("\t")[1:]
                    self.table_fields[curr_t] = fields
                elif raw.startswith("%R\t"):
                    vals = raw.split("\t")[1:]
                    # Pad or truncate to match field definition length
                    if len(vals) < len(fields):
                        vals = vals + [""] * (len(fields) - len(vals))
                    elif len(vals) > len(fields):
                        vals = vals[:len(fields)]
                    rows.append(vals)

            if curr_t is not None:
                self.tables[curr_t] = pd.DataFrame(rows, columns=fields)

        # Default header if file was empty or missing header
        if not self.header_lines:
            self.header_lines.append("ERMHDR\t25.12\t2026-10-29\tProject\tADMIN")

    def get_project_summary(self) -> Dict[str, Any]:
        """Extracts key project metadata from PROJECT and CALENDAR tables."""
        info = {
            "project_name": "Primavera Project",
            "project_short_name": "",
            "data_date": "",
            "plan_start_date": "",
            "plan_end_date": "",
            "task_count": 0,
            "resource_count": 0,
            "pred_count": 0
        }

        if "PROJECT" in self.tables and not self.tables["PROJECT"].empty:
            proj_df = self.tables["PROJECT"]
            first_row = proj_df.iloc[0]
            info["project_name"] = str(first_row.get("proj_short_name") or first_row.get("project_name") or "Primavera Project")
            info["project_short_name"] = str(first_row.get("proj_short_name") or "")
            info["data_date"] = str(first_row.get("last_recalc_date") or "")[:10]
            info["plan_start_date"] = str(first_row.get("plan_start_date") or "")[:10]
            info["plan_end_date"] = str(first_row.get("plan_end_date") or "")[:10]

        if "TASK" in self.tables:
            info["task_count"] = len(self.tables["TASK"])
        if "TASKRSRC" in self.tables:
            info["resource_count"] = len(self.tables["TASKRSRC"])
        if "TASKPRED" in self.tables:
            info["pred_count"] = len(self.tables["TASKPRED"])

        return info

    def apply_progress_updates(
        self,
        progress_map: Dict[str, Dict[str, Any]],
        data_date: str,
        default_work_day_hours: float = 8.0,
        auto_progress_ep: bool = True,
        auto_progress_milestones: bool = True
    ) -> Dict[str, int]:
        """
        Updates TASK and TASKRSRC tables based on the normalized progress map and P6 CPM rules.
        
        Includes the industry-standard As-Planned E&P Auto-Progression Rule:
        - Paperwork / Engineering & Procurement activities (HT.EN.*, HT.PR.*) planned before Data Date
          are automatically progressed as complete as-planned (act_start=target_start, act_end=target_end,
          remain_dur=0) so non-critical procurement paperwork does not falsely gate site construction.
        - Start-up & commencement milestones (HT.KD.*) planned before Data Date are set complete as planned.
        - Site construction tasks (HT.CO.*) are updated with physical % complete, actual start/finish dates,
          and remaining durations from site sheets.
        - TASKRSRC costs and quantities are proportionally recalculated:
          act_reg_cost = round(target_cost * (pct / 100), 2)
          remain_cost = round(target_cost - act_reg_cost, 2)
        """
        stats = {
            "matched_tasks": 0,
            "completed_tasks": 0,
            "active_tasks": 0,
            "not_started_tasks": 0,
            "ep_auto_completed": 0,
            "milestones_auto_completed": 0,
            "unmatched_progress_keys": 0
        }

        if "TASK" not in self.tables:
            return stats

        # Update PROJECT last recalc date / data date
        dd_clean = data_date[:10]
        if "PROJECT" in self.tables and not self.tables["PROJECT"].empty:
            dd_str = f"{dd_clean} 00:00:00"
            if "last_recalc_date" in self.tables["PROJECT"].columns:
                self.tables["PROJECT"]["last_recalc_date"] = dd_str
            if "scd_end_date" in self.tables["PROJECT"].columns:
                self.tables["PROJECT"]["scd_end_date"] = f"{dd_clean} 16:00:00"

        tasks = self.tables["TASK"].copy()
        pct_by_task_id: Dict[str, float] = {}
        matched_keys = set()

        def fmt_dt(val: Any, default_time: str = "08:00") -> str:
            if not val or pd.isna(val) or str(val).strip() in ("", "-", "None", "NaT"):
                return ""
            s = str(val).strip()[:10]
            return f"{s} {default_time}"

        # Activity prefixes
        ep_prefixes = ("HT.EN.", "HT.PR.")
        kd_prefixes = ("HT.KD.",)

        for idx, row in tasks.iterrows():
            t_code = str(row.get("task_code") or "").strip()
            t_id = str(row.get("task_id") or "").strip()
            t_name = str(row.get("task_name") or "")

            target_dur_hr = float(row.get("target_drtn_hr_cnt") or 0.0)
            target_work = float(row.get("target_work_qty") or 0.0)
            t_start = str(row.get("target_start_date") or "")
            t_end = str(row.get("target_end_date") or "")
            t_end_date_only = t_end[:10]

            # 1. Engineering & Procurement As-Planned Auto-Progression
            if auto_progress_ep and t_code.startswith(ep_prefixes) and t_code not in progress_map:
                if t_end_date_only and t_end_date_only <= dd_clean:
                    stats["ep_auto_completed"] += 1
                    stats["completed_tasks"] += 1
                    tasks.at[idx, "status_code"] = "TK_Complete"
                    tasks.at[idx, "phys_complete_pct"] = "100"
                    tasks.at[idx, "remain_drtn_hr_cnt"] = "0"
                    tasks.at[idx, "act_work_qty"] = f"{target_work:g}"
                    tasks.at[idx, "remain_work_qty"] = "0"
                    tasks.at[idx, "act_start_date"] = t_start or f"{dd_clean} 08:00"
                    tasks.at[idx, "act_end_date"] = t_end or f"{dd_clean} 16:00"
                    tasks.at[idx, "restart_date"] = ""
                    tasks.at[idx, "reend_date"] = ""
                    pct_by_task_id[t_id] = 100.0
                    continue

            # 2. Milestones Auto-Progression (Commencement & Mobilization Gates)
            if auto_progress_milestones and t_code.startswith(kd_prefixes) and t_code not in progress_map:
                # Mark start-up milestones as complete on their contract/target date
                is_startup_gate = any(m_id in t_code for m_id in ["005", "010", "015", "035", "045"]) or "HT.KD.MB." in t_code
                if is_startup_gate and t_end_date_only and t_end_date_only <= dd_clean:
                    stats["milestones_auto_completed"] += 1
                    stats["completed_tasks"] += 1
                    tasks.at[idx, "status_code"] = "TK_Complete"
                    tasks.at[idx, "phys_complete_pct"] = "100"
                    tasks.at[idx, "remain_drtn_hr_cnt"] = "0"
                    tasks.at[idx, "act_work_qty"] = "0"
                    tasks.at[idx, "remain_work_qty"] = "0"
                    tasks.at[idx, "act_start_date"] = t_start or f"{dd_clean} 08:00"
                    tasks.at[idx, "act_end_date"] = t_end or f"{dd_clean} 16:00"
                    tasks.at[idx, "restart_date"] = ""
                    tasks.at[idx, "reend_date"] = ""
                    pct_by_task_id[t_id] = 100.0
                    continue

            # 3. Direct Progress from Site Map (e.g. Construction Tasks HT.CO.*)
            if t_code in progress_map:
                matched_keys.add(t_code)
                stats["matched_tasks"] += 1
                info = progress_map[t_code]
                pct = max(0.0, min(100.0, float(info.get("pct") or 0.0)))
                st_val = info.get("start")
                fn_val = info.get("finish")
                rem_dur = info.get("remain_dur")

                # P6 Percentage Governing Rule: physical % complete strictly dictates task status
                if pct >= 100.0:
                    stats["completed_tasks"] += 1
                    tasks.at[idx, "status_code"] = "TK_Complete"
                    tasks.at[idx, "phys_complete_pct"] = "100"
                    tasks.at[idx, "remain_drtn_hr_cnt"] = "0"
                    tasks.at[idx, "act_work_qty"] = f"{target_work:g}"
                    tasks.at[idx, "remain_work_qty"] = "0"
                    act_st = fmt_dt(st_val, "08:00") or t_start or f"{dd_clean} 08:00"
                    act_fn = fmt_dt(fn_val, "16:00") or t_end or f"{dd_clean} 16:00"
                    tasks.at[idx, "act_start_date"] = act_st
                    tasks.at[idx, "act_end_date"] = act_fn
                    tasks.at[idx, "restart_date"] = ""
                    tasks.at[idx, "reend_date"] = ""
                    pct_by_task_id[t_id] = 100.0
                elif pct > 0.0:
                    stats["active_tasks"] += 1
                    tasks.at[idx, "status_code"] = "TK_Active"
                    tasks.at[idx, "phys_complete_pct"] = f"{pct:g}"
                    if rem_dur is not None and float(rem_dur) >= 0:
                        rem_hr = float(rem_dur) * default_work_day_hours
                    else:
                        rem_hr = round(target_dur_hr * (1.0 - pct / 100.0), 1)
                    tasks.at[idx, "remain_drtn_hr_cnt"] = f"{rem_hr:g}"
                    tasks.at[idx, "act_work_qty"] = f"{round(target_work * (pct / 100.0), 2):g}"
                    tasks.at[idx, "remain_work_qty"] = f"{round(target_work * (1.0 - pct / 100.0), 2):g}"
                    act_st = fmt_dt(st_val, "08:00") or t_start or f"{dd_clean} 08:00"
                    tasks.at[idx, "act_start_date"] = act_st
                    tasks.at[idx, "act_end_date"] = ""
                    tasks.at[idx, "restart_date"] = f"{dd_clean} 08:00"
                    pct_by_task_id[t_id] = pct
                else:
                    stats["not_started_tasks"] += 1
                    tasks.at[idx, "status_code"] = "TK_NotStart"
                    tasks.at[idx, "phys_complete_pct"] = "0"
                    tasks.at[idx, "remain_drtn_hr_cnt"] = f"{target_dur_hr:g}"
                    tasks.at[idx, "act_work_qty"] = "0"
                    tasks.at[idx, "remain_work_qty"] = f"{target_work:g}"
                    tasks.at[idx, "act_start_date"] = ""
                    tasks.at[idx, "act_end_date"] = ""
                    pct_by_task_id[t_id] = 0.0
            else:
                # Retain existing progress if present in baseline
                try:
                    pct_by_task_id[t_id] = float(row.get("phys_complete_pct") or 0.0)
                except ValueError:
                    pct_by_task_id[t_id] = 0.0
                if row.get("status_code") == "TK_Complete":
                    stats["completed_tasks"] += 1
                elif row.get("status_code") == "TK_Active":
                    stats["active_tasks"] += 1
                else:
                    stats["not_started_tasks"] += 1

        stats["unmatched_progress_keys"] = len(progress_map) - len(matched_keys)
        self.tables["TASK"] = tasks

        # 4. Update TASKRSRC costs and quantities with exact 2-decimal precision
        if "TASKRSRC" in self.tables and not self.tables["TASKRSRC"].empty:
            rsrcs = self.tables["TASKRSRC"].copy()
            for idx, r_row in rsrcs.iterrows():
                t_id = str(r_row.get("task_id") or "").strip()
                pct_dec = pct_by_task_id.get(t_id, 0.0) / 100.0
                try:
                    t_cost = float(r_row.get("target_cost") or 0.0)
                except ValueError:
                    t_cost = 0.0
                try:
                    t_qty = float(r_row.get("target_qty") or 0.0)
                except ValueError:
                    t_qty = 0.0

                act_cost = round(t_cost * pct_dec, 2)
                rem_cost = round(t_cost - act_cost, 2)
                act_qty = round(t_qty * pct_dec, 2)
                rem_qty = round(t_qty - act_qty, 2)

                rsrcs.at[idx, "act_reg_cost"] = f"{act_cost:.2f}"
                rsrcs.at[idx, "remain_cost"] = f"{rem_cost:.2f}"
                rsrcs.at[idx, "act_reg_qty"] = f"{act_qty:.2f}"
                rsrcs.at[idx, "remain_qty"] = f"{rem_qty:.2f}"
                if pct_dec >= 1.0:
                    rsrcs.at[idx, "restart_date"] = ""
                    rsrcs.at[idx, "reend_date"] = ""
                elif pct_dec > 0.0:
                    rsrcs.at[idx, "restart_date"] = f"{dd_clean} 08:00"

            self.tables["TASKRSRC"] = rsrcs

        return stats

        return stats

    def export_xer(self, out_path: str):
        """Exports the in-memory tables back into a standard Primavera P6 .XER file."""
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w", encoding=self.encoding, errors="replace", newline="\r\n") as f:
            for h in self.header_lines:
                f.write(h + "\r\n")
            for t_name in self.table_order:
                if t_name not in self.tables:
                    continue
                f.write(f"%T\t{t_name}\r\n")
                fields = self.table_fields.get(t_name, list(self.tables[t_name].columns))
                f.write("%F\t" + "\t".join(fields) + "\r\n")
                df = self.tables[t_name]
                for _, row in df.iterrows():
                    vals = [str(row[c]) if pd.notna(row.get(c)) else "" for c in fields]
                    f.write("%R\t" + "\t".join(vals) + "\r\n")
            f.write("%E\r\n")
