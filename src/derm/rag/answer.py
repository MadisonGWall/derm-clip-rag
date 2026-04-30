"""Live RAG answer generation using OpenAI gpt-4o-mini.

Retrieves top-K KB chunks from Chroma, sends them to OpenAI with a
citation-emitting system prompt, and filters sources down to the ones
the model actually cited.
"""
# claude-assisted with most of the module; composes retrieve() with a citation-emitting
# system prompt and calls OpenAI for the live "Ask Questions" chat.

from __future__ import annotations

import os
import re
from functools import lru_cache

from .retriever import retrieve

TOP_K = 5 # written by Madison
OPENAI_MODEL = "gpt-4o-mini" # written by Madison

# Claude assisted with overall prompt. Madison debugged relational precison, hallucinated sources,
# tone, and compare/contrast structure. 
SYSTEM_PROMPT = (
    "You are SkinSight AI, a dermatology study assistant for medical students. "
    "Answer the user's question using ONLY the numbered context passages "
    "provided. Cite every clinical claim with the matching number in square "
    "brackets, placed INLINE immediately after the claim it supports. For "
    "compare-and-contrast claims about two conditions, write each clause "
    "as full descriptive prose with inline citations: 'SCC in situ often "
    "presents as a scaly plaque with orange-red color [1], which differs "
    "from the dull tan/brown of SK [2].' Do NOT use shorthand like "
    "'X [1] vs. Y [2]' — always use complete descriptive sentences. "
    "Never let a single source cover claims about a different condition — "
    "if a clause makes a claim about SK, an SK source must be cited right "
    "after that clause. Always use a real number that matches a passage; "
    "never write a literal placeholder. When the question asks about a "
    "condition's clinical meaning, workflow, or characteristics ('what's "
    "the treatment,' 'next steps,' 'is this cancerous/malignant/benign,' "
    "'is this contagious,' 'how serious is this'), DO answer educationally "
    "using the passages (with inline citations). "
    "Don't refuse on personal-advice framing; the audience is medical "
    "students learning clinical reasoning. "
    "Cover at most TWO conditions per answer. If the question is generic "
    "and several conditions appear in the context, pick the two with the "
    "strongest retrieval support — typically sources [1] and [2], which "
    "are ranked highest and often have the most chunks. Briefly name-drop "
    "the others present in the context with an offer to expand (e.g., 'I "
    "can also cover X if helpful'). Only REFUSE CLEARLY when the knowledge "
    "base genuinely lacks content on the topic — refer to 'my knowledge "
    "base' rather than 'the context,' briefly list the conditions you CAN "
    "discuss, and offer to compare those. Do NOT infer about absent topics "
    "from related sources.\n\n"
    "Match the relational precision of the source: if a passage describes "
    "an association or uses parenthetical correlated markers (e.g. "
    "'lighter skin tones (often with blue eyes)'), do NOT upgrade it to a "
    "causal claim like 'due to X' or 'because of X' — preserve the looser "
    "relationship. Use causal language only when the source explicitly "
    "describes a mechanism (e.g. HPV → verruca, UV → SCC).\n\n"
    "STYLE:\n"
    "- 2–4 short paragraphs of plain prose, or comparison bullets when "
    "side-by-side contrast is helpful.\n"
    "- Comparison bullets use this structure: "
    "'• **<feature label>**: <full descriptive sentence with inline "
    "citations>'. Bold ONLY the feature label preceding the colon "
    "(e.g. '• **Color and texture**: …', '• **Border characteristics**: …'). "
    "Do NOT bold condition names inside the sentence.\n"
    "- Inline citations only — do NOT add a 'Sources:' footer; the UI "
    "renders source metadata separately.\n"
    "- Friendly but clinical. Preserve hedges (may, can, often) and exact "
    "descriptors (pearly, well-defined, atypical).\n"
    "- Educational tone, never diagnostic — this is a study tool."
)


def _format_context_and_sources(
    chunks: list[dict],
) -> tuple[str, list[dict]]:
    """Number chunks by *unique source*, not by chunk. Two BCC sections both
    cite as [1]; an SK section is [2]. Keeps the LLM's comparison crisp and
    the tooltip list duplicate-free."""
    sources: list[dict] = []
    url_to_idx: dict[str, int] = {}
    parts: list[str] = []
    for c in chunks:
        key = c["url"] or f"{c['source']}::{c['title']}"
        if key not in url_to_idx:
            url_to_idx[key] = len(sources)
            sources.append({
                "source": c["source"],
                "title": c["title"],
                "url": c["url"],
            })
        n = url_to_idx[key] + 1
        parts.append(f"[{n}] {c['title']} — {c['section']}\n{c['text']}")
    return "\n\n".join(parts), sources


# written by Madison
@lru_cache(maxsize=1)
def _openai_client():
    from openai import OpenAI
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def _call_openai(messages: list[dict]) -> str:
    resp = _openai_client().chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0,
        max_tokens=400,
    )
    return resp.choices[0].message.content.strip()


# claude-assisted: history-aware query rewriting before retrieval; resolves
# pronouns ("it", "this") in follow-ups so the retriever sees the actual
# topic instead of treating each turn as standalone.
def _rewrite_query_with_history(query: str, history: list[dict]) -> str:
    """Resolve pronouns and implicit references in follow-ups before
    retrieval. 'How does it differ from melanoma?' becomes 'How does basal
    cell carcinoma differ from melanoma?' so the retriever finds BCC
    chunks instead of guessing at 'it'.
    """
    turns = [m for m in history if m.get("role") in ("user", "assistant")]
    if not turns:
        return query
    convo = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}" for m in turns[-4:]
    )
    rewriter_messages = [
        {
            "role": "system",
            "content": (
                "Rewrite the user's follow-up question as a standalone "
                "search query. Resolve pronouns ('it', 'this', 'they') and "
                "implicit references using the conversation. If the user's "
                "message is a short affirmation ('yes', 'please', 'please "
                "do', 'sure', 'go ahead', 'yes please') and the previous "
                "assistant turn offered to cover specific topics (e.g. 'I "
                "can also cover X and Y if helpful'), rewrite the query as "
                "a request for those offered topics by name (e.g. 'Tell me "
                "about X and Y'). Output ONLY the rewritten query, no "
                "preamble or quotes."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Conversation:\n{convo}\n\n"
                f"Follow-up: {query}\n\nStandalone query:"
            ),
        },
    ]
    try:
        return _call_openai(rewriter_messages).strip()
    except Exception:
        return query


def _filter_to_cited(
    content: str, sources: list[dict]
) -> tuple[str, list[dict]]:
    """Keep only sources the model actually cited, renumbered 1-N in order of
    first appearance. Strips noise from the tooltip list."""
    cited: list[int] = []
    seen: set[int] = set()
    for m in re.finditer(r"\[(\d+)\]", content):
        n = int(m.group(1))
        if n not in seen and 1 <= n <= len(sources):
            seen.add(n)
            cited.append(n)
    if not cited:
        return content, []
    remap = {old: new for new, old in enumerate(cited, 1)}
    new_content = re.sub(
        r"\[(\d+)\]",
        lambda m: f"[{remap.get(int(m.group(1)), int(m.group(1)))}]",
        content,
    )
    new_sources = [sources[old - 1] for old in cited]
    return new_content, new_sources


def answer(query: str, history: list[dict] | None = None) -> dict:
    search_query = _rewrite_query_with_history(query, history or [])
    chunks = retrieve(search_query, k=TOP_K)
    context, sources = _format_context_and_sources(chunks)

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in (history or [])[-6:]:
        if m["role"] in ("user", "assistant"):
            messages.append({"role": m["role"], "content": m["content"]})
    messages.append({
        "role": "user",
        "content": f"Context:\n{context}\n\n---\nQuestion: {query}",
    })

    try:
        content = _call_openai(messages)
    except Exception as e:
        return {
            "role": "assistant",
            "content": f"_Couldn't reach OpenAI: {e}_",
            "sources": [],
        }

    content, sources = _filter_to_cited(content, sources)
    return {"role": "assistant", "content": content, "sources": sources}
