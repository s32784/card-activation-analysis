"""Load the CSV into SQLite and run the SQL files in order.

Each SQL file is split into blocks by lines starting with `-- name: <block_name>`.
A block that ends in a SELECT is saved to data/processed/<block_name>.csv;
other blocks (CREATE / DROP) are just executed.
"""
import re
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "BankChurners.csv"
DB_PATH = ROOT / "data" / "processed" / "cards.db"
SQL_DIR = ROOT / "sql"
OUT_DIR = ROOT / "data" / "processed"

SQL_FILES = ["01_create_table.sql", "02_data_quality.sql", "03_segmentation.sql", "04_drivers.sql"]


def connect():
    return sqlite3.connect(DB_PATH)


def load_csv(con):
    """Read the raw CSV, drop the two leftover model columns, insert into `customers`."""
    df = pd.read_csv(RAW_CSV)
    leftover = [c for c in df.columns if c.startswith("Naive_Bayes_Classifier")]
    df = df.drop(columns=leftover)
    df.to_sql("customers", con, if_exists="append", index=False)
    return len(df), leftover


def split_blocks(sql_text):
    """Return [(name, sql)] — text before the first `-- name:` gets the name None."""
    parts = re.split(r"^-- name:\s*(\w+)\s*$", sql_text, flags=re.MULTILINE)
    blocks = [(None, parts[0])]
    for i in range(1, len(parts), 2):
        blocks.append((parts[i], parts[i + 1]))
    return blocks


def statements(sql):
    """The SQL statements in a block, with comments removed."""
    no_comments = re.sub(r"--[^\n]*", "", sql)
    return [s.strip() for s in no_comments.split(";") if s.strip()]


def run_file(con, filename):
    """Run one SQL file; return {block_name: DataFrame} for blocks that return rows."""
    results = {}
    for name, sql in split_blocks((SQL_DIR / filename).read_text(encoding="utf-8")):
        stmts = statements(sql)
        if not stmts:
            continue
        last = stmts[-1]
        if name and re.match(r"^(SELECT|WITH)\b", last, flags=re.IGNORECASE):
            for s in stmts[:-1]:  # setup statements before the final query
                con.execute(s)
            df = pd.read_sql_query(last, con)
            df.to_csv(OUT_DIR / f"{name}.csv", index=False)
            results[name] = df
        else:
            con.executescript(sql)
    con.commit()
    return results


def run_all():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = connect()
    results = {}
    results.update(run_file(con, "01_create_table.sql"))
    n_rows, dropped = load_csv(con)
    print(f"Loaded {n_rows} rows; dropped columns: {len(dropped)}")
    for f in SQL_FILES[1:]:
        results.update(run_file(con, f))
        print(f"Ran {f}")
    # customer-level table with segment, for Excel and charts
    seg = pd.read_sql_query("SELECT * FROM customer_segments ORDER BY CLIENTNUM", con)
    seg.to_csv(OUT_DIR / "customers_with_segments.csv", index=False)
    con.close()
    return results


if __name__ == "__main__":
    run_all()
