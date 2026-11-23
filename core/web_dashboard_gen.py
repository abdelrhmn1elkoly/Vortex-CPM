"""Interactive Modern Fluent HTML5 Dashboard Generator.
Builds standalone, self-contained executive dashboards with Chart.js charts,
KPI hero cards, searchable tables, and print-optimized PDF layouts.
"""

from __future__ import annotations
import json
import os
from typing import Dict, Any


def generate_fluent_html_dashboard(analytics: Dict[str, Any], output_path: str) -> str:
    """Generates a standalone, dark Fluent Design HTML dashboard."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Prepare JSON payloads for Chart.js
    clusters_data = analytics.get("clusters", [])
    disciplines_data = analytics.get("disciplines", [])
    scurve_data = analytics.get("scurve", [])
    oos_ties = analytics.get("oos_ties", [])
    activities_data = analytics.get("activities", [])

    json_payload = json.dumps(analytics, default=str)

    html_content = f"""<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{analytics.get('project_name', 'AutoPlan Studio')} — Executive Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root {{
    --bg-main: #0B0F17;
    --bg-mica: rgba(19, 26, 40, 0.88);
    --bg-card: rgba(24, 33, 50, 0.82);
    --bg-card-hover: rgba(32, 44, 66, 0.95);
    --border-subtle: rgba(255, 255, 255, 0.08);
    --border-highlight: rgba(0, 229, 255, 0.35);
    --text-primary: #F8FAFC;
    --text-secondary: #94A3B8;
    --accent-cyan: #00E5FF;
    --accent-blue: #3B82F6;
    --accent-green: #10B981;
    --accent-amber: #F59E0B;
    --accent-red: #EF4444;
    --accent-purple: #A855F7;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI Variable Display', 'Segoe UI', system-ui, sans-serif; }}
body {{
    background: radial-gradient(circle at 85% 10%, #172542 0%, var(--bg-main) 60%);
    color: var(--text-primary);
    height: 100vh;
    display: flex;
    overflow: hidden;
}}
/* Sidebar */
.sidebar {{
    width: 250px;
    background: var(--bg-mica);
    backdrop-filter: blur(24px);
    border-right: 1px solid var(--border-subtle);
    display: flex;
    flex-direction: column;
    padding: 20px 14px;
    flex-shrink: 0;
}}
.brand {{
    display: flex; align-items: center; gap: 12px;
    padding: 8px 12px 24px; border-bottom: 1px solid var(--border-subtle);
    margin-bottom: 16px;
}}
.brand-icon {{
    width: 36px; height: 36px; border-radius: 10px;
    background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 16px; color: #06101E;
    box-shadow: 0 4px 14px rgba(0, 229, 255, 0.3);
}}
.brand-text h2 {{ font-size: 15px; font-weight: 700; letter-spacing: 0.3px; }}
.brand-text span {{ font-size: 11px; color: var(--text-secondary); }}
.nav-item {{
    display: flex; align-items: center; gap: 12px;
    padding: 11px 14px; border-radius: 8px;
    color: var(--text-secondary); font-size: 13px; font-weight: 500;
    cursor: pointer; transition: all 0.18s ease; margin-bottom: 6px;
    border: 1px solid transparent;
}}
.nav-item:hover {{ background: rgba(255,255,255,0.05); color: var(--text-primary); }}
.nav-item.active {{
    background: rgba(59, 130, 246, 0.16);
    color: var(--accent-cyan);
    border-color: rgba(0, 229, 255, 0.25);
    font-weight: 600;
}}
.sidebar-footer {{
    margin-top: auto; padding: 14px; border-radius: 10px;
    background: rgba(15, 23, 42, 0.65); border: 1px solid var(--border-subtle);
    font-size: 11.5px; color: var(--text-secondary); line-height: 1.5;
}}
/* Main Workspace */
.main {{
    flex: 1; display: flex; flex-direction: column; overflow: hidden;
}}
.topbar {{
    height: 68px; padding: 0 28px;
    background: rgba(15, 21, 33, 0.75); backdrop-filter: blur(16px);
    border-bottom: 1px solid var(--border-subtle);
    display: flex; align-items: center; justify-content: space-between;
    flex-shrink: 0;
}}
.topbar-title h1 {{ font-size: 17px; font-weight: 700; }}
.topbar-title p {{ font-size: 12px; color: var(--text-secondary); margin-top: 2px; }}
.topbar-actions {{ display: flex; align-items: center; gap: 10px; }}
.btn {{
    padding: 8px 15px; border-radius: 8px; font-size: 12.5px; font-weight: 600;
    cursor: pointer; border: 1px solid var(--border-subtle);
    background: var(--bg-card); color: var(--text-primary);
    display: inline-flex; align-items: center; gap: 8px; transition: all 0.18s;
}}
.btn:hover {{ border-color: var(--accent-cyan); background: var(--bg-card-hover); }}
.btn-primary {{
    background: linear-gradient(135deg, #0284C7, #2563EB);
    border-color: #38BDF8; color: #FFF;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
}}
.btn-primary:hover {{ filter: brightness(1.12); }}
.content-scroll {{
    flex: 1; overflow-y: auto; padding: 24px 28px 40px;
}}
.page-section {{ display: none; }}
.page-section.active {{ display: block; }}
/* KPI Grid */
.kpi-grid {{
    display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-bottom: 22px;
}}
.kpi-card {{
    background: var(--bg-card); backdrop-filter: blur(16px);
    border: 1px solid var(--border-subtle); border-radius: 12px;
    padding: 16px 18px; position: relative; overflow: hidden;
    transition: transform 0.18s ease, border-color 0.18s ease;
}}
.kpi-card:hover {{ transform: translateY(-2px); border-color: rgba(255,255,255,0.18); }}
.kpi-card::before {{
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3.5px;
    background: var(--accent, var(--accent-cyan));
}}
.kpi-label {{ font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-secondary); letter-spacing: 0.7px; }}
.kpi-val {{ font-size: 24px; font-weight: 800; margin: 7px 0 4px; color: #FFF; }}
.kpi-sub {{ font-size: 11.5px; color: var(--accent, var(--accent-cyan)); font-weight: 500; }}
/* Charts & Panels */
.grid-2col {{ display: grid; grid-template-columns: 1.55fr 1fr; gap: 18px; margin-bottom: 22px; }}
.card {{
    background: var(--bg-card); backdrop-filter: blur(16px);
    border: 1px solid var(--border-subtle); border-radius: 12px; padding: 18px 20px;
}}
.card-header {{
    display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;
}}
.card-title {{ font-size: 14px; font-weight: 700; color: #E2E8F0; }}
.filter-bar {{
    display: flex; gap: 10px; align-items: center; margin-bottom: 14px; flex-wrap: wrap;
}}
select, input[type="text"], input[type="date"] {{
    background: #111827; border: 1px solid var(--border-subtle); color: #F8FAFC;
    padding: 7px 12px; border-radius: 7px; font-size: 12.5px; outline: none;
}}
select:focus, input:focus {{ border-color: var(--accent-cyan); }}
/* Table */
.table-wrap {{ overflow-x: auto; max-height: 480px; overflow-y: auto; }}
table {{ width: 100%; border-collapse: collapse; font-size: 12.5px; }}
th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border-subtle); }}
th {{
    position: sticky; top: 0; background: #131B2E; color: var(--text-secondary);
    font-weight: 700; font-size: 11px; text-transform: uppercase; z-index: 2;
}}
tr:hover td {{ background: rgba(255,255,255,0.03); }}
.prog-track {{
    width: 75px; height: 6px; background: #1E293B; border-radius: 4px;
    display: inline-block; vertical-align: middle; margin-right: 7px; overflow: hidden;
}}
.prog-bar {{ height: 100%; background: linear-gradient(90deg, var(--accent-blue), var(--accent-green)); }}
.badge {{
    padding: 3px 9px; border-radius: 10px; font-size: 11px; font-weight: 700; display: inline-block;
}}
.badge-red {{ background: rgba(239,68,68,0.18); color: #FCA5A5; border: 1px solid rgba(239,68,68,0.35); }}
.badge-amber {{ background: rgba(245,158,11,0.18); color: #FCD34D; border: 1px solid rgba(245,158,11,0.35); }}
.badge-green {{ background: rgba(16,185,129,0.18); color: #6EE7B7; border: 1px solid rgba(16,185,129,0.35); }}
.badge-blue {{ background: rgba(59,130,246,0.18); color: #93C5FD; border: 1px solid rgba(59,130,246,0.35); }}

/* Print PDF Optimization */
@media print {{
    body {{ background: #FFF !important; color: #000 !important; height: auto !important; overflow: visible !important; }}
    .sidebar, .topbar-actions {{ display: none !important; }}
    .main {{ width: 100% !important; }}
    .topbar {{ background: transparent !important; border-bottom: 2px solid #000 !important; color: #000 !important; padding: 0 !important; }}
    .content-scroll {{ padding: 10px 0 !important; overflow: visible !important; }}
    .card, .kpi-card {{ background: #FFF !important; border: 1px solid #CCC !important; color: #000 !important; page-break-inside: avoid; }}
    .kpi-val, .kpi-label, .card-title, th, td {{ color: #000 !important; }}
    .badge {{ border: 1px solid #888 !important; color: #000 !important; }}
    .page-section {{ display: block !important; margin-bottom: 30px; }}
}}
</style>
</head>
<body>

<!-- SIDEBAR -->
<div class="sidebar">
    <div class="brand">
        <div class="brand-icon">AP</div>
        <div class="brand-text">
            <h2>AutoPlan Studio</h2>
            <span>Fluent Project Controls</span>
        </div>
    </div>
    <div class="nav-item active" onclick="switchTab('dash', this)">📊 Executive Dashboard</div>
    <div class="nav-item" onclick="switchTab('clusters', this)">🏢 Clusters Matrix</div>
    <div class="nav-item" onclick="switchTab('disciplines', this)">🛠️ Discipline Breakdown</div>
    <div class="nav-item" onclick="switchTab('lookahead', this)">📅 Lookahead & Critical</div>
    <div class="nav-item" onclick="switchTab('oos', this)">⚠️ Out-of-Sequence ({analytics.get('oos_count', 0)})</div>

    <div class="sidebar-footer">
        <strong>Active Schedule:</strong><br>
        Baseline: {analytics.get('baseline_name', 'Loaded')}<br>
        Data Date: {analytics.get('data_date', '')}<br>
        Total BAC: {analytics.get('bac', 0)/1e6:.2f}M EGP
    </div>
</div>

<!-- MAIN WORKSPACE -->
<div class="main">
    <div class="topbar">
        <div class="topbar-title">
            <h1>{analytics.get('project_name', 'HAPTOWN – Park View')}</h1>
            <p>Data Date: {analytics.get('data_date')} &nbsp;•&nbsp; Baseline: {analytics.get('baseline_name')} &nbsp;•&nbsp; Total Budget: {analytics.get('bac', 0)/1e6:.2f}M EGP</p>
        </div>
        <div class="topbar-actions">
            <button class="btn" onclick="window.print()">🖨️ Print / Save as PDF</button>
        </div>
    </div>

    <div class="content-scroll">
        <!-- TAB 1: EXECUTIVE DASHBOARD -->
        <div id="tab-dash" class="page-section active">
            <div class="kpi-grid">
                <div class="kpi-card" style="--accent: var(--accent-cyan)">
                    <div class="kpi-label">Overall Physical %</div>
                    <div class="kpi-val">{analytics.get('actual_pct', 0):.2f}%</div>
                    <div class="kpi-sub">Planned: {analytics.get('planned_pct', 0):.2f}% ({analytics.get('variance_pct', 0):+.2f}%)</div>
                </div>
                <div class="kpi-card" style="--accent: var(--accent-blue)">
                    <div class="kpi-label">Earned Value (EV)</div>
                    <div class="kpi-val">{analytics.get('ev', 0)/1e6:.2f}M EGP</div>
                    <div class="kpi-sub">PV: {analytics.get('pv', 0)/1e6:.2f}M / BAC: {analytics.get('bac', 0)/1e6:.2f}M</div>
                </div>
                <div class="kpi-card" style="--accent: var(--accent-red)">
                    <div class="kpi-label">Schedule Index (SPI)</div>
                    <div class="kpi-val">{analytics.get('spi', 0):.2f}</div>
                    <div class="kpi-sub">SV: {analytics.get('sv', 0)/1e6:+.2f}M EGP</div>
                </div>
                <div class="kpi-card" style="--accent: var(--accent-amber)">
                    <div class="kpi-label">Forecast Completion</div>
                    <div class="kpi-val">{analytics.get('forecast_finish', '')}</div>
                    <div class="kpi-sub">Contract: {analytics.get('contract_finish', '')} ({analytics.get('variance_days', 0)}d)</div>
                </div>
                <div class="kpi-card" style="--accent: var(--accent-purple)">
                    <div class="kpi-label">Activities & Logic</div>
                    <div class="kpi-val">{analytics.get('active_count', 0)} Act / {analytics.get('completed_count', 0)} Done</div>
                    <div class="kpi-sub">{analytics.get('oos_count', 0)} Out-of-Sequence Ties</div>
                </div>
            </div>

            <div class="grid-2col">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">📈 Cumulative S-Curve: Planned Value (PV) vs Earned Value (EV) [M EGP]</span>
                    </div>
                    <canvas id="scurveChart" height="115"></canvas>
                </div>
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">🛠️ Discipline Performance (Actual % vs Planned %)</span>
                    </div>
                    <canvas id="discChart" height="175"></canvas>
                </div>
            </div>

            <div class="grid-2col">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">🏢 Cluster Progress Comparison (Planned % vs Actual %)</span>
                    </div>
                    <canvas id="clusterChart" height="115"></canvas>
                </div>
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">⚡ Cluster Schedule Index (SPI)</span>
                    </div>
                    <canvas id="spiChart" height="175"></canvas>
                </div>
            </div>
        </div>

        <!-- TAB 2: CLUSTERS MATRIX -->
        <div id="tab-clusters" class="page-section">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">🏢 Cluster Progress & Earned Value Matrix (C08 to C18)</span>
                </div>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Cluster</th><th>Budget (BAC)</th><th>Weight %</th><th>Planned %</th>
                                <th>Actual %</th><th>PV (EGP)</th><th>EV (EGP)</th><th>SV (EGP)</th>
                                <th>SPI</th><th>Baseline Finish</th><th>Forecast Finish</th><th>Slip (d)</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-clusters"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 3: DISCIPLINE BREAKDOWN -->
        <div id="tab-disciplines" class="page-section">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">🛠️ Engineering Discipline Breakdown</span>
                </div>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Discipline</th><th>Budget (BAC)</th><th>Planned (PV)</th><th>Planned %</th>
                                <th>Earned (EV)</th><th>Actual %</th><th>SV (EGP)</th><th>SPI</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-disciplines"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 4: LOOKAHEAD ACTIVITIES -->
        <div id="tab-lookahead" class="page-section">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">📅 Active & 30-Day Lookahead Activities</span>
                </div>
                <div class="filter-bar">
                    <input type="text" id="search-act" placeholder="Search Activity ID or Name..." oninput="renderActivitiesTable()">
                    <select id="filter-st" onchange="renderActivitiesTable()">
                        <option value="ALL">All Statuses</option>
                        <option value="In progress">In Progress</option>
                        <option value="Complete">Complete</option>
                        <option value="Not started">Not Started</option>
                    </select>
                </div>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Activity ID</th><th>Activity Name</th><th>Cluster</th><th>Discipline</th>
                                <th>Status</th><th>Progress %</th><th>Target Start</th><th>Baseline Finish</th><th>Late (d)</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-activities"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 5: OUT OF SEQUENCE -->
        <div id="tab-oos" class="page-section">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">⚠️ Out-of-Sequence Logic Ties (Predecessor Not Started → Successor Has Progress)</span>
                </div>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Predecessor ID</th><th>Predecessor Name</th><th>Tie</th>
                                <th>Successor ID</th><th>Successor Name</th><th>Successor Status</th><th>Successor %</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-oos"></tbody>
                    </table>
                </div>
            </div>
        </div>

    </div>
</div>

<script>
const APP_DATA = {json_payload};

function switchTab(tabId, el) {{
    document.querySelectorAll('.page-section').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const target = document.getElementById('tab-' + tabId);
    if (target) target.classList.add('active');
    if (el) el.classList.add('active');
}}

function initCharts() {{
    // S-Curve
    const scurveCtx = document.getElementById('scurveChart');
    if (scurveCtx && APP_DATA.scurve) {{
        new Chart(scurveCtx.getContext('2d'), {{
            type: 'line',
            data: {{
                labels: APP_DATA.scurve.map(p => p.week),
                datasets: [
                    {{
                        label: 'Planned Value (PV)',
                        data: APP_DATA.scurve.map(p => p.pv_m),
                        borderColor: '#3B82F6',
                        backgroundColor: 'rgba(59, 130, 246, 0.12)',
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.35,
                        pointRadius: 2
                    }},
                    {{
                        label: 'Earned Value (EV)',
                        data: APP_DATA.scurve.map(p => p.ev_m),
                        borderColor: '#00E5FF',
                        backgroundColor: 'rgba(0, 229, 255, 0.12)',
                        borderWidth: 3,
                        fill: false,
                        tension: 0.3,
                        pointRadius: 3
                    }}
                ]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ labels: {{ color: '#E2E8F0', font: {{ size: 11 }} }} }} }},
                scales: {{
                    x: {{ ticks: {{ color: '#94A3B8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
                    y: {{ ticks: {{ color: '#94A3B8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}
                }}
            }}
        }});
    }}

    // Discipline Chart
    const discCtx = document.getElementById('discChart');
    if (discCtx && APP_DATA.disciplines) {{
        new Chart(discCtx.getContext('2d'), {{
            type: 'bar',
            data: {{
                labels: APP_DATA.disciplines.map(d => d.discipline),
                datasets: [
                    {{ label: 'Planned %', data: APP_DATA.disciplines.map(d => d.pv_pct), backgroundColor: '#334155', borderRadius: 4 }},
                    {{ label: 'Actual %', data: APP_DATA.disciplines.map(d => d.ev_pct), backgroundColor: '#00E5FF', borderRadius: 4 }}
                ]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                plugins: {{ legend: {{ labels: {{ color: '#E2E8F0' }} }} }},
                scales: {{
                    x: {{ ticks: {{ color: '#94A3B8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
                    y: {{ ticks: {{ color: '#E2E8F0' }}, grid: {{ display: false }} }}
                }}
            }}
        }});
    }}

    // Cluster Progress Chart
    const clCtx = document.getElementById('clusterChart');
    if (clCtx && APP_DATA.clusters) {{
        new Chart(clCtx.getContext('2d'), {{
            type: 'bar',
            data: {{
                labels: APP_DATA.clusters.map(c => c.cluster),
                datasets: [
                    {{ label: 'Planned %', data: APP_DATA.clusters.map(c => c.planned_pct), backgroundColor: '#3B82F6', borderRadius: 5 }},
                    {{ label: 'Actual %', data: APP_DATA.clusters.map(c => c.actual_pct), backgroundColor: '#10B981', borderRadius: 5 }}
                ]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ labels: {{ color: '#E2E8F0' }} }} }},
                scales: {{
                    x: {{ ticks: {{ color: '#E2E8F0' }} }},
                    y: {{ ticks: {{ color: '#94A3B8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}
                }}
            }}
        }});
    }}

    // Cluster SPI Chart
    const spiCtx = document.getElementById('spiChart');
    if (spiCtx && APP_DATA.clusters) {{
        new Chart(spiCtx.getContext('2d'), {{
            type: 'bar',
            data: {{
                labels: APP_DATA.clusters.map(c => c.cluster),
                datasets: [{{
                    label: 'SPI',
                    data: APP_DATA.clusters.map(c => c.spi),
                    backgroundColor: APP_DATA.clusters.map(c => c.spi < 0.4 ? '#EF4444' : (c.spi < 0.8 ? '#F59E0B' : '#10B981')),
                    borderRadius: 4
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ min: 0, max: 1.1, ticks: {{ color: '#94A3B8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
                    y: {{ ticks: {{ color: '#E2E8F0' }}, grid: {{ display: false }} }}
                }}
            }}
        }});
    }}
}}

function renderTables() {{
    // Clusters Table
    const tbCl = document.getElementById('tbody-clusters');
    if (tbCl && APP_DATA.clusters) {{
        tbCl.innerHTML = APP_DATA.clusters.map(c => {{
            const badgeCls = c.spi < 0.4 ? 'badge-red' : (c.spi < 0.8 ? 'badge-amber' : 'badge-green');
            return `<tr>
                <td><strong>${{c.cluster}}</strong></td>
                <td>${{(c.bac/1e6).toFixed(2)}}M</td>
                <td>${{c.weight.toFixed(1)}}%</td>
                <td>${{c.planned_pct.toFixed(1)}}%</td>
                <td><div class="prog-track"><div class="prog-bar" style="width:${{Math.min(100, c.actual_pct)}}%"></div></div>${{c.actual_pct.toFixed(1)}}%</td>
                <td>${{(c.pv/1e6).toFixed(2)}}M</td>
                <td>${{(c.ev/1e6).toFixed(2)}}M</td>
                <td>${{(c.sv/1e6).toFixed(2)}}M</td>
                <td><span class="badge ${{badgeCls}}">${{c.spi.toFixed(2)}}</span></td>
                <td>${{c.bl_finish || '-'}}</td>
                <td>${{c.fcst_finish || '-'}}</td>
                <td><span class="badge badge-red">${{c.slip_days || 0}}d</span></td>
            </tr>`;
        }}).join('');
    }}

    // Disciplines Table
    const tbDs = document.getElementById('tbody-disciplines');
    if (tbDs && APP_DATA.disciplines) {{
        tbDs.innerHTML = APP_DATA.disciplines.map(d => {{
            return `<tr>
                <td><strong>${{d.discipline}}</strong></td>
                <td>${{(d.bac/1e6).toFixed(2)}}M</td>
                <td>${{(d.pv/1e6).toFixed(2)}}M</td>
                <td>${{d.pv_pct.toFixed(1)}}%</td>
                <td>${{(d.ev/1e6).toFixed(2)}}M</td>
                <td><div class="prog-track"><div class="prog-bar" style="width:${{Math.min(100, d.ev_pct)}}%"></div></div>${{d.ev_pct.toFixed(1)}}%</td>
                <td>${{(d.sv/1e6).toFixed(2)}}M</td>
                <td>${{d.spi.toFixed(2)}}</td>
            </tr>`;
        }}).join('');
    }}

    // OOS Table
    const tbOos = document.getElementById('tbody-oos');
    if (tbOos && APP_DATA.oos_ties) {{
        tbOos.innerHTML = APP_DATA.oos_ties.map(o => `<tr>
            <td><code>${{o.pred_id}}</code></td>
            <td>${{o.pred_name}}</td>
            <td><span class="badge badge-amber">${{o.tie}}</span></td>
            <td><code>${{o.succ_id}}</code></td>
            <td>${{o.succ_name}}</td>
            <td><span class="badge badge-blue">${{o.succ_status}}</span></td>
            <td>${{o.succ_pct}}%</td>
        </tr>`).join('');
    }}

    renderActivitiesTable();
}}

function renderActivitiesTable() {{
    const q = (document.getElementById('search-act')?.value || '').toLowerCase();
    const st = document.getElementById('filter-st')?.value || 'ALL';
    const tbAct = document.getElementById('tbody-activities');
    if (!tbAct || !APP_DATA.activities) return;

    const filtered = APP_DATA.activities.filter(a => {{
        if (st !== 'ALL' && a.status.toLowerCase() !== st.toLowerCase()) return false;
        if (q && !a.act_id.toLowerCase().includes(q) && !a.act_name.toLowerCase().includes(q)) return false;
        return true;
    }});

    tbAct.innerHTML = filtered.slice(0, 150).map(a => {{
        const badge = a.status === 'Complete' ? 'badge-green' : (a.status === 'In progress' ? 'badge-blue' : 'badge-amber');
        return `<tr>
            <td><code>${{a.act_id}}</code></td>
            <td>${{a.act_name}}</td>
            <td><strong>${{a.cluster}}</strong></td>
            <td>${{a.discipline}}</td>
            <td><span class="badge ${{badge}}">${{a.status}}</span></td>
            <td><div class="prog-track"><div class="prog-bar" style="width:${{a.pct}}%"></div></div>${{a.pct}}%</td>
            <td>${{a.target_start || '-'}}</td>
            <td>${{a.bl_finish || '-'}}</td>
            <td>${{a.late_days > 0 ? a.late_days + 'd' : '-'}}</td>
        </tr>`;
    }}).join('');
}}

window.addEventListener('DOMContentLoaded', () => {{
    initCharts();
    renderTables();
}});
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path
