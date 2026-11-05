"""Build outputs/segment_summary.xlsx: Segments, Pivot (static cross-tab + how-to), Data."""
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
OUT = ROOT / "outputs" / "segment_summary.xlsx"

HEADER_FILL = PatternFill("solid", fgColor="1A3E8C")
HEADER_FONT = Font(color="FFFFFF", bold=True)

PIVOT_STEPS = [
    "How to build the real PivotTable in Excel (2 minutes):",
    "1. Go to sheet 'Data', click any cell inside the table, press Ctrl+A.",
    "2. Insert > PivotTable > New Worksheet > OK.",
    "3. Drag 'segment' to Rows, 'Card_Category' to Columns.",
    "4. Drag 'CLIENTNUM' to Values, click it > Value Field Settings > Count.",
    "5. Drag 'Total_Trans_Amt' to Values, click it > Value Field Settings > Average.",
    "6. Optional: drag 'Attrition_Flag' to Filters to look at churned customers only.",
    "The static tables below are the same numbers, computed in SQL (segment_by_card query), to check against.",
]


def _style_header(ws, row, ncols, col0=1):
    for c in range(col0, col0 + ncols):
        cell = ws.cell(row=row, column=c)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(wrap_text=True, vertical="center")


def _autowidth(ws, max_width=40):
    for col in ws.columns:
        width = max(len(str(c.value)) if c.value is not None else 0 for c in col)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max(10, width + 2), max_width)


def build():
    segments = pd.read_csv(DATA / "segment_summary.csv")
    seg_card = pd.read_csv(DATA / "segment_by_card.csv")
    customers = pd.read_csv(DATA / "customers_with_segments.csv")

    counts = seg_card.pivot(index="segment", columns="card_category", values="n_customers").fillna(0).astype(int)
    counts["Total"] = counts.sum(axis=1)
    spend = seg_card.pivot(index="segment", columns="card_category", values="avg_spend")

    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        segments.to_excel(xw, sheet_name="Segments", index=False)
        pd.DataFrame().to_excel(xw, sheet_name="Pivot")
        customers.to_excel(xw, sheet_name="Data", index=False)

    wb = load_workbook(OUT)
    ws = wb["Segments"]
    _style_header(ws, 1, ws.max_column)
    ws.freeze_panes = "B2"
    _autowidth(ws)

    ws = wb["Pivot"]
    for i, line in enumerate(PIVOT_STEPS, start=1):
        ws.cell(row=i, column=1, value=line).font = Font(bold=(i == 1))
    r = len(PIVOT_STEPS) + 2
    ws.cell(row=r, column=1, value="Number of customers: segment x card category").font = Font(bold=True)
    r += 1
    for block, table, fmt in ((r, counts, "0"), (r + len(counts) + 4, spend, "#,##0")):
        if table is spend:
            ws.cell(row=block - 1, column=1, value="Average 12-month spend ($): segment x card category").font = Font(bold=True)
        ws.cell(row=block, column=1, value="segment")
        for j, col in enumerate(table.columns, start=2):
            ws.cell(row=block, column=j, value=col)
        _style_header(ws, block, len(table.columns) + 1)
        for i, (idx, row) in enumerate(table.iterrows(), start=1):
            ws.cell(row=block + i, column=1, value=idx)
            for j, v in enumerate(row, start=2):
                cell = ws.cell(row=block + i, column=j, value=None if pd.isna(v) else float(v))
                cell.number_format = fmt
    ws.column_dimensions["A"].width = 30

    ws = wb["Data"]
    _style_header(ws, 1, ws.max_column)
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = ws.dimensions
    wb.save(OUT)


if __name__ == "__main__":
    build()
