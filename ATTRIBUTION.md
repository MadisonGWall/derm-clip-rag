# Attribution

## Dataset

**Stanford Diverse Dermatology Images (DDI)** — Daneshjou, R., Vodrahalli, K., Novoa, R. A., et al. (2022). "Disparities in dermatology AI performance on a diverse, curated clinical image set." *Science Advances*, 8(31).

Governed by the Stanford AIMI Data Use Agreement. **Not redistributed by this repository.** Users must obtain access independently: https://aimi.stanford.edu/datasets/ddi-diverse-dermatology-images

## Model

**CLIP** — Radford, A., Kim, J. W., Hallacy, C., et al. (2021). "Learning Transferable Visual Models From Natural Language Supervision." *ICML.*

OpenAI ViT-B/32 weights loaded via [open_clip](https://github.com/mlfoundations/open_clip) (MIT).

## Knowledge Base Sources

Condition descriptions in `data/public/kb/` are drafted from:

- **DermNet** — https://dermnetnz.org (CC BY-NC-ND 3.0 NZ)
- **American Academy of Dermatology** — https://www.aad.org (educational use)

Wording is paraphrased; content reviewed for clinical accuracy. Educational use within this tool only — not a substitute for professional medical advice.

## Software Libraries

| Library | License | Purpose |
|---|---|---|
| PyTorch | BSD | Tensor ops + CLIP inference |
| open_clip_torch | MIT | CLIP loader + preprocessing |
| LangChain | MIT | RAG pipeline framework |
| Chroma | Apache 2.0 | Vector store |
| sentence-transformers | Apache 2.0 | KB text embeddings |
| Streamlit | Apache 2.0 | Web UI |
| Ollama | MIT | Local LLM (one-time explanation generation) |

## AI Assistance Disclosure

Developed with assistance from **Claude (Anthropic)** for:

- Design discussion and architecture planning
- Boilerplate code generation (`src/`, `scripts/`)
- Documentation drafting

All AI-generated code was reviewed, modified, and tested by the project author. Clinical content in the knowledge base was independently verified against DermNet source material. The author is solely responsible for the design decisions, the final code, and the privacy posture (see `CLAUDE.md` for data-handling rules).

## Citation

```
Wall, M. (2026). derm-clip-rag: A CLIP + RAG dermatology study tool.
GitHub: https://github.com/madigwall/derm-clip-rag
```
