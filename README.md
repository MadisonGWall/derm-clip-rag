---
title: SkinSight AI
emoji: 🔬
colorFrom: purple
colorTo: pink
sdk: streamlit
sdk_version: "1.56.0"
app_file: app.py
pinned: false
short_description: Visual dermatology learning with CLIP retrieval and RAG
---

# derm-clip-rag

> An interactive dermatology study tool combining CLIP visual retrieval with LangChain RAG explanations.

<!-- TODO: replace with actual demo GIF once UI is built -->
<!-- ![Demo](assets/demo.gif) -->

**Live demo:** https://huggingface.co/spaces/madwall/skin-sight-website

## What it Does

derm-clip-rag is an educational flashcard app for medical and pre-medical students learning to recognize common dermatological conditions. The user is shown a derm image and asked to choose the correct diagnosis from four options. **The wrong answer choices are not random — they are the conditions that a CLIP embedding model finds most visually confusable with the correct answer**, drawn from a precomputed look-alike analysis over the Stanford Diverse Dermatology Images (DDI) dataset. After answering, the app reveals the correct label, surfaces visually similar reference images with cosine-similarity scores, and shows a RAG-generated explanation comparing the user's chosen condition to the true condition — including key visual features, common look-alikes, and distinguishing features.

This is **not a diagnostic tool.** It is a study aid for recognition practice.

## Data

The flashcard images are randomly drawn from the Stanford Diverse Dermatology Images (DDI) Dataset which include 656 images that triaged skin disease with diverse skin tones annotated across the Fitzpatrick Skin Type (FST) scale (I-II, III-IV, and V-VI). Source: https://doi.org/10.71718/kqee-3z39

KB comes from DermNet articles with the same name as the condition. Source: https://dermnetnz.org/

## Quick Start

```bash
git clone https://github.com/madigwall/derm-clip-rag.git
cd derm-clip-rag
conda env create -f environment.yml
conda activate derm-clip
streamlit run app.py
```

For full setup including dataset placement and the local pipeline, see [SETUP.md](SETUP.md).

## Architecture

```mermaid
graph LR
  A[Stanford DDI<br/>656 images<br/>private] --> B[CLIP ViT-B/32<br/>PyTorch + MPS]
  B --> C[Embeddings<br/>+ Look-alike Stats]
  C --> D[Sampled<br/>60 images<br/>public]
  E[KB JSONs<br/>DermNet] --> F[LangChain + Chroma]
  F --> G[Cached RAG<br/>Explanations]
  D --> H[Streamlit Flashcard App]
  G --> H
  H --> I[Hugging Face Spaces]
```

Local pipeline runs once on the developer's machine. The deployed app reads precomputed artifacts (image embeddings, look-alike statistics, the Chroma KB index, cached per-flashcard explanations) and makes one live LLM call per user question in the "Ask Questions" chat.

**LLMs in this project:**
- **Live chat ("Ask Questions"):** OpenAI `gpt-4o-mini`, called from [src/derm/rag/answer.py](src/derm/rag/answer.py). Requires `OPENAI_API_KEY`.
- **Cached flashcard explanations:** generated *offline, one time* using local Ollama (`llama3.1:8b`) and committed to `data/public/rag_cache.json`. The deployed app does not call Ollama.

## Video Links

- **Demo video** (non-specialist, no code): _TODO_
- **Technical walkthrough** (code structure, ML techniques): _TODO_

## Evaluation

| Metric | Score |
|---|---|
| Top-1 retrieval accuracy | 28.8% |
| Top-3 retrieval accuracy | 60.3% |
| Top-5 retrieval accuracy | 72.6% |
| Most common look-alike pair | Seborrheic Keratosis and Melanocytic Nevi (12 mutual confusions)|

Full methodology and results: `data/public/eval_results.json` and `notebooks/03_lookalike_analysis.ipynb`.

![alt text](assets/lookalike_heatmap.png)

DDI image counts per condition per Fitzpatrick group, after filtering to the top-7 conditions by sample count.

| Condition | FST I/II | FST III/IV | FST V/VI |
|---|---:|---:|---:|
| Melanocytic Nevi | 47 | 49 | 23 |
| Seborrheic Keratosis | 21 | 18 | 19 |
| Verruca Vulgaris | 26 | 7 | 17 |
| Epidermal Cyst | 16 | 5 | 14 |
| Squamous Cell Carcinoma In Situ | 15 | 10 | 3 |
| Mycosis Fungoides | 3 | 3 | 26 |
| Basal Cell Carcinoma | 7 | 34 | **0** |

Since there were no examples of Basal Cell Carcinoma on the FST V/VI group, in the UI we indicate that there was "No FST V/VI sample in DDI" placeholder rather than just hiding this group to indicate the underrepresentation in the sample.

![alt text](assets/qualitative-images.png)

## Individual Contributions

Solo project by Madison Wall. All design, ML pipeline implementation, RAG knowledge base curation, UI, and documentation are mine. AI assistance disclosed in [ATTRIBUTION.md](ATTRIBUTION.md).

## Limitations & Future Work

- **Demo subset only in deploy.** Only ~40 curated images ship publicly; look-alike statistics displayed reflect analysis over the full dataset.
- **CLIP zero-shot baseline.** No fine-tuning; published accuracy is the realistic baseline for ViT-B/32 zero-shot on the chosen condition set.
- **English-language KB.** RAG explanations sourced from public DermNet content.
- **Not a diagnostic tool.** Recognition trainer only.

## License

The Stanford DDI dataset is governed by its own [Data Use Agreement](https://aimi.stanford.edu/datasets/ddi-diverse-dermatology-images) and is not redistributed by this repository. See [ATTRIBUTION.md](ATTRIBUTION.md) for citation requirements.
