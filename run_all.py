"""Run the whole analysis: SQL -> charts -> Excel -> deck. Usage: python run_all.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import charts
import deck
import excel
import run_sql

if __name__ == "__main__":
    run_sql.run_all()
    charts.make_all()
    excel.build()
    deck.build()
    print("Done. Outputs are in outputs/. To export the deck to PDF on Windows run:")
    print("  powershell -ExecutionPolicy Bypass -File src/export_pdf.ps1")
