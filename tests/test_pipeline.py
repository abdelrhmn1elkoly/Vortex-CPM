import os
import sys

BASE_DIR = r"d:\PT Design\Programes\mangemnt-beast"
sys.path.insert(0, BASE_DIR)

from core.project_state import get_project_state
from core.excel_exporter import ExcelExporter
from core.pdf_exporter import PDFExporter
from core.web_dashboard_gen import generate_fluent_html_dashboard

def run_test():
    print("--- Testing Project State & Pipeline ---")
    state = get_project_state()
    bl_path = r"C:\Users\abdel\Downloads\HT-1 b3-Mod.xer"
    xls_path = r"C:\Users\abdel\Downloads\Copy of Hap_Town_Progress_Sheet_Final_All_Clusters(3) (1) (1) (1).xlsx"

    summary = state.load_baseline(bl_path)
    print("1. Baseline loaded:", summary["project_name"], "| Tasks:", summary["task_count"])

    ex_summary = state.load_site_excel(xls_path)
    print("2. Excel loaded:", ex_summary["total_parsed"], "activities | Sheets:", len(ex_summary["sheets_processed"]))

    res = state.apply_update_pipeline("2026-10-29")
    a = res["analytics"]
    print("3. Pipeline executed!")
    print(f"   BAC: {a['bac']/1e6:.2f}M EGP")
    print(f"   PV:  {a['pv']/1e6:.2f}M EGP ({a['planned_pct']:.2f}%)")
    print(f"   EV:  {a['ev']/1e6:.2f}M EGP ({a['actual_pct']:.2f}%)")
    print(f"   SPI: {a['spi']:.2f} | SV: {a['sv']/1e6:+.2f}M EGP")
    print(f"   OOS count: {a['oos_count']}")
    print(f"   Clusters: {len(a['clusters'])} | Disciplines: {len(a['disciplines'])}")

    out_dir = os.path.join(BASE_DIR, "test_output")
    os.makedirs(out_dir, exist_ok=True)

    # Test Excel export
    excel_out = os.path.join(out_dir, "HPT_Weekly_Report_2026-10-29.xlsx")
    ExcelExporter.export(a, excel_out)
    print("4. Excel export generated:", os.path.exists(excel_out), f"({os.path.getsize(excel_out):,} bytes)")

    # Test HTML export
    html_out = os.path.join(out_dir, "AutoPlan_Studio_Dashboard_2026-10-29.html")
    generate_fluent_html_dashboard(a, html_out)
    print("5. HTML dashboard generated:", os.path.exists(html_out), f"({os.path.getsize(html_out):,} bytes)")

    # Test PDF export via Edge Headless
    pdf_out = os.path.join(out_dir, "HPT_Executive_Report_2026-10-29.pdf")
    ok, msg = PDFExporter.export_pdf(a, pdf_out)
    print("6. PDF export result:", ok, "| File exists:", os.path.exists(pdf_out), f"({os.path.getsize(pdf_out) if os.path.exists(pdf_out) else 0:,} bytes)")
    print("   Message:", msg)

    # Test Updated XER export
    xer_out = os.path.join(out_dir, "HT-1_BL_UPDATED_2026-10-29.xer")
    state.xer_engine.export_xer(xer_out)
    print("7. Updated XER exported:", os.path.exists(xer_out), f"({os.path.getsize(xer_out):,} bytes)")

if __name__ == "__main__":
    run_test()
