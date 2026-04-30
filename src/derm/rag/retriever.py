"""Live retrieval over the prebuilt KB Chroma index built by
notebooks/03_build_rag_cache.ipynb."""
# # claude-assisted with most of the module; wraps the offline-built Chroma index for
# runtime retrieval and returns the metadata shape the chat bubble expects.

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

ROOT = Path(__file__).resolve().parents[3]
CHROMA_DIR = ROOT / "data" / "public" / "kb_chroma"
COLLECTION = "derm_kb"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
# function written by Madison
def _vectorstore() -> Chroma:
    return Chroma(
        persist_directory=str(CHROMA_DIR),
        collection_name=COLLECTION,
        embedding_function=HuggingFaceEmbeddings(model_name=EMBED_MODEL),
    )


def retrieve(query: str, k: int = 5) -> list[dict]:
    docs = _vectorstore().max_marginal_relevance_search(
        query, k=k, fetch_k=20, lambda_mult=0.7
    )
    return [
        {
            "text": d.page_content,
            "source": d.metadata.get("source", ""),
            "title": d.metadata.get("condition_name", ""),
            "url": d.metadata.get("url", ""),
            "condition": d.metadata.get("condition_slug", ""),
            "section": d.metadata.get("section", ""),
        }
        for d in docs
    ]
