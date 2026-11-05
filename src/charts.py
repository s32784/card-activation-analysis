"""Consulting-style charts. Every number on a chart is read from the SQL output CSVs."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
CHARTS = ROOT / "outputs" / "charts"

ACCENT = "#1A3E8C"   # one accent colour
GREY = "#B8BEC8"
DARK = "#2B2B2B"

plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#888888",
    "axes.titleweight": "bold",
    "axes.titlesize": 13,
    "axes.titlelocation": "left",
})


def read(name):
    return pd.read_csv(DATA / f"{name}.csv")


def _finish(fig, ax, title, subtitle, filename, source=True):
    ax.set_title(title, color=DARK, pad=26)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=10, color="#555555")
    if source:
        fig.text(0.01, 0.01, "Source: Kaggle 'Credit Card Customers' (BankChurners), n = 10,127; author's analysis",
                 fontsize=8, color="#777777")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    CHARTS.mkdir(parents=True, exist_ok=True)
    fig.savefig(CHARTS / filename, dpi=200)
    plt.close(fig)


def _bar_labels(ax, bars, fmt):
    for b in bars:
        ax.annotate(fmt(b.get_height()), (b.get_x() + b.get_width() / 2, b.get_height()),
                    ha="center", va="bottom", fontsize=9, xytext=(0, 2), textcoords="offset points")


def chart_segments():
    df = read("segment_summary")
    labels = [s.split(". ", 1)[1] for s in df.segment]
    risk = df.loc[df.segment.str.contains("At risk")].iloc[0]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6))
    b1 = ax1.bar(labels, df.pct_of_base, color=GREY)
    _bar_labels(ax1, b1, lambda v: f"{v:.1f}%")
    ax1.set_ylabel("% of customers")
    ax1.set_title("Share of customer base", fontsize=11, loc="left")
    colors = [ACCENT if "At risk" in s else GREY for s in df.segment]
    b2 = ax2.bar(labels, df.attrition_rate_pct, color=colors)
    _bar_labels(ax2, b2, lambda v: f"{v:.1f}%")
    ax2.set_ylabel("Attrition rate (%)")
    ax2.set_title("Attrition rate", fontsize=11, loc="left")
    for ax in (ax1, ax2):
        ax.tick_params(axis="x", labelrotation=15)
    fig.suptitle(f"'At risk' customers are {risk.pct_of_base:.1f}% of the base but "
                 f"{risk.pct_of_all_attrited:.1f}% of all churners",
                 x=0.01, ha="left", fontweight="bold", fontsize=13, color=DARK)
    fig.text(0.01, 0.01, "Source: Kaggle 'Credit Card Customers' (BankChurners), n = 10,127; author's analysis",
             fontsize=8, color="#777777")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    CHARTS.mkdir(parents=True, exist_ok=True)
    fig.savefig(CHARTS / "1_segments.png", dpi=200)
    plt.close(fig)


def chart_inactive():
    df = read("attr_by_inactive")
    r1 = df.loc[df.months_inactive == 1].iloc[0]
    r4 = df.loc[df.months_inactive == 4].iloc[0]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    colors = [ACCENT if m in (3, 4) else GREY for m in df.months_inactive]
    labels = [f"{m}\n(n={n:,})" for m, n in zip(df.months_inactive, df.n_customers)]
    bars = ax.bar(labels, df.attrition_rate_pct, color=colors)
    _bar_labels(ax, bars, lambda v: f"{v:.1f}%")
    ax.set_xlabel("Months inactive in the last 12 months")
    ax.set_ylabel("Attrition rate (%)")
    _finish(fig, ax,
            f"Attrition rises from {r1.attrition_rate_pct:.1f}% at 1 inactive month to "
            f"{r4.attrition_rate_pct:.1f}% at 4 months",
            "Attrition rate by months inactive. Note: 0 months (n=29) and 5-6 months are small groups",
            "2_attrition_by_inactive.png")


def chart_contacts():
    df = read("attr_by_contacts")
    r0 = df.loc[df.contacts_12m == 0].iloc[0]
    r5 = df.loc[df.contacts_12m == 5].iloc[0]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    colors = [ACCENT if c >= 3 else GREY for c in df.contacts_12m]
    labels = [f"{c}\n(n={n:,})" for c, n in zip(df.contacts_12m, df.n_customers)]
    bars = ax.bar(labels, df.attrition_rate_pct, color=colors)
    _bar_labels(ax, bars, lambda v: f"{v:.1f}%")
    ax.set_xlabel("Contacts with the bank in the last 12 months")
    ax.set_ylabel("Attrition rate (%)")
    _finish(fig, ax,
            f"Attrition climbs with every bank contact: {r0.attrition_rate_pct:.1f}% at 0 contacts, "
            f"{r5.attrition_rate_pct:.1f}% at 5",
            "Attrition rate by number of contacts. All 54 customers with 6 contacts left",
            "3_attrition_by_contacts.png")


def chart_ct_change():
    df = read("ct_change_distribution")
    status = read("activity_change_by_status").set_index("status")
    churn = df[df.status == "Attrited Customer"].set_index("ct_change_band").pct_of_status
    stay = df[df.status == "Existing Customer"].set_index("ct_change_band").pct_of_status
    bands = sorted(set(df.ct_change_band))
    labels = [b.split(". ", 1)[1] for b in bands]
    x = range(len(bands))
    w = 0.38
    fig, ax = plt.subplots(figsize=(9, 4.6))
    b1 = ax.bar([i - w / 2 for i in x], [churn.get(b, 0) for b in bands], w, color=ACCENT, label="Churned")
    b2 = ax.bar([i + w / 2 for i in x], [stay.get(b, 0) for b in bands], w, color=GREY, label="Retained")
    _bar_labels(ax, b1, lambda v: f"{v:.1f}%")
    _bar_labels(ax, b2, lambda v: f"{v:.1f}%")
    ax.set_xticks(list(x), labels)
    ax.set_xlabel("Change in number of transactions, Q4 vs Q1")
    ax.set_ylabel("% of group")
    ax.legend(frameon=False)
    c = status.loc["Attrited Customer"]
    s = status.loc["Existing Customer"]
    _finish(fig, ax,
            f"{c.pct_trans_down_40pct_plus:.1f}% of churners had cut transactions by 40%+ "
            f"(vs {s.pct_trans_down_40pct_plus:.1f}% of retained)",
            "Distribution of Q4-vs-Q1 transaction change, churned vs retained customers",
            "4_ct_change_churned_vs_retained.png")


def chart_card_spend():
    df = read("attr_by_card")
    fig, ax = plt.subplots(figsize=(9, 4.6))
    bars = ax.bar(df.card_category, df.avg_spend, color=GREY)
    _bar_labels(ax, bars, lambda v: f"${v:,.0f}")
    for b, n in zip(bars, df.n_customers):
        ax.text(b.get_x() + b.get_width() / 2, 150, f"n={n:,}", ha="center", fontsize=8, color=DARK)
    ax.set_ylabel("Average 12-month spend per customer ($)")
    blue = df.loc[df.card_category == "Blue"].iloc[0]
    _finish(fig, ax,
            f"Blue cards are {100 * blue.n_customers / df.n_customers.sum():.1f}% of customers and spend least "
            f"(${blue.avg_spend:,.0f} a year)",
            "Average spend per customer by card tier",
            "5_spend_by_card.png")


def make_all():
    chart_segments()
    chart_inactive()
    chart_contacts()
    chart_ct_change()
    chart_card_spend()


if __name__ == "__main__":
    make_all()
