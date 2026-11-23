# Vortex Controls ⚡
### Executive Construction Project Controls & Fluent Primavera P6 Engine

**Vortex Controls** is an executive construction project controls and schedule management desktop suite built with **PySide6** and adhering strictly to the **Microsoft Windows 11 WinUI 3 / Fluent Design** philosophy of **Vortex PT**.

It bridges Oracle Primavera P6 baseline schedules (`.XER`) with on-site weekly execution tracking workbooks (`.XLSX`), delivering real-time Earned Value Management (EVM), automated schedule updating, interactive native S-curves, logic integrity auditing, and publication-quality pure-white executive PDF / Excel reporting.

---

## 🌟 Key Architecture & Highlights

1. **Authentic WinUI 3 Navigation Rail & Theme Engine**:
   - Live Windows 11 DWM material switching: **Mica (`DWMSBT_MAINWINDOW`)**, **Mica Old / Mica Alt (`DWMSBT_TABBEDWINDOW`)**, **Acrylic**, and **Dark Solid**.
   - Collapsible navigation rail (compact 48px ↔ expanded 210px) with top Hamburger toggle button (`☰`).
   - Active view highlighted with bright vertical cyan/accent pill indicator (`#60CDFF` / `#0078D4`) and rounded pill background.
   - Pinned bottom controls: **Help & Guidance** (`?`) and **Project Settings** (`⚙`).

2. **Vortex PT Status Footer Bar**:
   - Status indicator dot (● Ready / Calculating / Error) + status message.
   - Active selection context (`No selection`, `Activity: ...`, `Cluster: ...`).
   - Live metrics readout (`BAC`, `EV`, `SPI`, `Data Date`, `OOS`, `Database Status`).

3. **Embedded SQLite Database Persistence & Historical Trends**:
   - Automatically stores every recalculation as an immutable weekly snapshot in `vortex_controls.db`.
   - **History & Trends Dashboard**: multi-period EVM progression chart, progress velocity (%/week), and database snapshot log.

4. **Right-Docked Master-Detail Inspector Pane**:
   - Directly inspired by modern WinUI 3 master-detail patterns (e.g., `FluentDL`).
   - Clicking any activity in the Lookahead schedule or any cluster in the matrix immediately displays:
     - WBS hierarchy, Activity ID, and Name.
     - Planned Start/Finish vs Actual/Forecast Start/Finish with schedule slip.
     - Total Float & Free Float (highlighting **CRITICAL PATH** in red if Float ≤ 0).
     - Physical % Complete and Earned Value budget contribution (BAC & EV).
     - Full Predecessor and Successor logic ties with link types (FS, SS, FF) and lags.

3. **100% In-App Native Dashboard (No Web Browser Inside App)**:
   - Built entirely with native PySide6 widgets: responsive KPI cards, high-DPI vector S-Curve widget with hover crosshair and tooltips, quick cluster performance summary, and smooth data tables.
   - Zero dependency on external web browsers or HTML files to view the dashboard inside the desktop app.

4. **Dedicated Pure-White Executive PDF Generator**:
   - Built directly using **ReportLab** and **Matplotlib** on a **crisp white canvas (`#FFFFFF`)**.
   - Solves the dark-webpage print issue completely: high-contrast dark typography (`#0F172A`), blue corporate accent rules, executive EVM scorecards, vector S-Curve with data-date line, cluster breakdown tables, out-of-sequence logic risk audits, running headers/footers with page numbering ("Page X of Y"), and executive sign-off blocks.

5. **Pristine Zero-Data Launch State**:
   - The application launches in a clean, professional state without pre-loaded or hardcoded demo projects.
   - Welcoming onboarding hero card with drag-and-drop file ingestion: drop your Primavera P6 Baseline (`.XER`) and weekly progress sheet (`.XLSX`) directly onto the window.

6. **Primavera P6 XER Engine ([`core/xer_engine.py`](file:///d:/PT%20Design/Programes/mangemnt-beast/core/xer_engine.py))**:
   - Parses and serializes standard Oracle Primavera P6 `.XER` export format (`TASK`, `TASKRSRC`, `PROJECT`, `TASKPRED`, `PROJWBS`).
   - Updates physical % complete, actual start/finish dates, remaining durations, and recalculates resource costs.
   - Generates valid `.XER` files directly loadable into Primavera P6.

7. **Weekly Site Excel Importer ([`core/excel_importer.py`](file:///d:/PT%20Design/Programes/mangemnt-beast/core/excel_importer.py))**:
   - Reads multi-cluster workbooks (`Cluster`, `Cluster C09`..`C18`) or unified progress sheets.
   - Fuzzy header detection in English and Arabic (`Activity ID`, `Performance % Complete`, `Start`, `Finish`, etc.).
   - Date sanitation and flip protection against inverted day/month values.

8. **Multi-Tab Formatted Excel Workbook ([`core/excel_exporter.py`](file:///d:/PT%20Design/Programes/mangemnt-beast/core/excel_exporter.py))**:
   - 6 formatted sheets: Executive Dashboard, Cluster Progress, Discipline Breakdown, Lookahead & Delays, Out-of-Sequence Ties, and S-Curve.

---

## 🚀 Quick Start

### 1. Launch with One Click
Double-click [`Vortex Controls.bat`](file:///d:/PT%20Design/Programes/mangemnt-beast/Vortex%20Controls.bat) or [`run_app.bat`](file:///d:/PT%20Design/Programes/mangemnt-beast/run_app.bat) to launch the app immediately.

### 2. Launch via Terminal
```powershell
cd "d:\PT Design\Programes\mangemnt-beast"
.\.venv\Scripts\python.exe app.py
```
