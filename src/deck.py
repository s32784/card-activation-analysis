"""Build the 7-slide client deck. All numbers are read from the SQL output CSVs."""
from pathlib import Path

import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
CHARTS = ROOT / "outputs" / "charts"
OUT = ROOT / "outputs" / "card_activation_deck.pptx"

ACCENT = RGBColor(0x1A, 0x3E, 0x8C)
DARK = RGBColor(0x2B, 0x2B, 0x2B)
GREY = RGBColor(0x6B, 0x6B, 0x6B)


def read(name):
    return pd.read_csv(DATA / f"{name}.csv")


def numbers():
    """Collect every figure used in the deck (and README) in one place."""
    seg = read("segment_summary").set_index("segment")
    seg.index = [s.split(". ", 1)[1] for s in seg.index]
    ina = read("attr_by_inactive").set_index("months_inactive")
    con = read("attr_by_contacts").set_index("contacts_12m")
    act = read("activity_change_by_status").set_index("status")
    band = read("attr_by_ct_change_band").set_index("ct_change_band")
    ew = read("early_warning_combo").set_index("group_name")
    flagged = ew.loc[[i for i in ew.index if i.startswith("Flagged")][0]]
    not_flagged = ew.loc["Not flagged"]
    base = read("dq_row_count").iloc[0]
    return dict(seg=seg, ina=ina, con=con, act=act, band=band, flagged=flagged,
                not_flagged=not_flagged, base=base)


def add_title(slide, text, size=24):
    box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(1.0))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = True
    p.font.color.rgb = DARK
    line = slide.shapes.add_shape(1, Inches(0.5), Inches(1.3), Inches(1.2), Inches(0.06))
    line.fill.solid()
    line.fill.fore_color.rgb = ACCENT
    line.line.fill.background()


def add_text(slide, x, y, w, h, lines, size=14, color=DARK, bold_first=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.font.bold = bold_first and i == 0
        p.space_after = Pt(6)
    return box


def add_footer(slide, text="Source: Kaggle 'Credit Card Customers' (BankChurners), n = 10,127 customers; author's analysis"):
    add_text(slide, 0.5, 7.0, 12, 0.4, [text], size=9, color=GREY)


def chart_slide(prs, title, chart, takeaway):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, title)
    s.shapes.add_picture(str(CHARTS / chart), Inches(0.5), Inches(1.6), width=Inches(8.4))
    add_text(s, 9.2, 1.8, 3.7, 4.8, ["So what?"] + takeaway, size=13, bold_first=True)
    add_footer(s)
    return s


def build():
    n = numbers()
    seg, ina, con, act, band = n["seg"], n["ina"], n["con"], n["act"], n["band"]
    risk, low = seg.loc["At risk"], seg.loc["Low-activity"]
    churned, retained = act.loc["Attrited Customer"], act.loc["Existing Customer"]
    down60, flat = band.loc["1. down >60%"], band.loc["5. flat or up"]
    fl, nf = n["flagged"], n["not_flagged"]

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]

    # 1. Title
    s = prs.slides.add_slide(blank)
    add_text(s, 0.8, 2.4, 11.5, 1.2, ["Raising card usage: segment-level diagnostic"], size=36, bold_first=True)
    add_text(s, 0.8, 3.6, 11.5, 1.0,
             ["Credit card activation & loyalty analysis for a Polish retail bank (fictional client)",
              "Portfolio project, public dataset"], size=16, color=GREY)
    bar = s.shapes.add_shape(1, Inches(0.8), Inches(2.2), Inches(1.5), Inches(0.08))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT
    bar.line.fill.background()

    # 2. Executive summary
    s = prs.slides.add_slide(blank)
    add_title(s, f"Falling usage predicts churn: an early-warning trigger could reach "
                 f"{fl.pct_of_all_attrited:.0f}% of churners in {fl.pct_of_base:.0f}% of the base", size=22)
    add_text(s, 0.5, 1.6, 6.0, 5.2, [
        "What we found",
        f"1. Customers whose Q4 transactions fell by more than 60% vs Q1 churned at "
        f"{down60.attrition_rate_pct:.1f}%, vs {flat.attrition_rate_pct:.1f}% for those with flat or rising use.",
        f"2. Attrition rises from {ina.loc[1].attrition_rate_pct:.1f}% at 1 inactive month to "
        f"{ina.loc[3].attrition_rate_pct:.1f}% at 3 and {ina.loc[4].attrition_rate_pct:.1f}% at 4 months.",
        f"3. Every contact with the bank adds risk: {con.loc[0].attrition_rate_pct:.1f}% attrition at 0 contacts, "
        f"{con.loc[3].attrition_rate_pct:.1f}% at 3, {con.loc[5].attrition_rate_pct:.1f}% at 5.",
        f"The 'At risk' segment is {risk.pct_of_base:.1f}% of customers but {risk.pct_of_all_attrited:.1f}% of churners.",
    ], size=13, bold_first=True)
    add_text(s, 6.9, 1.6, 6.0, 5.2, [
        "What we recommend",
        f"1. Early-warning trigger: flag customers with 3+ inactive months AND 3+ bank contacts "
        f"({fl.n_customers:,.0f} customers, {fl.attrition_rate_pct:.1f}% attrition) and the 'At risk' segment; "
        f"contact them with a retention offer.",
        f"2. Activation offer for the 'Low-activity' segment ({low.n_customers:,.0f} customers, "
        f"{low.attrition_rate_pct:.1f}% attrition): reward reaching a monthly transaction target.",
        "3. Service-contact review: treat the 3rd contact in a year as a churn signal; "
        "find and fix the top contact reasons.",
    ], size=13, bold_first=True)
    add_footer(s)

    # 3. Segments
    chart_slide(prs,
                f"'At risk' customers are {risk.pct_of_base:.1f}% of the base but "
                f"{risk.pct_of_all_attrited:.1f}% of all churners",
                "1_segments.png",
                [f"At risk: {risk.attrition_rate_pct:.1f}% attrition (3+ inactive months and Q4 transactions down 40%+).",
                 f"Low-activity: {low.attrition_rate_pct:.1f}% attrition, the second retention priority.",
                 f"Champions: {seg.loc['Champions'].attrition_rate_pct:.1f}% attrition; "
                 f"Steady users: {seg.loc['Steady users'].attrition_rate_pct:.1f}%."])

    # 4. Finding 1: falling activity
    chart_slide(prs,
                f"Finding 1: {churned.pct_trans_down_40pct_plus:.1f}% of churners had cut transactions by 40%+ "
                f"(vs {retained.pct_trans_down_40pct_plus:.1f}% of retained)",
                "4_ct_change_churned_vs_retained.png",
                [f"Median Q4/Q1 transaction ratio: {churned.median_ct_change_q4_q1:.2f} for churners vs "
                 f"{retained.median_ct_change_q4_q1:.2f} for retained.",
                 f"Customers down >60% churned at {down60.attrition_rate_pct:.1f}% "
                 f"vs {flat.attrition_rate_pct:.1f}% when flat or up.",
                 "A drop in usage is visible in the data the bank already has: it can be monitored monthly."])

    # 5. Finding 2: inactivity
    chart_slide(prs,
                f"Finding 2: attrition rises from {ina.loc[1].attrition_rate_pct:.1f}% at 1 inactive month to "
                f"{ina.loc[4].attrition_rate_pct:.1f}% at 4 months",
                "2_attrition_by_inactive.png",
                [f"{ina.loc[3].n_customers:,.0f} customers sit at exactly 3 inactive months "
                 f"({ina.loc[3].attrition_rate_pct:.1f}% attrition): the largest pool to act on.",
                 "5-6 months and 0 months are small groups with noisy rates.",
                 "Act at month 2-3, before the customer has mentally left."])

    # 6. Finding 3: contacts
    chart_slide(prs,
                f"Finding 3: attrition climbs with each bank contact, from {con.loc[0].attrition_rate_pct:.1f}% "
                f"to {con.loc[5].attrition_rate_pct:.1f}% at 5 contacts",
                "3_attrition_by_contacts.png",
                [f"All {con.loc[6].n_customers:,.0f} customers with 6 contacts left.",
                 "Contacts likely reflect unresolved problems (we cannot see the reason in this data).",
                 f"3+ inactive months AND 3+ contacts: {fl.pct_of_base:.1f}% of customers, "
                 f"{fl.pct_of_all_attrited:.1f}% of churners, {fl.attrition_rate_pct:.1f}% attrition "
                 f"(vs {nf.attrition_rate_pct:.1f}% for the rest)."])

    # 7. Recommendations
    s = prs.slides.add_slide(blank)
    add_title(s, "Three actions, each tested against a control group, can show impact within 6 months")
    rows = [
        ("Action", "Target segment", "Metric to track"),
        ("1. Early-warning trigger + retention offer: 3+ inactive months AND 3+ contacts, "
         "or 3+ inactive months with Q4/Q1 transactions < 0.6 ('At risk')",
         f"Flagged ({fl.n_customers:,.0f}, {fl.attrition_rate_pct:.1f}% attrition) and "
         f"At risk ({risk.n_customers:,.0f}, {risk.attrition_rate_pct:.1f}% attrition)",
         "Attrition rate vs. control group"),
        ("2. Activation offer: cashback for reaching N transactions a month for 3 months",
         f"Low-activity ({low.n_customers:,.0f} customers, {low.attrition_rate_pct:.1f}% attrition)",
         "Transactions per active card; activation rate"),
        ("3. Service-contact review: root-cause top contact reasons; senior handling from the 3rd contact",
         f"Customers with 3+ contacts ({con.loc[con.index >= 3].n_customers.sum():,.0f})",
         "Attrition rate of 3+ contact customers; repeat-contact rate"),
    ]
    table = s.shapes.add_table(len(rows), 3, Inches(0.5), Inches(1.7), Inches(12.3), Inches(3.6)).table
    widths = [5.8, 3.6, 2.9]
    for j, w in enumerate(widths):
        table.columns[j].width = Inches(w)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = table.cell(i, j)
            cell.text = val
            para = cell.text_frame.paragraphs[0]
            para.font.size = Pt(13)
            para.font.bold = i == 0
            para.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF) if i == 0 else DARK
            cell.fill.solid()
            cell.fill.fore_color.rgb = ACCENT if i == 0 else RGBColor(0xF3, 0xF4, 0xF7)
    add_text(s, 0.5, 5.6, 12.3, 1.3, [
        "Next steps: (1) agree the trigger rule and offer budget, (2) pilot on a random half of each target "
        "group with the other half as control, (3) read results monthly for 6 months, (4) validate with the "
        "bank's own transaction-level data (exact dates, merchant categories, contact reasons)."], size=13)
    add_footer(s)

    prs.save(OUT)


if __name__ == "__main__":
    build()
