# claude-assisted: condition-pair mean cosine similarity from embeddings_full.pt
"""
Compute pairwise mean cosine similarity between the top-7 condition groups
and save aggregate stats to data/public/lookalike_stats.json.

Aggregate floats only — no per-image data — so the output is DUA-safe and
ships in the public GitHub repo.

Run:
    python scripts/03_compute_stats.py
"""

import json
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
EMB_PATH = ROOT / "data" / "private" / "embeddings_full.pt"
TOP_PATH = ROOT / "data" / "public" / "top_conditions.json"
OUT_PATH = ROOT / "data" / "public" / "lookalike_stats.json"


def main():
    # embeddings_full.pt is pre-filtered to the top-7 conditions at source
    # by scripts/01_filter_labels.py.
    data = torch.load(EMB_PATH)
    embeddings = data["embeddings"]
    labels = data["labels"]

    top_conditions = json.loads(TOP_PATH.read_text())

    emb_by_cond = {
        c: embeddings[[i for i, l in enumerate(labels) if l == c]]
        for c in top_conditions
    }

    matrix = {}
    for a in top_conditions:
        matrix[a] = {}
        for b in top_conditions:
            sim = emb_by_cond[a] @ emb_by_cond[b].T
            matrix[a][b] = round(sim.mean().item(), 4)

    OUT_PATH.write_text(json.dumps({
        "model_id": data["model_id"],
        "conditions": top_conditions,
        "matrix": matrix,
    }, indent=2))

    print(f"Wrote {OUT_PATH.relative_to(ROOT)}")
    for a in top_conditions:
        others = sorted(
            ((b, s) for b, s in matrix[a].items() if b != a),
            key=lambda kv: -kv[1],
        )
        top2 = ", ".join(f"{b}={s:.3f}" for b, s in others[:2])
        print(f"  {a}: {top2}")


if __name__ == "__main__":
    main()
