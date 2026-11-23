"""Smart Weekly Site Progress Excel Importer.
Parses multi-cluster or unified Excel progress sheets, handles fuzzy column matching,
date sanitation, whitespace trimming, and % scale normalization.
"""

from __future__ import annotations
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import openpyxl


def clean_date_string(val: Any, data_date_str: str) -> Optional[str]:
    """Parses and sanitizes date strings or datetime objects, preventing inverted day/month."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.strftime("%Y-%m-%d")

    s = str(val).strip()
    if not s or s.lower() in ("-", "none", "nat", "null", "n/a"):
        return None

    # Handle datetime with timestamp (e.g., '2026-10-29 00:00:00')
    s = s.split(" ")[0].strip()

    formats = (
        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
        "%d-%m-%Y", "%d-%b-%Y", "%d-%b-%y",
        "%Y/%m/%d"
    )

    dd_limit = None
    try:
        dd_limit = datetime.strptime(data_date_str[:10], "%Y-%m-%d")
    except Exception:
        pass

    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            # Correct inverted month and day if date falls into the future beyond data_date
            if dd_limit and dt > dd_limit and dt.day <= 12 and dt.month <= 12:
                try:
                    flipped = dt.replace(month=dt.day, day=dt.month)
                    if flipped <= dd_limit:
                        dt = flipped
                except ValueError:
                    pass
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


class ExcelProgressImporter:
    """Parses site progress workbooks and extracts normalized activity updates."""

    ID_KEYS = ["activity id", "task_code", "act id", "id", "code", "كود النشاط"]
    NAME_KEYS = ["activity name", "task_name", "name", "description", "اسم النشاط"]
    STATUS_KEYS = ["activity status", "status", "حالة النشاط", "الحالة"]
    PCT_KEYS = ["% complete", "performance % complete", "physical %", "actual %", "progress", "phys_complete_pct", "نسبة الإنجاز", "%"]
    START_KEYS = ["actual start", "act_start_date", "start date", "start", "تاريخ البداية"]
    FINISH_KEYS = ["actual finish", "act_end_date", "finish date", "finish", "تاريخ النهاية"]
    REM_DUR_KEYS = ["remaining duration", "rem dur", "remain_drtn", "remaining", "المدة المتبقية"]
    NOTES_KEYS = ["notes", "remarks", "comment", "comments", "ملاحظات"]

    @classmethod
    def parse_file(cls, file_path: str, data_date: str = "2026-10-29") -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
        """
        Parses all sheets in the Excel workbook and extracts a normalized progress map.
        Returns:
            progress_map: { 'HT.CO.Civil.C08.010': { 'pct': 50.0, 'start': '2026-09-30', 'finish': None, 'remain_dur': 7, ... } }
            summary: { 'total_parsed': int, 'sheets_processed': list, 'clusters_found': list }
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Site progress file not found: {file_path}")

        wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        sheet_names = wb.sheetnames
        progress_records: Dict[str, Dict[str, Any]] = {}
        clusters_found = set()
        sheets_processed = []

        # Sheets that are purely analytical or audit reports, not activity progress lists
        SKIP_SHEET_KEYWORDS = ["out-of-seq", "ties", "forecast", "s-curve", "dashboard", "baseline pv", "baseline e&p"]

        for s_name in sheet_names:
            s_lower = s_name.lower()
            if any(kw in s_lower for kw in SKIP_SHEET_KEYWORDS):
                continue

            ws = wb[s_name]
            rows = list(ws.iter_rows(values_only=True))
            if not rows or len(rows) < 2:
                continue

            # Detect header row within top 10 rows
            header_idx = -1
            col_map: Dict[str, int] = {}

            for r_idx in range(min(10, len(rows))):
                row_vals = [str(v).strip().lower() if v is not None else "" for v in rows[r_idx]]
                if any(any(k == rv or k in rv for k in cls.ID_KEYS) for rv in row_vals):
                    header_idx = r_idx
                    # Map column types
                    for c_idx, cell_val in enumerate(row_vals):
                        if not cell_val:
                            continue
                        if "col_id" not in col_map and any(k == cell_val or k in cell_val for k in cls.ID_KEYS):
                            col_map["col_id"] = c_idx
                        elif "col_pct" not in col_map and any(k in cell_val for k in cls.PCT_KEYS):
                            col_map["col_pct"] = c_idx
                        elif "col_name" not in col_map and any(k in cell_val for k in cls.NAME_KEYS):
                            col_map["col_name"] = c_idx
                        elif "col_status" not in col_map and any(k in cell_val for k in cls.STATUS_KEYS):
                            col_map["col_status"] = c_idx
                        elif "col_st" not in col_map and any(k in cell_val for k in cls.START_KEYS):
                            col_map["col_st"] = c_idx
                        elif "col_fn" not in col_map and any(k in cell_val for k in cls.FINISH_KEYS):
                            col_map["col_fn"] = c_idx
                        elif "col_rem" not in col_map and any(k in cell_val for k in cls.REM_DUR_KEYS):
                            col_map["col_rem"] = c_idx
                        elif "col_notes" not in col_map and any(k in cell_val for k in cls.NOTES_KEYS):
                            col_map["col_notes"] = c_idx
                    break

            if header_idx == -1 or "col_id" not in col_map or "col_pct" not in col_map:
                continue

            sheets_processed.append(s_name)

            # Process data rows
            for row in rows[header_idx + 1:]:
                if not row or len(row) <= col_map["col_id"]:
                    continue

                raw_id_val = row[col_map["col_id"]]
                if raw_id_val is None or pd.isna(raw_id_val):
                    continue

                raw_id_str = str(raw_id_val).strip()
                if not raw_id_str:
                    continue

                # Extract task code (e.g., from '    HT.CO.Civil.C08.010' or 'HT.CO.Civil.C08.010 - Surface')
                act_id = None
                tokens = raw_id_str.split()
                for t in tokens:
                    if t.startswith("HT.") or t.startswith("ACT-") or (len(t) > 3 and "." in t):
                        act_id = t
                        break
                if not act_id:
                    if raw_id_str.startswith("HT."):
                        act_id = raw_id_str
                    else:
                        continue

                # Parse % complete
                raw_pct_val = row[col_map["col_pct"]] if col_map["col_pct"] < len(row) else 0.0
                pct = 0.0
                if raw_pct_val is not None and not pd.isna(raw_pct_val):
                    pct_str = str(raw_pct_val).replace("%", "").strip()
                    try:
                        pct = float(pct_str)
                        if 0.0 < pct <= 1.0:
                            pct *= 100.0
                    except ValueError:
                        pct = 0.0
                pct = max(0.0, min(100.0, pct))

                # Parse Status
                status_raw = ""
                if "col_status" in col_map and col_map["col_status"] < len(row):
                    v = row[col_map["col_status"]]
                    status_raw = str(v).strip() if v is not None else ""

                if not status_raw:
                    if pct >= 100.0:
                        status_raw = "Finished"
                    elif pct > 0.0:
                        status_raw = "Started"
                    else:
                        status_raw = "Not Started"

                # Parse Dates
                st_val = row[col_map["col_st"]] if "col_st" in col_map and col_map["col_st"] < len(row) else None
                fn_val = row[col_map["col_fn"]] if "col_fn" in col_map and col_map["col_fn"] < len(row) else None
                clean_st = clean_date_string(st_val, data_date)
                clean_fn = clean_date_string(fn_val, data_date)

                # Parse Remaining Duration
                rem_dur = None
                if "col_rem" in col_map and col_map["col_rem"] < len(row):
                    rem_val = row[col_map["col_rem"]]
                    if rem_val is not None and not pd.isna(rem_val):
                        try:
                            rem_dur = float(rem_val)
                        except ValueError:
                            rem_dur = None

                # Extract Cluster info if possible
                cluster_match = re.search(r"\b(C\d{1,2})\b", act_id, re.IGNORECASE)
                if not cluster_match:
                    cluster_match = re.search(r"\b(C\d{1,2})\b", s_name, re.IGNORECASE)
                if cluster_match:
                    cl_num = int(cluster_match.group(1)[1:])
                    clusters_found.add(f"C{cl_num:02d}")

                # Save record
                progress_records[act_id] = {
                    "task_code": act_id,
                    "pct": pct,
                    "status": status_raw,
                    "start": clean_st,
                    "finish": clean_fn,
                    "remain_dur": rem_dur,
                    "sheet_source": s_name
                }

        summary = {
            "total_parsed": len(progress_records),
            "sheets_processed": sheets_processed,
            "clusters_found": sorted(list(clusters_found))
        }

        return progress_records, summary

    @classmethod
    def parse_csv_text(cls, csv_text: str, data_date: str = "2026-11-12") -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
        """
        Parses raw CSV / TSV text pasted directly from site reports or spreadsheets.
        Detects delimiters (comma, tab, semicolon), headers, and extracts normalized progress.
        """
        import io
        import csv

        if not csv_text or not csv_text.strip():
            return {}, {"total_parsed": 0, "sheets_processed": [], "clusters_found": []}

        lines = [line for line in csv_text.splitlines() if line.strip()]
        if not lines:
            return {}, {"total_parsed": 0, "sheets_processed": [], "clusters_found": []}

        # Detect delimiter
        first_line = lines[0]
        delimiter = "\t" if "\t" in first_line else (";" if ";" in first_line else ",")

        reader = csv.reader(io.StringIO(csv_text), delimiter=delimiter)
        rows = list(reader)
        if not rows:
            return {}, {"total_parsed": 0, "sheets_processed": [], "clusters_found": []}

        # Locate header row
        header_idx = -1
        col_map: Dict[str, int] = {}
        for r_i, row in enumerate(rows[:15]):
            row_clean = [str(c).strip().lower() for c in row if c]
            id_col = -1
            pct_col = -1
            for c_i, c_val in enumerate(row):
                val_l = str(c_val).strip().lower()
                if any(k in val_l for k in cls.ID_KEYS):
                    id_col = c_i
                elif any(k in val_l for k in cls.PCT_KEYS):
                    pct_col = c_i
            if id_col >= 0 and pct_col >= 0:
                header_idx = r_i
                col_map["col_id"] = id_col
                col_map["col_pct"] = pct_col
                for c_i, c_val in enumerate(row):
                    val_l = str(c_val).strip().lower()
                    if any(k in val_l for k in cls.START_KEYS) and "col_st" not in col_map:
                        col_map["col_st"] = c_i
                    elif any(k in val_l for k in cls.FINISH_KEYS) and "col_fn" not in col_map:
                        col_map["col_fn"] = c_i
                    elif any(k in val_l for k in cls.REM_DUR_KEYS) and "col_rem" not in col_map:
                        col_map["col_rem"] = c_i
                    elif any(k in val_l for k in cls.STATUS_KEYS) and "col_status" not in col_map:
                        col_map["col_status"] = c_i
                break

        if header_idx < 0:
            # Fallback heuristic: assume col 0 is Activity ID, col 1 is Name/Status, col 2 is % Complete
            col_map = {"col_id": 0, "col_pct": 2, "col_st": 3, "col_fn": 4}
            header_idx = 0

        progress_records: Dict[str, Dict[str, Any]] = {}
        clusters_found = set()

        for row in rows[header_idx + 1:]:
            if not row or len(row) <= col_map.get("col_id", 0):
                continue
            act_id = str(row[col_map["col_id"]]).strip()
            if not act_id or act_id.lower() in ("activity id", "task_code", "total", "summary"):
                continue

            # Parse % Complete
            pct = 0.0
            if "col_pct" in col_map and col_map["col_pct"] < len(row):
                pct_str = str(row[col_map["col_pct"]]).replace("%", "").strip()
                try:
                    pct = float(pct_str)
                    if 0.0 < pct < 1.0:
                        pct *= 100.0
                except ValueError:
                    pct = 0.0
            pct = max(0.0, min(100.0, pct))

            # Status
            status_raw = ""
            if "col_status" in col_map and col_map["col_status"] < len(row):
                status_raw = str(row[col_map["col_status"]]).strip()
            if not status_raw:
                if pct >= 100.0:
                    status_raw = "Finished"
                elif pct > 0.0:
                    status_raw = "Started"
                else:
                    status_raw = "Not Started"

            # Dates
            st_val = row[col_map["col_st"]] if "col_st" in col_map and col_map["col_st"] < len(row) else None
            fn_val = row[col_map["col_fn"]] if "col_fn" in col_map and col_map["col_fn"] < len(row) else None
            clean_st = clean_date_string(st_val, data_date)
            clean_fn = clean_date_string(fn_val, data_date)

            # Remaining Duration
            rem_dur = None
            if "col_rem" in col_map and col_map["col_rem"] < len(row):
                rem_val = row[col_map["col_rem"]]
                try:
                    rem_dur = float(rem_val) if rem_val is not None and str(rem_val).strip() else None
                except ValueError:
                    rem_dur = None

            cluster_match = re.search(r"\b(C\d{1,2})\b", act_id, re.IGNORECASE)
            if cluster_match:
                cl_num = int(cluster_match.group(1)[1:])
                clusters_found.add(f"C{cl_num:02d}")

            progress_records[act_id] = {
                "task_code": act_id,
                "pct": pct,
                "status": status_raw,
                "start": clean_st,
                "finish": clean_fn,
                "remain_dur": rem_dur,
                "sheet_source": "Pasted_CSV"
            }

        return progress_records, {
            "total_parsed": len(progress_records),
            "sheets_processed": ["Pasted_CSV"],
            "clusters_found": sorted(list(clusters_found))
        }
