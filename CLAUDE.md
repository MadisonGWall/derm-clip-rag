# derm-clip-rag

Educational dermatology study tool called SkinSight AI: CLIP image retrieval + LangChain RAG explanations, deployed as a Streamlit flashcard web app on Hugging Face Spaces. School project for madisonwall + portfolio piece for internships.

## Working rules

**Confirm before writing files.** Before calling Write, Edit, or NotebookEdit on any file in this project, show the proposed content in chat and wait for explicit confirmation. Read, Bash (read-only), Grep, Glob do not need pre-confirmation.

**Don't read patient data.** The Stanford DDI dataset at `/Users/madisonwall/Downloads/ml_final/ddi_metadata.csv` and `/Users/madisonwall/Downloads/ml_final/ddidiversedermatologyimages/` is under a Stanford DUA that prohibits redistribution. Treat it as PHI-equivalent.
- Do NOT use Read on image files
- Do NOT read more rows of `ddi_metadata.csv` than the user explicitly pastes
- Do NOT run scripts that surface dataset content back through tool output
- DO write code that reads/processes data locally; user runs it and shares aggregate summaries in her own words
- Notebook cell outputs containing patient-derived data must be cleared before commit

## Key paths

- Project root: `/Users/madisonwall/Downloads/ml_final/derm-clip-rag/`
- Full dataset (gitignored, never deploy): currently lives at `/Users/madisonwall/Downloads/ml_final/ddidiversedermatologyimages/` and `ddi_metadata.csv`
- Public artifacts (deploy to HF Spaces): `data/public/`
- Plan file (outside this repo): `/Users/madisonwall/.claude/plans/i-want-to-build-enchanted-bachman.md`

## Stack

PyTorch (MPS) + open_clip (ViT-B/32) for CLIP embeddings; LangChain + Chroma + sentence-transformers/all-MiniLM-L6-v2 for the RAG knowledge base; Ollama (local, llama3.1:8b) for one-time explanation generation; Streamlit for the deployed UI on Hugging Face Spaces.

## Brand colors

Reference palette for the SkinSight AI brand. Use the simple names in chat (e.g. "make this violet").

| Name | Hex | Notes |
|---|---|---|
| `violet` | `#A78BFA` | Primary purple — logo, primary CTAs, active links |
| `lavender` | `#C084FC` | Lighter purple — accents, hover states |
| `pink` | `#F472B6` | Pink — gradient endpoint, "dermatology" accent |
| `coral` | `#FFB8A2` | Salmon/coral — gradient endpoint |
| `peach` | `#FFD6A5` | Light peach — soft warm accent |
| `sky` | `#9EC5FD` | Sky blue — cool accent (brand asset labels this `#F6F4FF`, but the swatch is visibly sky blue; use `#9EC5FD`) |
| `ink` | `#1F2937` | Dark navy — body text, headings |

Typography: **Poppins** (700/600) for headings; **Inter** (400/500/600) for body.
