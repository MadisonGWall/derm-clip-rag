"""
Local-only inspection of the DDI dataset metadata.
Prints aggregate summary info you can choose to share back with Claude.
Reads NO image files. Reads only the label CSV.

Usage:
    cd /Users/madisonwall/Downloads/ml_final/derm-clip-rag
    conda activate derm-clip
    python scripts/00_inspect_dataset.py

Output is printed to your terminal only. Nothing is sent anywhere.
"""

from pathlib import Path
from collections import Counter
import csv

CSV_PATH = Path("/Users/madisonwall/Downloads/ml_final/ddi_metadata.csv")


def main() -> None:
    with CSV_PATH.open() as f:
        rows = list(csv.DictReader(f))

    print(f"Total rows:    {len(rows)}")
    print(f"Columns:       {list(rows[0].keys())}")
    print()

    diseases = Counter(r["disease"] for r in rows)
    print(f"Unique diseases: {len(diseases)}")
    print()
    print("Disease distribution (sorted by count):")
    for disease, n in diseases.most_common():
        print(f"  {n:4d}  {disease}")
    print()

    print("Malignant / benign:")
    for value, n in Counter(r["malignant"] for r in rows).most_common():
        print(f"  {n:4d}  malignant={value}")
    print()

    print("Skin tone (Fitzpatrick group):")
    for value, n in Counter(r["skin_tone"] for r in rows).most_common():
        print(f"  {n:4d}  skin_tone={value}")


if __name__ == "__main__":
    main()
