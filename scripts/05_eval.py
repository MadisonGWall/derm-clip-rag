# claude-assisted: top-K retrieval accuracy on a stratified 80/20 reference/query split
"""
Evaluate zero-shot CLIP image-image retrieval on the top-7 conditions.

Stratified 80/20 reference/query split (seed=42):
- 80% of each condition's images → reference set
- 20% → queries; for each, find K nearest in the reference set by cosine similarity
- Score top-K retrieval accuracy (correct condition appears in top K)
- Tally which condition was retrieved when the top-1 was wrong

No training. CLIP is frozen. The split exists to prevent self-matches.

Run:
    python scripts/06_eval.py
"""

import json
from pathlib import Path

import torch
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
EMB_PATH = ROOT / "data" / "private" / "embeddings_full.pt"
OUT_PATH = ROOT / "data" / "public" / "eval_results.json"

SEED = 42
TEST_SIZE = 0.2
TOP_KS = (1, 3, 5)


def main():
    # embeddings_full.pt is filtered to the top-7 conditions at source
    # by scripts/01_filter_labels.py, so no further condition filter is needed.
    data = torch.load(EMB_PATH)
    embs = data["embeddings"]
    lbls = data["labels"]

    ref_idx, qry_idx = train_test_split(
        list(range(len(lbls))),
        test_size=TEST_SIZE,
        stratify=lbls,
        random_state=SEED,
    )
    ref_emb = embs[ref_idx]
    ref_lbl = [lbls[i] for i in ref_idx]
    qry_emb = embs[qry_idx]
    qry_lbl = [lbls[i] for i in qry_idx]

    sims = qry_emb @ ref_emb.T
    _, topk_idx = torch.topk(sims, k=max(TOP_KS), dim=1)

    accuracy = {}
    confusion = {}
    for k in TOP_KS:
        hits = 0
        for i, true_label in enumerate(qry_lbl):
            top_k_labels = [ref_lbl[j.item()] for j in topk_idx[i, :k]]
            if true_label in top_k_labels:
                hits += 1
            if k == 1 and top_k_labels[0] != true_label:
                key = f"{true_label}__{top_k_labels[0]}"
                confusion[key] = confusion.get(key, 0) + 1
        accuracy[f"top_{k}_accuracy"] = round(hits / len(qry_lbl), 4)

    OUT_PATH.write_text(json.dumps({
        "metric": "top_k_retrieval_accuracy",
        "model_id": data["model_id"],
        "split": "stratified_80_20",
        "split_seed": SEED,
        "n_reference": len(ref_idx),
        "n_query": len(qry_idx),
        **accuracy,
        "confusion_when_top_1_wrong": dict(sorted(confusion.items(), key=lambda kv: -kv[1])),
    }, indent=2))

    print(f"Wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"  reference: {len(ref_idx)}  query: {len(qry_idx)}")
    for k in TOP_KS:
        print(f"  top-{k} accuracy: {accuracy[f'top_{k}_accuracy']:.4f}")
    print("  most-frequent wrong retrievals (top-1):")
    for key, count in sorted(confusion.items(), key=lambda kv: -kv[1])[:5]:
        print(f"    {key}: {count}")


if __name__ == "__main__":
    main()
