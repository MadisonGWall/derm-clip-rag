# Author: Madison Wall
"""
Filter labels.csv to only include rows from top 7 conditions 
used in project. Then print aggregate row counts
"""
import json
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LABELS_PATH = ROOT / "data" / "private" / "labels.csv"
TOP_PATH = ROOT / "data" / "public" / "top_conditions.json"


def disease_clean(df: pd.DataFrame) -> pd.Series:
    s = df["disease"].str.replace("-", " ", regex=False).str.title()
    return s.str.replace("(Nm)", "(NM)", regex=False)

# claude-assisted: filter labels.csv to top-7
def main() -> None:
    top_conditions = set(json.loads(TOP_PATH.read_text()))
    df = pd.read_csv(LABELS_PATH)
    before_n = len(df)

    clean = disease_clean(df)
    filtered = df[clean.isin(top_conditions)].reset_index(drop=True)
    after_n = len(filtered)

    # Atomic write: temp file + rename, so a crash mid-write doesn't corrupt
    # the original CSV.
    tmp = LABELS_PATH.with_suffix(".csv.tmp")
    filtered.to_csv(tmp, index=False)
    tmp.replace(LABELS_PATH)

    kept_dist = Counter(disease_clean(filtered))
    print(f"Rows before:  {before_n}")
    print(f"Rows kept:    {after_n}")
    print(f"Rows dropped: {before_n - after_n}")
    print()
    print("Distribution kept (sorted by count):")
    for cond, n in sorted(kept_dist.items(), key=lambda x: -x[1]):
        print(f"  {n:4d}  {cond}")

if __name__ == "__main__":
    main()
