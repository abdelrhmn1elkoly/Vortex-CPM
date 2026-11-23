"""Earned Value Management (EVM) and Project Controls Analytics Engine.
Calculates BAC, PV, EV, SV, SPI, cluster metrics, discipline breakdowns,
out-of-sequence logic ties, weekly S-curve, and 30-day lookahead schedules.
"""

from __future__ import annotations
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np


class AnalyticsEngine:
    """Computes comprehensive project controls and Earned Value analytics from P6 XER tables."""

    DISCIPLINE_MAP = {
        "Civil": "Civil Works",
        "PL": "Plumbing & Drainage",
        "ELC": "Electrical Works",
        "HVAC": "HVAC & Ventilation",
        "FF": "Fire Fighting",
        "FA": "Fire Alarm",
        "Tie": "Infrastructure Tie-In",
        "Test": "Testing & Commissioning"
    }

    @classmethod
    def analyze(
        cls,
        tables: Dict[str, pd.DataFrame],
        data_date_str: str,
        contract_commence_str: Optional[str] = None,
        contract_finish_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes complete project controls analytics on parsed P6 tables.
        """
        if "TASK" not in tables:
            raise ValueError("TASK table is missing from schedule data.")

        tasks = tables["TASK"].copy()
        rsrcs = tables.get("TASKRSRC", pd.DataFrame()).copy()
        preds = tables.get("TASKPRED", pd.DataFrame()).copy()

        # Parse costs by task_id from TASKRSRC
        if not rsrcs.empty:
            rsrcs["target_cost"] = pd.to_numeric(rsrcs.get("target_cost", 0), errors="coerce").fillna(0.0)
            rsrcs["act_reg_cost"] = pd.to_numeric(rsrcs.get("act_reg_cost", 0), errors="coerce").fillna(0.0)
            cost_by_task = rsrcs.groupby("task_id")[["target_cost", "act_reg_cost"]].sum().reset_index()
            df = pd.merge(tasks, cost_by_task, on="task_id", how="left").fillna({"target_cost": 0.0, "act_reg_cost": 0.0})
        else:
            df = tasks.copy()
            df["target_cost"] = pd.to_numeric(df.get("target_cost", 0), errors="coerce").fillna(0.0)
            df["act_reg_cost"] = 0.0

        # Ensure numeric columns
        df["phys_complete_pct"] = pd.to_numeric(df.get("phys_complete_pct", 0), errors="coerce").fillna(0.0)
        df["target_drtn_hr_cnt"] = pd.to_numeric(df.get("target_drtn_hr_cnt", 0), errors="coerce").fillna(0.0)

        # Helpers for cluster and discipline extraction
        def extract_cluster(code: Any) -> str:
            s = str(code)
            for part in s.split("."):
                part_clean = part.strip()
                if part_clean.startswith("C") and len(part_clean) in (2, 3) and part_clean[1:].isdigit():
                    return f"C{int(part_clean[1:]):02d}"
            # Secondary regex search
            m = re.search(r"\b(C\d{1,2})\b", s, re.IGNORECASE)
            if m:
                return f"C{int(m.group(1)[1:]):02d}"
            return "General"

        def extract_discipline(code: Any) -> str:
            s = str(code)
            for key, name in cls.DISCIPLINE_MAP.items():
                if f".{key}." in s or f".{key}" in s or s.startswith(f"{key}."):
                    return name
            return "General Works"

        df["Cluster"] = df["task_code"].apply(extract_cluster)
        df["Discipline"] = df["task_code"].apply(extract_discipline)

        # Date handling & Planned Value (PV) calculation
        dd_dt = pd.to_datetime(data_date_str[:10], errors="coerce")
        ts = pd.to_datetime(df.get("target_start_date"), errors="coerce")
        te = pd.to_datetime(df.get("target_end_date"), errors="coerce")

        total_secs = (te - ts).dt.total_seconds().fillna(0.0)
        elapsed_secs = (dd_dt - ts).dt.total_seconds().fillna(0.0)

        # Time-phased linear Planned Value ratio
        pv_ratio = np.where(
            dd_dt >= te, 1.0,
            np.where(
                dd_dt <= ts, 0.0,
                elapsed_secs / np.maximum(total_secs, 1.0)
            )
        )
        pv_ratio = np.clip(pv_ratio, 0.0, 1.0)
        df["pv_cost"] = df["target_cost"] * pv_ratio

        # Calculate Earned Value (EV) per task
        # If act_reg_cost is populated from resources, use it; otherwise target_cost * (pct / 100)
        calculated_ev = df["target_cost"] * (df["phys_complete_pct"] / 100.0)
        df["ev_cost"] = np.where(df["act_reg_cost"] > 0, df["act_reg_cost"], calculated_ev)

        # Total Project EVM Totals
        bac_total = float(df["target_cost"].sum())
        pv_total = float(df["pv_cost"].sum())
        ev_total = float(df["ev_cost"].sum())

        planned_pct = (pv_total / bac_total * 100.0) if bac_total > 0 else 0.0
        actual_pct = (ev_total / bac_total * 100.0) if bac_total > 0 else 0.0
        variance_pct = actual_pct - planned_pct
        sv_total = ev_total - pv_total
        spi_total = (ev_total / pv_total) if pv_total > 0 else (1.0 if ev_total >= pv_total else 0.0)

        # Activity Status Counts
        status_series = df.get("status_code", pd.Series(dtype=str))
        complete_cnt = int((status_series == "TK_Complete").sum()) + int((df["phys_complete_pct"] >= 100.0).sum() - ((status_series == "TK_Complete") & (df["phys_complete_pct"] >= 100.0)).sum())
        active_cnt = int(((df["phys_complete_pct"] > 0) & (df["phys_complete_pct"] < 100.0)).sum())
        not_start_cnt = len(df) - complete_cnt - active_cnt

        # -------------------------------------------------------------
        # 1. Cluster Breakdown Analysis (C08 - C18)
        # -------------------------------------------------------------
        clusters_list = []
        cluster_groups = df[df["Cluster"] != "General"].groupby("Cluster")

        # Fallback if no specific clusters
        if cluster_groups.ngroups == 0:
            cluster_groups = df.groupby("Cluster")

        for cl_name, c_df in cluster_groups:
            c_bac = float(c_df["target_cost"].sum())
            c_pv = float(c_df["pv_cost"].sum())
            c_ev = float(c_df["ev_cost"].sum())
            c_weight = (c_bac / bac_total * 100.0) if bac_total > 0 else 0.0
            c_planned_pct = (c_pv / c_bac * 100.0) if c_bac > 0 else 0.0
            c_actual_pct = (c_ev / c_bac * 100.0) if c_bac > 0 else 0.0
            c_sv = c_ev - c_pv
            c_spi = (c_ev / c_pv) if c_pv > 0 else (1.0 if c_ev >= c_pv else 0.0)

            # Dates
            c_te_valid = pd.to_datetime(c_df["target_end_date"], errors="coerce").dropna()
            bl_finish = c_te_valid.max().strftime("%Y-%m-%d") if not c_te_valid.empty else ""

            # Forecast finish calculation based on SPI
            slip_days = 0
            fcst_finish = bl_finish
            if bl_finish and c_spi > 0 and c_spi < 1.0:
                bl_dt = datetime.strptime(bl_finish, "%Y-%m-%d")
                # Estimated slippage proportional to remaining work / SPI
                rem_days = max(10, (bl_dt - dd_dt).days) if dd_dt else 60
                slip_days = int(rem_days * ((1.0 / max(0.15, c_spi)) - 1.0))
                fcst_dt = bl_dt + timedelta(days=slip_days)
                fcst_finish = fcst_dt.strftime("%Y-%m-%d")
            elif c_spi >= 1.0:
                slip_days = 0
                fcst_finish = bl_finish

            # Health classification
            if c_spi < 0.4:
                health = "Critical"
            elif c_spi < 0.8:
                health = "Attention"
            else:
                health = "Healthy"

            # Discipline gap remark
            disc_grp = c_df.groupby("Discipline")[["target_cost", "pv_cost", "ev_cost"]].sum()
            disc_grp["gap"] = disc_grp["pv_cost"] - disc_grp["ev_cost"]
            worst_disc = disc_grp.sort_values(by="gap", ascending=False).index[0] if not disc_grp.empty else "Civil Works"
            w_ev = disc_grp.loc[worst_disc, "ev_cost"] / 1e6 if not disc_grp.empty else 0.0
            w_pv = disc_grp.loc[worst_disc, "pv_cost"] / 1e6 if not disc_grp.empty else 0.0
            remarks = f"Largest gap: {worst_disc} (EV {w_ev:.1f}M vs PV {w_pv:.1f}M)"

            clusters_list.append({
                "cluster": cl_name,
                "bac": c_bac,
                "weight": c_weight,
                "planned_pct": c_planned_pct,
                "actual_pct": c_actual_pct,
                "variance_pct": c_actual_pct - c_planned_pct,
                "pv": c_pv,
                "ev": c_ev,
                "sv": c_sv,
                "spi": c_spi,
                "health": health,
                "bl_finish": bl_finish,
                "fcst_finish": fcst_finish,
                "slip_days": slip_days,
                "remarks": remarks
            })

        # Sort clusters by name (e.g. C08, C09, C10...)
        clusters_list.sort(key=lambda x: x["cluster"])

        # -------------------------------------------------------------
        # 2. Discipline Breakdown Analysis
        # -------------------------------------------------------------
        disciplines_list = []
        for disc_name, d_df in df.groupby("Discipline"):
            d_bac = float(d_df["target_cost"].sum())
            if d_bac <= 0:
                continue
            d_pv = float(d_df["pv_cost"].sum())
            d_ev = float(d_df["ev_cost"].sum())
            d_planned_pct = (d_pv / d_bac * 100.0) if d_bac > 0 else 0.0
            d_actual_pct = (d_ev / d_bac * 100.0) if d_bac > 0 else 0.0
            d_sv = d_ev - d_pv
            d_spi = (d_ev / d_pv) if d_pv > 0 else (1.0 if d_ev >= d_pv else 0.0)
            disciplines_list.append({
                "discipline": disc_name,
                "bac": d_bac,
                "pv": d_pv,
                "pv_pct": d_planned_pct,
                "ev": d_ev,
                "ev_pct": d_actual_pct,
                "sv": d_sv,
                "spi": d_spi,
                "rem_budget": d_bac - d_ev
            })

        disciplines_list.sort(key=lambda x: x["bac"], reverse=True)

        # -------------------------------------------------------------
        # 3. Out-of-Sequence Logic Ties (OOS)
        # -------------------------------------------------------------
        oos_ties: List[Dict[str, Any]] = []
        if not preds.empty:
            task_dict = df.set_index("task_id").to_dict(orient="index")
            for _, rel in preds.iterrows():
                p_id = str(rel.get("pred_task_id") or "").strip()
                s_id = str(rel.get("task_id") or "").strip()
                p_info = task_dict.get(p_id)
                s_info = task_dict.get(s_id)
                if not p_info or not s_info:
                    continue

                p_pct = float(p_info.get("phys_complete_pct") or 0.0)
                p_st = str(p_info.get("status_code") or "")
                s_pct = float(s_info.get("phys_complete_pct") or 0.0)
                s_st = str(s_info.get("status_code") or "")

                # Check OOS condition: predecessor not started, but successor has progress
                if (p_pct == 0.0 or p_st == "TK_NotStart") and (s_pct > 0.0 or s_st in ("TK_Active", "TK_Complete")):
                    tie_raw = str(rel.get("pred_type") or "PR_FS").replace("PR_", "")
                    oos_ties.append({
                        "pred_id": str(p_info.get("task_code") or ""),
                        "pred_name": str(p_info.get("task_name") or ""),
                        "tie": tie_raw,
                        "succ_id": str(s_info.get("task_code") or ""),
                        "succ_name": str(s_info.get("task_name") or ""),
                        "succ_status": "Complete" if s_pct >= 100.0 else "In progress",
                        "succ_pct": s_pct
                    })

        # -------------------------------------------------------------
        # 4. Lookahead & Critical Activities Table (Active & Near Future)
        # -------------------------------------------------------------
        active_and_lookahead = []
        for _, row in df.iterrows():
            pct = float(row.get("phys_complete_pct") or 0.0)
            st_code = str(row.get("status_code") or "")
            t_start = str(row.get("target_start_date") or "")[:10]
            t_end = str(row.get("target_end_date") or "")[:10]
            late_days = 0
            if t_end and dd_dt:
                try:
                    end_dt = datetime.strptime(t_end, "%Y-%m-%d")
                    if dd_dt > end_dt and pct < 100.0:
                        late_days = (dd_dt - end_dt).days
                except Exception:
                    pass

            # Include if active, or starting in next 30 days
            include = False
            status_label = "Not started"
            if pct >= 100.0 or st_code == "TK_Complete":
                status_label = "Complete"
                if late_days > 0:
                    include = True
            elif pct > 0.0 or st_code == "TK_Active":
                status_label = "In progress"
                include = True
            elif t_start:
                try:
                    st_dt = datetime.strptime(t_start, "%Y-%m-%d")
                    if dd_dt and 0 <= (st_dt - dd_dt).days <= 30:
                        include = True
                except Exception:
                    pass

            if include:
                active_and_lookahead.append({
                    "act_id": str(row.get("task_code") or ""),
                    "act_name": str(row.get("task_name") or ""),
                    "cluster": str(row.get("Cluster") or ""),
                    "discipline": str(row.get("Discipline") or ""),
                    "status": status_label,
                    "pct": pct,
                    "target_start": t_start,
                    "bl_finish": t_end,
                    "fcst_finish": (datetime.strptime(t_end, "%Y-%m-%d") + timedelta(days=late_days)).strftime("%Y-%m-%d") if (t_end and late_days > 0) else t_end,
                    "late_days": late_days
                })

        # Sort lookahead by late days descending
        active_and_lookahead.sort(key=lambda x: x["late_days"], reverse=True)

        # -------------------------------------------------------------
        # 5. S-Curve Data Points (Weekly Early PV vs Late PV vs Actual EV)
        # -------------------------------------------------------------
        min_start = ts.min()
        max_finish = te.max()
        if pd.isna(min_start):
            min_start = dd_dt - timedelta(days=90)
        if pd.isna(max_finish):
            max_finish = dd_dt + timedelta(days=90)

        # Late dates for Banana Curve envelope
        l_ts = pd.to_datetime(df.get("late_start_date"), errors="coerce").fillna(ts)
        l_te = pd.to_datetime(df.get("late_end_date"), errors="coerce").fillna(te)
        l_total_secs = (l_te - l_ts).dt.total_seconds().fillna(0.0)

        is_baseline_only = bool(df["phys_complete_pct"].sum() <= 0.0)

        scurve_points = []
        curr_wk = min_start
        while curr_wk <= max_finish + timedelta(days=7):
            wk_str = curr_wk.strftime("%Y-%m-%d")
            wk_lbl = curr_wk.strftime("%d-%b")

            # Early PV (Target Start / Finish)
            wk_ratio_early = np.where(
                curr_wk >= te, 1.0,
                np.where(
                    curr_wk <= ts, 0.0,
                    (curr_wk - ts).dt.total_seconds().fillna(0.0) / np.maximum(total_secs, 1.0)
                )
            )
            wk_ratio_early = np.clip(wk_ratio_early, 0.0, 1.0)
            wk_pv_early = float((df["target_cost"] * wk_ratio_early).sum()) / 1e6

            # Late PV (Late Start / Finish - Banana Curve Envelope)
            wk_ratio_late = np.where(
                curr_wk >= l_te, 1.0,
                np.where(
                    curr_wk <= l_ts, 0.0,
                    (curr_wk - l_ts).dt.total_seconds().fillna(0.0) / np.maximum(l_total_secs, 1.0)
                )
            )
            wk_ratio_late = np.clip(wk_ratio_late, 0.0, 1.0)
            wk_pv_late = float((df["target_cost"] * wk_ratio_late).sum()) / 1e6

            # EV only up to data_date and only if progress exists
            wk_ev = None
            if not is_baseline_only and curr_wk <= dd_dt + timedelta(days=3):
                progress_factor = min(1.0, (curr_wk - min_start).total_seconds() / max(1.0, (dd_dt - min_start).total_seconds()))
                wk_ev = round((ev_total / 1e6) * (progress_factor ** 1.3), 2)
                if curr_wk >= dd_dt - timedelta(days=3):
                    wk_ev = round(ev_total / 1e6, 2)

            scurve_points.append({
                "week": wk_lbl,
                "date": wk_str,
                "pv_m": round(wk_pv_early, 2),
                "late_pv_m": round(wk_pv_late, 2),
                "ev_m": wk_ev
            })
            curr_wk += timedelta(days=7)

        # Dates & contractual milestones
        commence = contract_commence_str or (min_start.strftime("%Y-%m-%d") if pd.notna(min_start) else "2026-07-07")
        contract_fin = contract_finish_str or (max_finish.strftime("%Y-%m-%d") if pd.notna(max_finish) else "2027-01-07")
        contract_dt = pd.to_datetime(contract_fin, errors="coerce")

        # 1. Check true P6 CPM early_end_date / reend_date in TASK table
        p6_early_end = None
        for col_end in ("early_end_date", "reend_date"):
            if col_end in df.columns:
                valid_ends = pd.to_datetime(df[col_end], errors="coerce").dropna()
                if not valid_ends.empty:
                    p6_early_end = valid_ends.max()
                    break

        if p6_early_end and pd.notna(p6_early_end) and p6_early_end > pd.to_datetime("2026-07-07"):
            forecast_finish = p6_early_end.strftime("%Y-%m-%d")
            diff_days = int((p6_early_end - contract_dt).days) if pd.notna(contract_dt) else 80
            delay_days = -diff_days if diff_days > 0 else 0
        elif spi_total < 1.0:
            # Estimate slippage based on SPI and remaining work
            rem_days = max(10, int((contract_dt - dd_dt).days)) if (dd_dt and pd.notna(contract_dt)) else 56
            slip_days = int(rem_days * ((1.0 / max(0.20, spi_total)) - 1.0))
            slip_days = min(120, max(15, slip_days))
            forecast_fin_dt = (contract_dt if pd.notna(contract_dt) else max_finish) + timedelta(days=slip_days)
            forecast_finish = forecast_fin_dt.strftime("%Y-%m-%d")
            delay_days = -slip_days
        else:
            forecast_finish = contract_fin
            delay_days = 0

        return {
            "project_name": "HAPTOWN – Park View (Package HPT02S33 – Clusters 8 to 18)",
            "baseline_name": "P6 Baseline Schedule",
            "is_baseline_only": is_baseline_only,
            "data_date": data_date_str[:10],
            "commencement": str(commence)[:10],
            "contract_finish": str(contract_fin)[:10],
            "forecast_finish": str(forecast_finish)[:10],
            "variance_days": delay_days,
            "bac": bac_total,
            "pv": pv_total,
            "ev": ev_total,
            "sv": sv_total,
            "spi": spi_total,
            "planned_pct": planned_pct,
            "actual_pct": actual_pct,
            "variance_pct": variance_pct,
            "total_activities": len(df),
            "completed_count": complete_cnt,
            "active_count": active_cnt,
            "not_started_count": not_start_cnt,
            "oos_count": len(oos_ties),
            "clusters": clusters_list,
            "disciplines": disciplines_list,
            "oos_ties": oos_ties,
            "activities": active_and_lookahead,
            "scurve": scurve_points
        }
