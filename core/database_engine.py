"""SQLite Database Persistence Engine for Vortex Controls.
Stores projects, baseline schedules, weekly progress update snapshots,
cluster performance history, and out-of-sequence logic violations.
Enables historical EVM multi-week trend analysis and snapshot comparisons.
"""

from __future__ import annotations
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

DB_FILENAME = "vortex_controls.db"


class DatabaseEngine:
    """Manages SQLite storage and historical analytics retrieval for Vortex Controls."""

    def __init__(self, db_path: Optional[str] = None):
        if not db_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, DB_FILENAME)
        self.db_path = db_path
        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Initializes relational schema for projects, snapshots, clusters, and activities."""
        with self._get_connection() as conn:
            cur = conn.cursor()

            # 1. Projects Table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                baseline_name TEXT,
                contract_finish TEXT,
                forecast_finish TEXT,
                total_bac REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 2. Weekly Snapshots Table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS weekly_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                data_date TEXT NOT NULL,
                planned_pct REAL DEFAULT 0.0,
                actual_pct REAL DEFAULT 0.0,
                variance_pct REAL DEFAULT 0.0,
                pv REAL DEFAULT 0.0,
                ev REAL DEFAULT 0.0,
                sv REAL DEFAULT 0.0,
                spi REAL DEFAULT 1.0,
                active_count INTEGER DEFAULT 0,
                completed_count INTEGER DEFAULT 0,
                oos_count INTEGER DEFAULT 0,
                variance_days INTEGER DEFAULT 0,
                notes TEXT,
                snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );
            """)

            # 3. Cluster History Table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS cluster_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER,
                cluster_name TEXT NOT NULL,
                bac REAL DEFAULT 0.0,
                weight REAL DEFAULT 0.0,
                planned_pct REAL DEFAULT 0.0,
                actual_pct REAL DEFAULT 0.0,
                variance_pct REAL DEFAULT 0.0,
                pv REAL DEFAULT 0.0,
                ev REAL DEFAULT 0.0,
                sv REAL DEFAULT 0.0,
                spi REAL DEFAULT 1.0,
                forecast_finish TEXT,
                slip_days INTEGER DEFAULT 0,
                FOREIGN KEY(snapshot_id) REFERENCES weekly_snapshots(id)
            );
            """)

            # 4. Out-of-Sequence Violations Table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS oos_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER,
                pred_id TEXT,
                pred_name TEXT,
                tie TEXT,
                succ_id TEXT,
                succ_name TEXT,
                succ_status TEXT,
                succ_pct REAL,
                FOREIGN KEY(snapshot_id) REFERENCES weekly_snapshots(id)
            );
            """)

            conn.commit()

    def save_analytics_snapshot(self, analytics: Dict[str, Any], notes: str = "") -> int:
        """Saves a full project analytics update as an immutable snapshot in SQLite."""
        proj_name = analytics.get("project_name", "Vortex Project")
        bl_name = analytics.get("baseline_name", "")
        data_date = analytics.get("data_date", datetime.now().strftime("%Y-%m-%d"))
        bac = analytics.get("bac", 0.0)
        contract_finish = analytics.get("contract_finish", "-")
        fcst_finish = analytics.get("forecast_finish", "-")

        with self._get_connection() as conn:
            cur = conn.cursor()

            # Ensure or find project
            cur.execute("SELECT id FROM projects WHERE project_name = ? LIMIT 1;", (proj_name,))
            row = cur.fetchone()
            if row:
                project_id = row["id"]
                cur.execute("""
                    UPDATE projects 
                    SET baseline_name = ?, contract_finish = ?, forecast_finish = ?, total_bac = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?;
                """, (bl_name, contract_finish, fcst_finish, bac, project_id))
            else:
                cur.execute("""
                    INSERT INTO projects (project_name, baseline_name, contract_finish, forecast_finish, total_bac)
                    VALUES (?, ?, ?, ?, ?);
                """, (proj_name, bl_name, contract_finish, fcst_finish, bac))
                project_id = cur.lastrowid

            # Insert weekly snapshot
            cur.execute("""
                INSERT INTO weekly_snapshots (
                    project_id, data_date, planned_pct, actual_pct, variance_pct,
                    pv, ev, sv, spi, active_count, completed_count, oos_count,
                    variance_days, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                project_id,
                data_date,
                analytics.get("planned_pct", 0.0),
                analytics.get("actual_pct", 0.0),
                analytics.get("variance_pct", 0.0),
                analytics.get("pv", 0.0),
                analytics.get("ev", 0.0),
                analytics.get("sv", 0.0),
                analytics.get("spi", 1.0),
                analytics.get("active_count", 0),
                analytics.get("completed_count", 0),
                analytics.get("oos_count", 0),
                analytics.get("variance_days", 0),
                notes
            ))
            snapshot_id = cur.lastrowid

            # Insert cluster records
            clusters = analytics.get("clusters", [])
            for c in clusters:
                cur.execute("""
                    INSERT INTO cluster_history (
                        snapshot_id, cluster_name, bac, weight, planned_pct, actual_pct,
                        variance_pct, pv, ev, sv, spi, forecast_finish, slip_days
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    snapshot_id,
                    c.get("cluster", ""),
                    c.get("bac", 0.0),
                    c.get("weight", 0.0),
                    c.get("planned_pct", 0.0),
                    c.get("actual_pct", 0.0),
                    c.get("variance_pct", 0.0),
                    c.get("pv", 0.0),
                    c.get("ev", 0.0),
                    c.get("sv", 0.0),
                    c.get("spi", 1.0),
                    c.get("fcst_finish", "-"),
                    c.get("slip_days", 0)
                ))

            # Insert OOS ties (top 50)
            oos_ties = analytics.get("oos_ties", [])
            for o in oos_ties[:50]:
                cur.execute("""
                    INSERT INTO oos_history (
                        snapshot_id, pred_id, pred_name, tie, succ_id, succ_name, succ_status, succ_pct
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    snapshot_id,
                    o.get("pred_id", ""),
                    o.get("pred_name", ""),
                    o.get("tie", "FS"),
                    o.get("succ_id", ""),
                    o.get("succ_name", ""),
                    o.get("succ_status", ""),
                    o.get("succ_pct", 0.0)
                ))

            conn.commit()
            return snapshot_id

    def get_all_snapshots(self, project_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves historical weekly snapshots ordered chronologically."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            if project_name:
                cur.execute("""
                    SELECT s.*, p.project_name, p.baseline_name
                    FROM weekly_snapshots s
                    JOIN projects p ON s.project_id = p.id
                    WHERE p.project_name = ?
                    ORDER BY s.data_date ASC, s.snapshot_time ASC;
                """, (project_name,))
            else:
                cur.execute("""
                    SELECT s.*, p.project_name, p.baseline_name
                    FROM weekly_snapshots s
                    JOIN projects p ON s.project_id = p.id
                    ORDER BY s.data_date ASC, s.snapshot_time ASC;
                """)
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def get_snapshot_by_id(self, snapshot_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves full snapshot data including cluster breakdown and OOS records."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT s.*, p.project_name, p.baseline_name, p.contract_finish, p.forecast_finish, p.total_bac
                FROM weekly_snapshots s
                JOIN projects p ON s.project_id = p.id
                WHERE s.id = ?;
            """, (snapshot_id,))
            s_row = cur.fetchone()
            if not s_row:
                return None
            result = dict(s_row)

            # Get clusters
            cur.execute("SELECT * FROM cluster_history WHERE snapshot_id = ? ORDER BY cluster_name ASC;", (snapshot_id,))
            result["clusters"] = [dict(r) for r in cur.fetchall()]

            # Get OOS ties
            cur.execute("SELECT * FROM oos_history WHERE snapshot_id = ?;", (snapshot_id,))
            result["oos_ties"] = [dict(r) for r in cur.fetchall()]

            return result

    def get_database_stats(self) -> Dict[str, Any]:
        """Returns database storage diagnostics."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as count FROM projects;")
            proj_count = cur.fetchone()["count"]

            cur.execute("SELECT COUNT(*) as count FROM weekly_snapshots;")
            snap_count = cur.fetchone()["count"]

            cur.execute("SELECT COUNT(*) as count FROM cluster_history;")
            cluster_count = cur.fetchone()["count"]

            db_size_kb = os.path.getsize(self.db_path) / 1024 if os.path.exists(self.db_path) else 0

            return {
                "db_path": self.db_path,
                "db_size_kb": db_size_kb,
                "project_count": proj_count,
                "snapshot_count": snap_count,
                "cluster_records": cluster_count
            }
