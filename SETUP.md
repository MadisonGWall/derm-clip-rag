# Setup

## Easiest path

**Just open the deployed app — no install, no API key, no dataset access required:**

➡️ **https://madwall-skin-sight-website.hf.space/**

It runs on Hugging Face Spaces' free tier and may take ~30 seconds to wake from sleep on first load. Everything works out of the box: flashcards, the cross-FST display triplet, the "Ask Questions" live RAG chat (the `OPENAI_API_KEY` is provisioned as a Space secret on the deploy).

The rest of this document is for running from source.

---

## Running locally

### Prerequisites

- macOS (tested on Apple Silicon) or Linux
- ~3 GB free disk space
- Python 3.11
- [conda](https://docs.conda.io/en/latest/miniconda.html) (Miniconda or Anaconda)
- An **OpenAI API key** for the live "Ask Questions" chat path
- **One of**:
  - Stanford DDI dataset access via [Stanford AIMI](https://aimi.stanford.edu/datasets/ddi-diverse-dermatology-images) (full local pipeline), **or**
  - A Hugging Face token with read access to the private thumbnail dataset (app-only, no rebuild)

> **Note for graders:** thumbnails are stored in a private HF Dataset under Stanford's DUA, so a fresh local clone cannot render flashcard images without one of the two access paths above. Use the deployed Space link instead.

### 1. Clone the repo

```bash
git clone https://github.com/madigwall/derm-clip-rag.git
cd derm-clip-rag
```

### 2. Create the Python environment

```bash
conda env create -f environment.yml
conda activate derm-clip
```

Verify PyTorch sees your accelerator:

```bash
python -c "import torch; print('MPS:', torch.backends.mps.is_available(), 'CUDA:', torch.cuda.is_available())"
```

### 3. Provide image data (pick one)

**Option A — DDI dataset (full pipeline).** After getting access via Stanford AIMI:

```bash
mkdir -p data/private/images
# Copy DDI image files into data/private/images/
# Copy ddi_metadata.csv to data/private/labels.csv
```

`data/private/` is gitignored.

**Option B — HF thumbnail snapshot (app only, no rebuild).** Set an HF token with read access to `madwall/ddi-thumbnails-private`:

```bash
export HF_TOKEN=hf_...
```

The app will download the snapshot on first launch and cache it.

### 4. Set your OpenAI API key

The live "Ask Questions" chat calls OpenAI `gpt-4o-mini`:

```bash
export OPENAI_API_KEY=sk-...
```

### 5. Run the app

```bash
streamlit run app.py
```

Opens at http://localhost:8501.

---

## Optional: rebuild artifacts from scratch (DDI dataset required)

These steps regenerate the precomputed embeddings, look-alike statistics, and demo subset. You only need them if you change the dataset or pipeline.

```bash
python scripts/01_split_dataset.py        # reference / query split
python scripts/02_embed_full.py           # CLIP embeddings (~1 min on MPS)
python scripts/03_compute_stats.py        # look-alike statistics
python scripts/04_pick_demo_subset.py     # interactive: approve ~40 images
python scripts/05_embed_demo.py           # embed demo subset
python scripts/06_eval.py                 # top-k accuracy + report
```

### Optional: regenerate cached RAG explanations (requires Ollama)

The flashcard "AI Explanation" text is precomputed and committed at `data/public/rag_cache.json`. You only need this if you change the KB markdown files in `data/public/kb/` or the prompt template.

```bash
ollama pull llama3.1:8b
jupyter notebook notebooks/03_build_rag_cache.ipynb   # then Run All
```

Takes ~5 min. The live "Ask Questions" chat is a separate path that calls OpenAI at runtime — see step 4.

---

## Deploying your own copy to Hugging Face Spaces

1. Create a free account at https://huggingface.co
2. New Space: SDK = Streamlit, hardware = CPU basic (free tier)
3. Connect to your GitHub repo or push to the Space's git remote
4. Add `OPENAI_API_KEY` as a Space secret (Settings → Variables and secrets → New secret)
5. Add `HF_TOKEN` as a Space secret if your thumbnail dataset is private
6. HF auto-installs from `requirements.txt` and runs `app.py`

---

## Troubleshooting

- `torch.backends.mps.is_available()` returns False → check macOS ≥ 12.3 and Python is `arm64`.
- Ollama connection refused → start `ollama serve` in a separate terminal.
- HF Spaces build fails on torch → pin CPU-only: `torch==2.4 --index-url https://download.pytorch.org/whl/cpu`.
- Flashcard images don't render locally → you're missing both DDI imagery and a valid `HF_TOKEN`. See step 3.
