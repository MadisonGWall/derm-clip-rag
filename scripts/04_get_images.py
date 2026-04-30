# Written by Madison Wall with line debugging assistance by ChatGPT
import pandas as pd
import json
from pathlib import Path

# Paths
ROOT = Path(__file__).resolve().parents[1]
LABELS_PATH = ROOT / "data" / "private" / "labels.csv"
OUT_PATH = ROOT / "data" / "public" / "image_map.json"

# Load labels
df = pd.read_csv(LABELS_PATH)

# Clean condition names
df["condition"] = (df["disease"].str.replace("-", " ", regex=False).str.title())

# Convert FST to string groups
df["fst"] = df["skin_tone"].astype(str)

# Create empty structure
image_map = {}

for _, row in df.iterrows():
    condition = row["condition"]
    fst = row["fst"]
    filename = row["DDI_file"]  # already includes extension

    if condition not in image_map:
        image_map[condition] = {"12": [], "34": [], "56": []}

    image_map[condition][fst].append(filename)

# Save
with open(OUT_PATH, "w") as f:
    json.dump(image_map, f, indent=2)

print(f"Saved to {OUT_PATH}")