# Setup

Step-by-step instructions to run derm-clip-rag locally and deploy to Hugging Face Spaces.

## Prerequisites

- macOS (tested on Apple Silicon) or Linux
- ~3 GB free disk space
- Python 3.11
- [conda](https://docs.conda.io/en/latest/miniconda.html) (Miniconda or Anaconda)
- [Ollama](https://ollama.com) — only required if regenerating the cached RAG explanations
- Stanford DDI dataset access via [Stanford AIMI](https://aimi.stanford.edu/datasets/ddi-diverse-dermatology-images)

## 1. Clone the repo

```bash
git clone https://github.com/madigwall/derm-clip-rag.git
cd derm-clip-rag
```

## 2. Create the Python environment

```bash
conda env create -f environment.yml
conda activate derm-clip
```

Verify PyTorch sees your GPU:

```bash
python -c "import torch; print('MPS:', torch.backends.mps.is_available(), 'CUDA:', torch.cuda.is_available())"
```

## 3. Place the dataset

After getting access via Stanford AIMI:

```bash
mkdir -p data/private/images
# Copy DDI image files into data/private/images/
# Copy ddi_metadata.csv to data/private/labels.csv
```

`data/private/` is gitignored.

## 4. Run the local pipeline

```bash
python scripts/01_split_dataset.py        # reference / query split
python scripts/02_embed_full.py           # CLIP embeddings (~1 min on MPS)
python scripts/03_compute_stats.py        # look-alike statistics
python scripts/04_pick_demo_subset.py     # interactive: approve ~40 images
python scripts/05_embed_demo.py           # embed demo subset
python scripts/06_eval.py                 # top-k accuracy + report
```

## 5. Generate cached RAG explanations (optional, one-time, requires Ollama)

The flashcard "AI Explanation" text is precomputed and committed at `data/public/rag_cache.json`. You only need to run this if you change the KB markdown files in `data/public/kb/` or the prompt templates in the notebook.

```bash
ollama pull llama3.1:8b
jupyter notebook notebooks/03_build_rag_cache.ipynb   # then Run All
```

Takes ~5 min. (The live "Ask Questions" chat is a separate path that calls OpenAI at runtime — see step 6.)

## 6. Run the app locally

The live "Ask Questions" chat calls OpenAI `gpt-4o-mini`, so set your OpenAI API key in your shell environment:

```bash
export OPENAI_API_KEY=sk-...
```

Then start the app:

```bash
streamlit run app.py
```

Opens at http://localhost:8501.

## 7. Deploy to Hugging Face Spaces

1. Create a free account at https://huggingface.co
2. New Space: SDK = Streamlit, hardware = CPU basic (free tier)
3. Connect to your GitHub repo or push to the Space's git remote
4. Add `OPENAI_API_KEY` as a Space secret (Settings → Variables and secrets → New secret)
5. HF auto-installs from `requirements.txt` and runs `app.py`

## Troubleshooting

- `torch.backends.mps.is_available()` returns False → check macOS ≥ 12.3 and Python is `arm64`.
- Ollama connection refused → start `ollama serve` in a separate terminal.
- HF Spaces build fails on torch → pin CPU-only: `torch==2.4 --index-url https://download.pytorch.org/whl/cpu`.
