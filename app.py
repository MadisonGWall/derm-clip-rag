# Written almost entirely by Claude via prompting
import base64
import html
import json
import random
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

ASSETS = Path(__file__).parent / "assets"
ROOT = Path(__file__).parent

@st.cache_data
def load_image_map():
    with open(ROOT / "data" / "public" / "image_map.json") as f:
        return json.load(f)


def _b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


LOGO_SVG_B64 = _b64(ASSETS / "logo.svg")


# Deck of the top-7 DDI conditions by image count (data/public/top_conditions.json).
# Public-knowledge clinical summaries, not patient data. Lookalikes are the top-2
# highest mean-cosine pairs from data/public/lookalike_stats.json — the conditions
# CLIP confuses each card with most often.
DECK_BASE = [
    {
        "name": "Melanocytic Nevi",
        "category": "Benign",
        "frequency": "Common",
        "definition": "Benign, uniformly pigmented macules or papules with regular borders and stable size.",
        "rag": (
            "Melanocytic nevi (moles) are benign proliferations of melanocytes. "
            "Lesions are typically symmetric, uniformly pigmented, with smooth, "
            "regular borders. Most adults have 10–40 nevi; new lesions or change "
            "in an existing nevus warrants ABCDE evaluation to rule out melanoma. "
            "The 'ugly duckling' sign — a nevus that looks unlike the patient's "
            "others — is a sensitive marker for atypia."
        ),
        "lookalikes": ["Seborrheic Keratosis", "Verruca Vulgaris"],
        "feedback": {
            "Seborrheic Keratosis": (
                "Both can be raised and pigmented in older adults — CLIP groups "
                "them tightly (mean cosine 0.78). Differentiator: nevi are "
                "**smooth and uniform** with regular borders. SKs look "
                "**stuck-on** with a dull, **warty** surface and pseudohorn "
                "cysts on dermoscopy."
            ),
            "Verruca Vulgaris": (
                "Both benign, both can be dark. Differentiator: warts have a "
                "**rough, hyperkeratotic** surface with **thrombosed capillaries** "
                "(black dots) and disrupted skin lines. Nevi are **smooth**, "
                "with intact skin markings and uniform pigment."
            ),
        },
    },
    {
        "name": "Seborrheic Keratosis",
        "category": "Benign",
        "frequency": "Common",
        "definition": "Stuck-on, waxy papules with a verrucous surface and sharp demarcation.",
        "rag": (
            "Benign epidermal proliferation common in adults over 40. Lesions look "
            "'pasted on' with a dull, warty surface; dermoscopy shows pseudohorn "
            "cysts and milia-like cysts. Color ranges from skin-toned to dark brown. "
            "Sudden eruption of many lesions (Leser-Trélat sign) can indicate an "
            "underlying internal malignancy and warrants further workup."
        ),
        "lookalikes": ["Verruca Vulgaris", "Squamous Cell Carcinoma In Situ"],
        "feedback": {
            "Verruca Vulgaris": (
                "Both rough, raised, and benign-appearing. Differentiator: SKs "
                "have a **dull, waxy 'stuck-on'** look with pseudohorn cysts on "
                "dermoscopy. Warts have **thrombosed capillaries** (black dots) "
                "and disrupt the skin's normal lines."
            ),
            "Squamous Cell Carcinoma In Situ": (
                "**Higher-stakes confusion** — both are scaly papules/plaques in "
                "older adults (CLIP mean cosine 0.79). Differentiator: SK is "
                "**uniform, dull, and waxy** with sharp borders. SCC in situ "
                "(Bowen's) shows **persistent erythema, irregular borders**, and "
                "resists topical treatment — biopsy if uncertain."
            ),
        },
    },
    {
        "name": "Verruca Vulgaris",
        "category": "Benign",
        "frequency": "Common",
        "definition": "Hyperkeratotic, rough papules from HPV infection, often with thrombosed capillaries.",
        "rag": (
            "Verruca vulgaris (common warts) are benign epidermal growths caused "
            "by human papillomavirus. They appear as hyperkeratotic, rough-surfaced "
            "papules most often on hands, fingers, and knees. Dermoscopy shows "
            "thrombosed capillaries — pinpoint black dots — and disruption of "
            "normal skin markings. Most resolve spontaneously within 1–2 years; "
            "persistent lesions are treated with cryotherapy or salicylic acid."
        ),
        "lookalikes": ["Seborrheic Keratosis", "Basal Cell Carcinoma"],
        "feedback": {
            "Seborrheic Keratosis": (
                "Both benign, raised, and rough on the surface. Differentiator: "
                "warts have **thrombosed capillaries** (black dots) and "
                "**disrupted skin lines** from HPV-driven hyperkeratosis. SKs "
                "look **stuck-on, dull, and waxy** with intact pseudohorn cysts "
                "on dermoscopy."
            ),
            "Basal Cell Carcinoma": (
                "Both can be papular on sun-exposed skin. Differentiator: BCC "
                "is **pearly/translucent** with **arborizing telangiectasias** "
                "and a **rolled border**. Warts are **dull and rough** with "
                "central black dots and no visible vessels."
            ),
        },
    },
    {
        "name": "Basal Cell Carcinoma",
        # claude-assisted: BCC has 0 images in FST 56 in the DDI dataset, so it
        # only renders one round (FST 12 + 34 + a "no sample" placeholder).
        "rounds": 1,
        "category": "Malignant",
        "frequency": "Common",
        "definition": "Pearly papule with telangiectasias and a rolled border on sun-exposed skin.",
        "rag": (
            "The most common human malignancy. Nodular BCC presents as a "
            "translucent, pearly papule with arborizing telangiectasias and may "
            "show central ulceration ('rodent ulcer'). Growth is slow and "
            "metastasis is rare, but local destruction can be significant. Mohs "
            "micrographic surgery is preferred for high-risk locations, "
            "especially the face."
        ),
        "lookalikes": ["Squamous Cell Carcinoma In Situ", "Verruca Vulgaris"],
        "feedback": {
            "Squamous Cell Carcinoma In Situ": (
                "Both malignant, both on sun-exposed skin. Differentiator: BCC "
                "is **pearly/translucent** with **arborizing telangiectasias** "
                "and a **rolled border**. SCC in situ is a **persistent, scaly, "
                "erythematous plaque** with irregular borders — flatter and "
                "less vascular."
            ),
            "Verruca Vulgaris": (
                "Both papular, but very different stakes. Differentiator: BCC "
                "is **pearly** with **telangiectasias** and slow growth in "
                "older patients. Warts are **dull, rough**, with **thrombosed "
                "capillaries**, often in younger patients on hands or knees."
            ),
        },
    },
    {
        "name": "Epidermal Cyst",
        "category": "Benign",
        "frequency": "Common",
        "definition": "Mobile, dome-shaped subcutaneous nodule with a central punctum.",
        "rag": (
            "Benign cyst lined by stratified squamous epithelium and filled with "
            "keratinous material. Lesions are dome-shaped, mobile, dermal "
            "nodules — most often on the face, neck, scalp, or trunk — with a "
            "characteristic central punctum representing the obstructed follicle. "
            "Rupture causes a foreign-body inflammatory reaction that can mimic "
            "infection. Definitive treatment is excision of the cyst wall; "
            "incision and drainage alone leads to recurrence."
        ),
        "lookalikes": ["Seborrheic Keratosis", "Verruca Vulgaris"],
        "feedback": {
            "Seborrheic Keratosis": (
                "Both benign, both raised in older adults. Differentiator: "
                "cysts are **dome-shaped, mobile, and dermal** with a "
                "**central punctum**. SKs are **stuck-on**, waxy, and "
                "**epidermal** — no punctum and no mobility under the skin."
            ),
            "Verruca Vulgaris": (
                "Both raised papules/nodules. Differentiator: warts are "
                "**surface-level, hyperkeratotic**, with **thrombosed "
                "capillaries**. Cysts are **deeper, smooth-surfaced, and "
                "freely mobile** — typically with a visible **central punctum**."
            ),
        },
    },
    {
        "name": "Mycosis Fungoides",
        "category": "Malignant",
        "frequency": "Uncommon",
        "definition": "Persistent erythematous patches and plaques in sun-protected areas; cutaneous T-cell lymphoma.",
        "rag": (
            "The most common form of cutaneous T-cell lymphoma. Early disease "
            "presents as persistent, ill-defined erythematous patches in a "
            "'bathing-suit' distribution (buttocks, lower trunk) that can "
            "resemble eczema or psoriasis for years before diagnosis. Plaques "
            "and tumors develop in advanced disease. Diagnosis requires biopsy "
            "with immunohistochemistry; staging guides therapy from skin-"
            "directed treatment to systemic chemotherapy."
        ),
        "lookalikes": ["Verruca Vulgaris", "Seborrheic Keratosis"],
        "feedback": {
            "Verruca Vulgaris": (
                "Visually different but CLIP groups them by texture/scale at "
                "low magnification. Differentiator: warts are **localized, "
                "hyperkeratotic papules** with black dots. MF presents as "
                "**broader patches or plaques** in sun-protected areas, often "
                "persisting for years and **resistant to topical steroids**."
            ),
            "Seborrheic Keratosis": (
                "Both can show scale or surface irregularity in older adults. "
                "Differentiator: SKs are **discrete, waxy, stuck-on papules**. "
                "MF is **broader, ill-defined erythematous patches/plaques** "
                "that wax and wane and persist for years — biopsy if unclear."
            ),
        },
    },
    {
        "name": "Squamous Cell Carcinoma In Situ",
        "category": "Malignant",
        "frequency": "Uncommon",
        "definition": "Persistent, scaly, erythematous plaque with sharp irregular borders (Bowen's disease).",
        "rag": (
            "Squamous cell carcinoma in situ (Bowen's disease) is full-thickness "
            "epidermal dysplasia confined above the basement membrane. Lesions "
            "are slow-growing, scaly, erythematous plaques with sharp, irregular "
            "borders, most often on sun-exposed skin in older adults. Without "
            "treatment, roughly 3–5% progress to invasive SCC. Topical "
            "5-fluorouracil, imiquimod, photodynamic therapy, cryotherapy, and "
            "excision are all first-line options."
        ),
        "lookalikes": ["Seborrheic Keratosis", "Basal Cell Carcinoma"],
        "feedback": {
            "Seborrheic Keratosis": (
                "Both scaly papules/plaques in older adults — CLIP confuses "
                "them (mean cosine 0.79). Differentiator: SCC in situ is "
                "**erythematous with irregular borders** and **resists topical "
                "treatment**. SKs are **uniform, waxy, dull**, with **sharp "
                "borders** and pseudohorn cysts on dermoscopy."
            ),
            "Basal Cell Carcinoma": (
                "Both malignant on sun-exposed skin. Differentiator: SCC in "
                "situ is a **flat-to-slightly-raised, scaly, red plaque** with "
                "**irregular borders**. BCC is **pearly/translucent** with "
                "**arborizing telangiectasias** and **rolled borders**, often "
                "with central ulceration."
            ),
        },
    },
]

# claude-assisted: load LLM-generated strings from rag_cache.json and override
# the static placeholders above. Cache is built by notebooks/03_build_rag_cache.ipynb.
_RAG_CACHE_PATH = Path(__file__).parent / "data" / "public" / "rag_cache.json"
if _RAG_CACHE_PATH.exists():
    _cache = json.loads(_RAG_CACHE_PATH.read_text())
    for _card in DECK_BASE:
        _entry = _cache.get(_card["name"])
        if _entry:
            if _entry.get("definition"):
                _card["definition"] = _entry["definition"]
            if _entry.get("feedback"):
                _card["feedback"].update(_entry["feedback"])
                # AI Explanation panel reuses the correct-pick feedback paragraph
                _correct_text = _entry["feedback"].get(_card["name"])
                if _correct_text:
                    _card["rag"] = _correct_text

# claude-assisted: expand DECK_BASE into round-variants. Most conditions get 3
# rounds (a/b/c) showing different example images per FST; BCC gets 1 (its FST
# 56 bucket is empty in DDI). Each card carries a "round" letter that the tile
# loader uses to pick the right thumbnail directory.
DECK = [
    {**_card, "round": _r}
    for _card in DECK_BASE
    for _r in ("a", "b", "c")[: _card.get("rounds", 3)]
]

# Pill colors — (background, text). Soft tinted background, saturated text.
CATEGORY_COLORS = {
    "Benign":    ("#e0f2fe", "#0369a1"),
    "Malignant": ("#fee2e2", "#b91c1c"),
}
FREQUENCY_COLORS = {
    "Common":   ("#d1fae5", "#047857"),
    "Uncommon": ("#fed7aa", "#9a3412"),
    "Rare":     ("#fee2e2", "#b91c1c"),
}


# Citation tooltips always render "Accessed {CITATION_ACCESSED}." — bump this
# whenever you re-verify the linked sources.
CITATION_ACCESSED = "Apr. 2026"

# Suggested-question chips for the Ask Questions tab. Each click sets
# ask_pending and reruns; the live RAG call fires from render_ask after the
# pending bubble + loading row have been drawn — same path as typing into
# the chat input. Picked to cover the highest-stakes CLIP confusions in the
# deck plus the project's skin-tone framing.
CHIP_QUESTIONS = [
    "How can I tell SCC in situ from seborrheic keratosis?",
    "What features suggest verruca vulgaris?",
    "Which conditions present differently in darker skin tones?",
]


def _placeholder_tile_b64(variant: int) -> str:
    """Brand-gradient placeholder tile — stand-in until the DDI pipeline emits
    public thumbnails. Variant 0/1/2 picks a different gradient pair."""
    palettes = [
        ("#f3f4f6", "#e5e7eb"),  # neutral gray
        ("#f3f4f6", "#e5e7eb"),
        ("#f3f4f6", "#e5e7eb"),
    ]
    a, b = palettes[variant % 3]
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 130' "
        "preserveAspectRatio='xMidYMid slice'>"
        f"<defs><linearGradient id='g{variant}' x1='0' y1='0' x2='1' y2='1'>"
        f"<stop offset='0' stop-color='{a}'/>"
        f"<stop offset='1' stop-color='{b}'/>"
        "</linearGradient></defs>"
        f"<rect width='100' height='130' fill='url(#g{variant})'/>"
        "</svg>"
    )
    return base64.b64encode(svg.encode()).decode()


TILE_B64 = [_placeholder_tile_b64(i) for i in range(3)]


# claude-assisted: thumbnail loading + "no sample" placeholder for cards where
# a given FST bucket is empty in DDI (currently only Basal Cell Carcinoma FST 56).
# Local dev reads from data/private/thumbnails/. On HF Space (no local private
# data), get_thumbnail_dir downloads the snapshot from the private HF Dataset
# using HF_TOKEN from st.secrets, caching after the first call.
_HF_DATASET_REPO = "madwall/skinsight-ddi-images"


def _slugify(name: str) -> str:
    return name.lower().replace(" ", "-")


def _no_sample_svg_b64(fst: str) -> str:
    fst_label = {"12": "I/II", "34": "III/IV", "56": "V/VI"}.get(fst, fst)
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100' "
        "preserveAspectRatio='xMidYMid slice'>"
        "<defs><linearGradient id='ng' x1='0' y1='0' x2='1' y2='1'>"
        "<stop offset='0' stop-color='#A78BFA' stop-opacity='0.18'/>"
        "<stop offset='1' stop-color='#F472B6' stop-opacity='0.18'/>"
        "</linearGradient></defs>"
        "<rect width='100' height='100' fill='url(#ng)'/>"
        "<g font-family='Inter, sans-serif' text-anchor='middle'>"
        "<text x='50' y='40' font-size='8' font-weight='600' fill='#5a5170'>No FST</text>"
        f"<text x='50' y='56' font-size='14' font-weight='700' fill='#1F2937'>{fst_label}</text>"
        "<text x='50' y='72' font-size='7' fill='#5a5170'>sample in DDI</text>"
        "</g></svg>"
    )
    return base64.b64encode(svg.encode()).decode()


@st.cache_resource
def get_thumbnail_dir() -> Path:
    local = ROOT / "data" / "private" / "thumbnails"
    if local.exists():
        return local
    from huggingface_hub import snapshot_download

    token = st.secrets.get("HF_TOKEN") if hasattr(st, "secrets") else None
    snapshot = snapshot_download(
        repo_id=_HF_DATASET_REPO,
        repo_type="dataset",
        token=token,
        allow_patterns=["thumbnails/**"],
    )
    return Path(snapshot) / "thumbnails"


@st.cache_data
def load_tile_b64(slug: str, round_letter: str, fst: str) -> tuple[str, str]:
    """Returns (mime_type, base64_payload). Falls back to "no sample" SVG when
    the (condition, round, FST) thumbnail doesn't exist."""
    path = get_thumbnail_dir() / slug / f"round-{round_letter}" / f"{fst}.jpg"
    if path.exists():
        return ("image/jpeg", base64.b64encode(path.read_bytes()).decode("ascii"))
    return ("image/svg+xml", _no_sample_svg_b64(fst))


st.set_page_config(
    page_title="SkinSight AI — Visual Dermatology Learning",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---- Session state ----
if "page" not in st.session_state:
    st.session_state.page = "home"
if "_just_clicked" not in st.session_state:
    st.session_state._just_clicked = None
if "fc_order" not in st.session_state:
    # Shuffle on first session: deck is generated as [cond1_a, cond1_b, cond1_c,
    # cond2_a, ...] so sequential order shows three rounds of the same condition
    # back-to-back. Shuffling once at init mixes them.
    _initial_order = list(range(len(DECK)))
    random.shuffle(_initial_order)
    st.session_state.fc_order = _initial_order
if "fc_pos" not in st.session_state:
    st.session_state.fc_pos = 0
if "fc_revealed" not in st.session_state:
    st.session_state.fc_revealed = False
if "fc_just_revealed" not in st.session_state:
    st.session_state.fc_just_revealed = False
# MC quiz state. fc_options is the per-card shuffled order of 4 option names
# (correct + 3 lookalikes); fc_picked is the option name the user clicked
# (None until they pick).
if "fc_options" not in st.session_state:
    st.session_state.fc_options = None
if "fc_options_for_pos" not in st.session_state:
    st.session_state.fc_options_for_pos = None
if "fc_picked" not in st.session_state:
    st.session_state.fc_picked = None
# Mode toggle: "Learn" shows the answer + RAG explanation directly;
# "Quiz" shows 4 multiple-choice options with feedback.
if "fc_mode" not in st.session_state:
    st.session_state.fc_mode = "Learn"
# Per-card familiarity status (DECK index → "familiar" | "unfamiliar"),
# set by the ✓/✕ buttons on the card. Drives the filter tabs at the top
# of the card.
if "fc_familiarity" not in st.session_state:
    st.session_state.fc_familiarity = {}
if "fc_filter" not in st.session_state:
    st.session_state.fc_filter = "All Cards"
if "ask_messages" not in st.session_state:
    st.session_state.ask_messages = []
if "ask_pending" not in st.session_state:
    st.session_state.ask_pending = None

# Logo click is an <a href='?nav=home'>. Consume the param here so a click
# on the SVG routes to home, then clean it out of the URL.
_qp = st.query_params
if "nav" in _qp:
    _target = _qp.get("nav", "")
    if _target and _target != st.session_state.page:
        st.session_state.page = _target
        st.session_state._just_clicked = _target
    del _qp["nav"]


def go(page: str) -> None:
    st.session_state.page = page
    st.session_state._just_clicked = page
    # Force an immediate rerun so the nav re-renders with the correct
    # active-state container key (otherwise the highlighted link lags
    # one click behind the actual page).
    st.rerun()


def fc_shuffle() -> None:
    order = list(range(len(DECK)))
    random.shuffle(order)
    st.session_state.fc_order = order
    st.session_state.fc_pos = 0
    st.session_state.fc_revealed = False
    st.session_state.fc_picked = None
    st.session_state.fc_options = None
    st.session_state.fc_options_for_pos = None


def fc_set_mode(mode: str) -> None:
    if mode == st.session_state.fc_mode:
        return
    st.session_state.fc_mode = mode
    # Reset current-card view state so a mid-card mode switch shows fresh.
    st.session_state.fc_picked = None
    st.session_state.fc_revealed = False
    st.session_state.fc_just_revealed = False


def current_card_mode(pos: int) -> str:
    """Return 'mc' or 'reveal' for the card at `pos` based on user's mode."""
    return "mc" if st.session_state.fc_mode == "Quiz" else "reveal"


def fc_displayed_order() -> list[int]:
    """Master `fc_order` filtered by the active tab. `All Cards` returns
    everything; `Familiar`/`Unfamiliar` filter by `fc_familiarity` status."""
    fil = st.session_state.fc_filter
    if fil == "All Cards":
        return st.session_state.fc_order
    fam = st.session_state.fc_familiarity
    target = "familiar" if fil == "Familiar" else "unfamiliar"
    return [i for i in st.session_state.fc_order if fam.get(i) == target]


def fc_set_filter(new_filter: str) -> None:
    """Switch the active filter tab; reset position + per-card transient state."""
    if new_filter == st.session_state.fc_filter:
        return
    st.session_state.fc_filter = new_filter
    st.session_state.fc_pos = 0
    st.session_state.fc_revealed = False
    st.session_state.fc_picked = None
    st.session_state.fc_options = None
    st.session_state.fc_options_for_pos = None


def fc_mark(status: str) -> None:
    """Mark current card familiar/unfamiliar. Advance only if the card is
    still in the active filter post-mark; otherwise stay at the same pos
    (the next card naturally takes its place in the filtered list)."""
    order = fc_displayed_order()
    pos = st.session_state.fc_pos
    if pos >= len(order):
        return
    st.session_state.fc_familiarity[order[pos]] = status
    fil = st.session_state.fc_filter
    still_in_filter = (
        fil == "All Cards"
        or (fil == "Familiar" and status == "familiar")
        or (fil == "Unfamiliar" and status == "unfamiliar")
    )
    if still_in_filter:
        fc_advance()
    else:
        st.session_state.fc_revealed = False
        st.session_state.fc_picked = None
        st.session_state.fc_options = None
        st.session_state.fc_options_for_pos = None


def fc_reveal() -> None:
    st.session_state.fc_revealed = True
    st.session_state.fc_just_revealed = True


def fc_pick(option: str, correct: str | None = None) -> None:
    """Record the user's MC pick. If `correct` is provided, also auto-mark
    the card's familiarity (familiar if the pick matched, unfamiliar otherwise).
    The auto-reveal shortcut omits `correct` so accidental skips don't taint
    familiarity tracking."""
    st.session_state.fc_picked = option
    st.session_state.fc_just_revealed = True
    if correct is not None:
        order = fc_displayed_order()
        pos = st.session_state.fc_pos
        if pos < len(order):
            st.session_state.fc_familiarity[order[pos]] = (
                "familiar" if option == correct else "unfamiliar"
            )


def fc_advance() -> None:
    st.session_state.fc_pos += 1
    st.session_state.fc_revealed = False
    st.session_state.fc_picked = None


def fc_prev() -> None:
    st.session_state.fc_pos = max(0, st.session_state.fc_pos - 1)
    st.session_state.fc_revealed = False
    st.session_state.fc_picked = None


def fc_options_for(pos: int) -> list[str]:
    """Return the 3 shuffled MC options for the card at `pos` (correct +
    2 random lookalikes), generating them once per card and caching in
    session state so the order is stable across reruns until the user
    advances."""
    if (
        st.session_state.fc_options is not None
        and st.session_state.fc_options_for_pos == pos
    ):
        return st.session_state.fc_options
    card = DECK[fc_displayed_order()[pos]]
    decoys = random.sample(card["lookalikes"], k=min(2, len(card["lookalikes"])))
    options = [card["name"], *decoys]
    random.shuffle(options)
    st.session_state.fc_options = options
    st.session_state.fc_options_for_pos = pos
    return options


def _md_to_html(
    text: str,
    msg_idx: int = 0,
    sources: list[dict] | None = None,
) -> str:
    """Tiny markdown shim for chat bubbles — bold (**x**), italic (_x_),
    bullet lines (• …), \\n\\n paragraph breaks, and [n] citation markers
    rendered as inline academic-style superscripts ([1], [2], …) with a
    hover tooltip showing the source name + title."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"_([^_]+?)_", r"<em>\1</em>", text)

    def _cite(m: "re.Match[str]") -> str:
        n = int(m.group(1))
        s = sources[n - 1] if sources and 1 <= n <= len(sources) else None
        tooltip = ""
        if s:
            title_punct = "," if s.get("url") else "."
            parts = [
                "<span class='cite-tooltip-source'>"
                f"{html.escape(s['source'])}.</span>",
                "<span class='cite-tooltip-title'>"
                f"&ldquo;{html.escape(s['title'])}&rdquo;{title_punct}</span>",
            ]
            if s.get("url"):
                display_url = re.sub(r"^https?://(www\.)?", "", s["url"])
                parts.append(
                    "<a class='cite-tooltip-url' "
                    f"href='{html.escape(s['url'], quote=True)}' "
                    f"target='_blank' rel='noopener noreferrer'>"
                    f"{html.escape(display_url)}</a>."
                )
            parts.append(
                "<span class='cite-tooltip-accessed'>"
                f"Accessed {html.escape(CITATION_ACCESSED)}.</span>"
            )
            tooltip = (
                "<span class='cite-tooltip' role='tooltip'>"
                + " ".join(parts)
                + "</span>"
            )
        return f"<span class='cite' tabindex='0'>[{n}]{tooltip}</span>"

    text = re.sub(r"\[(\d+)\]", _cite, text)
    paragraphs = text.split("\n\n")
    out = []
    for p in paragraphs:
        # If every non-empty line in this paragraph starts with a bullet,
        # render as a <ul>; otherwise as a <p> with <br> for soft breaks.
        lines = [l for l in p.split("\n") if l.strip()]
        if lines and all(l.lstrip().startswith("•") for l in lines):
            items = "".join(
                f"<li>{l.lstrip()[1:].strip()}</li>" for l in lines
            )
            out.append(f"<ul class='chat-list'>{items}</ul>")
        else:
            out.append(f"<p>{p.replace(chr(10), '<br>')}</p>")
    return "\n".join(out)


def _render_chat_message(msg: dict, msg_idx: int) -> None:
    role = msg["role"]
    content = msg["content"]
    if role == "user":
        # Escape user-supplied content so typed HTML renders as text.
        content = html.escape(content)
    body_html = _md_to_html(content, msg_idx, msg.get("sources"))
    st.markdown(
        f"<div class='chat-row chat-row-{role}'>"
        f"<div class='chat-bubble chat-bubble-{role}'>{body_html}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


# Sparkle SVG used as a tiled background overlay (4-point star, soft white).
CLOUD_PUFF_SVG = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 220 130' "
    "preserveAspectRatio='xMidYMid meet'>"
    "<defs>"
    "<radialGradient id='puff' cx='50%25' cy='45%25' r='55%25'>"
    "<stop offset='0' stop-color='white' stop-opacity='0.85'/>"
    "<stop offset='0.6' stop-color='white' stop-opacity='0.55'/>"
    "<stop offset='1' stop-color='white' stop-opacity='0.10'/>"
    "</radialGradient>"
    "</defs>"
    "<g fill='url(%23puff)'>"
    "<ellipse cx='110' cy='95' rx='98' ry='26'/>"
    "<circle cx='58'  cy='75' r='30'/>"
    "<circle cx='95'  cy='52' r='40'/>"
    "<circle cx='140' cy='58' r='34'/>"
    "<circle cx='170' cy='78' r='26'/>"
    "<circle cx='80'  cy='62' r='22'/>"
    "<circle cx='125' cy='80' r='30'/>"
    "</g>"
    "</svg>"
)

SPARKLE_SVG = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='420' height='420'>"
    # large sparkles
    "<g fill='white' opacity='0.55'>"
    "<path d='M60 40 L62 50 L72 52 L62 54 L60 64 L58 54 L48 52 L58 50 Z'/>"
    "<path d='M340 90 L342 100 L352 102 L342 104 L340 114 L338 104 L328 102 L338 100 Z'/>"
    "<path d='M210 220 L213 234 L227 237 L213 240 L210 254 L207 240 L193 237 L207 234 Z'/>"
    "<path d='M90 320 L92 330 L102 332 L92 334 L90 344 L88 334 L78 332 L88 330 Z'/>"
    "<path d='M370 360 L372 370 L382 372 L372 374 L370 384 L368 374 L358 372 L368 370 Z'/>"
    "</g>"
    # small sparkles
    "<g fill='white' opacity='0.45'>"
    "<circle cx='150' cy='110' r='2'/>"
    "<circle cx='280' cy='180' r='1.5'/>"
    "<circle cx='40'  cy='220' r='2'/>"
    "<circle cx='320' cy='280' r='1.5'/>"
    "<circle cx='180' cy='380' r='2'/>"
    "<circle cx='250' cy='60'  r='1.5'/>"
    "</g>"
    "</svg>"
)

def sparkle_chip_svg(grad_id: str, gray: bool = False) -> str:
    """Small inline sparkle for eyebrow chips. Each call needs a unique
    gradient id since multiple chips render in one DOM. `gray=True` swaps
    the violet→pink gradient for a flat muted gray (matches the AI
    Explanation eyebrow on the flashcard)."""
    if gray:
        return (
            "<svg width='14' height='14' viewBox='0 0 24 24' fill='none' "
            "xmlns='http://www.w3.org/2000/svg'>"
            "<path d='M12 3 L13.4 9.6 L20 11 L13.4 12.4 L12 19 L10.6 12.4 "
            "L4 11 L10.6 9.6 Z' fill='#9ca3af'/></svg>"
        )
    return (
        "<svg width='16' height='16' viewBox='0 0 24 24' fill='none' "
        "xmlns='http://www.w3.org/2000/svg'>"
        f"<path d='M12 3 L13.4 9.6 L20 11 L13.4 12.4 L12 19 L10.6 12.4 L4 11 "
        f"L10.6 9.6 Z' fill='url(#{grad_id})'/>"
        f"<defs><linearGradient id='{grad_id}' x1='0' y1='0' x2='1' y2='1'>"
        "<stop offset='0' stop-color='#b85cff'/>"
        "<stop offset='1' stop-color='#ff6fb1'/></linearGradient></defs></svg>"
    )


# claude-assisted: brand-styled chat-bubble glyph for the Ask page hero
def chat_bubble_sparkle_svg(grad_id: str) -> str:
    """Two overlapping speech bubbles (lavender + violet outlines) with three
    brand-gradient sparkles around them. Drives the Ask Questions hero icon.
    `grad_id` must be unique per render so the gradient defs don't collide
    with sparkle_chip_svg in the same DOM."""
    return (
        "<svg viewBox='0 0 72 72' fill='none' "
        "xmlns='http://www.w3.org/2000/svg'>"
        f"<defs><linearGradient id='{grad_id}' x1='0' y1='0' x2='1' y2='1'>"
        "<stop offset='0' stop-color='#b85cff'/>"
        "<stop offset='1' stop-color='#ff6fb1'/></linearGradient></defs>"
        "<path d='M16 8 H38 Q48 8 48 18 V26 Q48 36 38 36 H22 L14 44 L16 36 "
        "Q6 36 6 26 V18 Q6 8 16 8 Z' fill='white' stroke='#C084FC' "
        "stroke-width='2' stroke-linejoin='round'/>"
        "<path d='M30 20 H56 Q66 20 66 30 V38 Q66 48 56 48 L56 56 L46 48 "
        "H30 Q20 48 20 38 V30 Q20 20 30 20 Z' fill='white' stroke='#A78BFA' "
        "stroke-width='2' stroke-linejoin='round'/>"
        "<circle cx='32' cy='34' r='1.6' fill='#A78BFA'/>"
        "<circle cx='39' cy='34' r='1.6' fill='#A78BFA'/>"
        "<circle cx='46' cy='34' r='1.6' fill='#A78BFA'/>"
        f"<path d='M66 2 L67.2 4.8 L70 6 L67.2 7.2 L66 10 L64.8 7.2 L62 6 "
        f"L64.8 4.8 Z' fill='url(#{grad_id})'/>"
        f"<path d='M58 11.5 L58.75 13.25 L60.5 14 L58.75 14.75 L58 16.5 "
        f"L57.25 14.75 L55.5 14 L57.25 13.25 Z' fill='url(#{grad_id})'/>"
        f"<path d='M4 1 L4.9 3.1 L7 4 L4.9 4.9 L4 7 L3.1 4.9 L1 4 L3.1 3.1 "
        f"Z' fill='url(#{grad_id})'/>"
        "</svg>"
    )


st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp {{
        font-family: 'Inter', system-ui, sans-serif;
        color: #1f2937;
    }}

    /* Image-protect: block drag-to-save, text selection, and iOS
       long-press save menu on every <img> in the app. */
    img {{
        -webkit-user-drag: none;
        user-select: none;
        -webkit-user-select: none;
        -webkit-touch-callout: none;
    }}
    h1, h2, h3, h4, .hero-title, .card-title, .brand-text {{
        font-family: 'Poppins', 'Inter', system-ui, sans-serif;
    }}

    /* Background gradient — sampled from the banner */
    .stApp {{
        background:
            radial-gradient(circle at 22% 28%, rgba(232,226,247,0.85), transparent 38%),
            radial-gradient(circle at 78% 18%, rgba(252,233,238,0.70), transparent 42%),
            radial-gradient(circle at 50% 92%, rgba(244,228,250,0.55), transparent 46%),
            linear-gradient(135deg, #f6f1ff 0%, #f7eef5 55%, #fdf5f4 100%);
        background-attachment: fixed;
    }}
    /* Sparkle overlay — tiled SVG of soft white stars/dots */
    .stApp::before {{
        content: '';
        position: fixed; inset: 0;
        pointer-events: none;
        background-image: url("{SPARKLE_SVG}");
        background-repeat: repeat;
        opacity: 0.85;
        z-index: 0;
    }}
    .block-container {{
        position: relative; z-index: 1;
        padding-top: 0 !important;
        padding-bottom: 2rem !important;
        max-width: 1320px !important;
    }}
    #MainMenu, header, footer {{display: none !important;}}
    [data-testid="stHeader"], [data-testid="stAppHeader"] {{display: none !important; height: 0 !important;}}
    [data-testid="stMain"] {{padding-top: 0 !important;}}
    [data-testid="stAppViewContainer"] > .main {{padding-top: 0 !important;}}

    /* Zero out top spacing on every Streamlit wrapper between viewport and
       menu-bar. Newer Streamlit wraps .block-container in stMainBlockContainer
       with its own padding-top; the body UA default 8px margin is the
       remaining contributor. Together these cover the gap above the bar. */
    html, body, #root,
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    .main,
    .block-container {{
        margin-top: 0 !important;
        padding-top: 0 !important;
    }}

    /* Brand logo. */
    .brand-logo {{
        height: 48px; width: auto; display: block;
        transform: translateY(-5px);
    }}

    /* Eyebrow chip */
    .eyebrow {{
        font-family: 'Inter', sans-serif;
        display: inline-flex; align-items: center; gap: 0.5rem;
        padding: 0.5rem 1.1rem;
        background: rgba(255,255,255,0.7);
        border: 1px solid rgba(167, 139, 250, 0.28);
        border-radius: 999px;
        color: #7c3aed; font-size: 0.88rem; font-weight: 500;
        backdrop-filter: blur(10px);
        margin-bottom: 1.4rem;
        box-shadow: 0 4px 14px rgba(167,139,250,0.08);
    }}
    .eyebrow svg {{ flex-shrink: 0; }}

    /* Hero text */
    .hero-title {{
        font-family: 'Poppins', sans-serif;
        font-size: clamp(1.8rem, 2.5vw + 0.8rem, 3rem);
        font-weight: 600;
        color: #1f2937; line-height: 1.15;
        margin: 0 0 1.25rem 0; letter-spacing: -0.02em;
    }}
    .hero-accent {{
        background: linear-gradient(135deg, #f472b6 0%, #ffb8a2 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 600;
    }}
    .hero-sub {{
        font-family: 'Inter', sans-serif;
        font-size: 1.02rem; font-weight: 400;
        color: #5a5170; line-height: 1.6;
        margin-bottom: 1.75rem; max-width: 500px;
    }}

    /* Ask page hero — chat-bubble icon + brand-gradient sparkles */
    .ask-hero {{ margin: 0 auto 0.5rem auto; text-align: center; }}
    .ask-hero-icon {{
        width: 60px; height: 60px;
        margin: 2px auto 0.65rem auto;
    }}
    .ask-hero-icon svg {{ display: block; width: 100%; height: 100%; }}
    .ask-hero .hero-title {{
        font-size: clamp(1.45rem, 1.4vw + 0.8rem, 2.1rem);
        line-height: 1.15;
        font-weight: 600;
        letter-spacing: -0.015em;
        max-width: 720px;
        margin: 0 auto 0.35rem auto;
    }}
    .ask-hero .hero-sub {{
        font-size: 0.94rem;
        line-height: 1.5;
        color: #6b6580;
        max-width: 720px;
        margin: 0 auto;
        white-space: nowrap;
    }}

    /* Streamlit button overrides — brand spec */
    div[data-testid="stButton"] > button {{
        font-family: 'Inter', sans-serif !important;
        border-radius: 12px !important;
        padding: 0.7rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        border: none !important;
        white-space: nowrap !important;
        overflow: visible !important;
        min-width: max-content !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }}
    div[data-testid="stButton"] > button:hover {{
        transform: translateY(-1px);
    }}
    /* Primary — pink → purple gradient (brand) with subtle drop shadow */
    div[data-testid="stButton"] > button[kind="primary"] {{
        background: linear-gradient(135deg, #f472b6 0%, #a78bfa 100%) !important;
        color: white !important;
        box-shadow: 0 6px 18px rgba(167, 139, 250, 0.28) !important;
    }}
    div[data-testid="stButton"] > button[kind="primary"]:hover {{
        box-shadow: 0 10px 24px rgba(167, 139, 250, 0.38) !important;
    }}
    /* Secondary — outlined purple, no shadow (brand) */
    div[data-testid="stButton"] > button[kind="secondary"] {{
        background: rgba(255,255,255,0.85) !important;
        color: #7c3aed !important;
        border: 1.5px solid #a78bfa !important;
        font-weight: 500 !important;
        box-shadow: none !important;
    }}
    div[data-testid="stButton"] > button[kind="secondary"]:hover {{
        background: rgba(255,255,255,1) !important;
        border-color: #7c3aed !important;
        color: #7c3aed !important;
        box-shadow: none !important;
    }}
    /* Review Unfamiliar — secondary button paired with the primary
       "Shuffle & Restart All" on the deck-complete state. Inherits the
       outlined-secondary look but gets the same lavender drop shadow as
       primary so the two buttons read as a balanced pair. */
    [class*="st-key-fc-review-wrap"] div[data-testid="stButton"] > button {{
        box-shadow: 0 6px 18px rgba(167, 139, 250, 0.28) !important;
        transition: box-shadow 0.18s ease, transform 0.15s ease !important;
    }}
    [class*="st-key-fc-review-wrap"] div[data-testid="stButton"] > button:hover {{
        box-shadow: 0 10px 24px rgba(167, 139, 250, 0.38) !important;
    }}
    /* Tertiary — text-link look (brand) */
    div[data-testid="stButton"] > button[kind="tertiary"] {{
        background: transparent !important;
        color: #1f2937 !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        padding: 0.5rem 0.4rem !important;
    }}
    div[data-testid="stButton"] > button[kind="tertiary"]:hover {{
        color: #a78bfa !important;
        background: transparent !important;
    }}
    /* External-link nav item (st.link_button) — match tertiary button look. */
    [data-testid="stLinkButton"] a {{
        background: transparent !important;
        color: #1f2937 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        padding: 0.5rem 0.4rem !important;
        border: none !important;
        border-radius: 12px !important;
        text-decoration: none !important;
        box-shadow: none !important;
        white-space: nowrap !important;
        min-width: max-content !important;
        transition: transform 0.15s ease, color 0.15s ease !important;
    }}
    [data-testid="stLinkButton"] a:hover {{
        color: #a78bfa !important;
        background: transparent !important;
        text-decoration: none !important;
        transform: translateY(-1px);
    }}
    /* Top nav grouping — single keyed container wraps the whole bar
       (logo + links + right icons). In-flow at top of page; uses
       negative-margin trick to break out of the 1320px max-width and
       span the full viewport. Inner padding centers the content at the
       1320px column. Margin-bottom gives consistent breathing room
       before page content on every page. */
    [class*="st-key-menu-bar"] {{
        margin-top: 0 !important;
        margin-bottom: 0.6rem !important;
        margin-left: calc(-50vw + 50%) !important;
        width: 100vw !important;
        max-width: 100vw !important;
        padding: 20px max(1.5rem, calc((100vw - 1320px) / 2 + 1.5rem)) !important;
        background: #ffffff;
        border: none;
        border-radius: 0;
        box-shadow: 0 1px 8px rgba(0, 0, 0, 0.08);
    }}
    /* Night-mode icon button — bare gray icon, hover darkens, no focus ring. */
    [class*="st-key-nav-icon-night"] button[kind="tertiary"] {{
        background: transparent !important;
        border: none !important;
        color: #6b7280 !important;
        padding: 6px !important;
        min-width: 36px !important;
        height: 36px !important;
    }}
    [class*="st-key-nav-icon-night"] button[kind="tertiary"]:hover {{
        background: rgba(167, 139, 250, 0.08) !important;
        color: #1f2937 !important;
    }}
    [class*="st-key-nav-icon-night"] button:focus,
    [class*="st-key-nav-icon-night"] button:focus-visible,
    [class*="st-key-nav-icon-avatar"] button:focus,
    [class*="st-key-nav-icon-avatar"] button:focus-visible {{
        outline: none !important;
        box-shadow: none !important;
    }}
    /* Avatar — perfect circle, light lavender bg, violet initials.
       Hard-locked to 40x40 with min/max constraints + aspect-ratio so
       Streamlit's default button height/padding can't distort it. */
    [class*="st-key-nav-icon-avatar"] [data-testid="stButton"] {{
        width: 40px !important;
        max-width: 40px !important;
        display: inline-block !important;
    }}
    [class*="st-key-nav-icon-avatar"] button[kind="tertiary"] {{
        background: linear-gradient(135deg, #A78BFA 0%, #F472B6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        min-width: 40px !important;
        max-width: 40px !important;
        min-height: 40px !important;
        max-height: 40px !important;
        padding: 0 !important;
        line-height: 1 !important;
        flex: none !important;
        aspect-ratio: 1 / 1 !important;
        box-sizing: border-box !important;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.82rem !important;
        letter-spacing: 0.5px !important;
    }}
    [class*="st-key-nav-icon-avatar"] button[kind="tertiary"]:hover {{
        transform: scale(1.04) !important;
        box-shadow: 0 2px 8px rgba(167, 139, 250, 0.3) !important;
    }}
    /* Nav item containers — every nav item is wrapped in a keyed container
       so all five share identical DOM structure. Reset spacing. */
    [class*="st-key-nav-item-"], [class*="st-key-nav-active-"] {{
        margin: 0 !important;
        padding: 0 !important;
        gap: 0 !important;
    }}
    /* Nav text-item hover — paint the visible pill on the inner <p>
       (st.button) or inner <a> (st.link_button) so it hugs the text,
       while the outer button stays full column width as the click target.
       inline-block lets the inner element size to its content. Lift is
       applied to the inner pill, not the outer, so only the visible pill
       jumps. Color is forced to ink across all descendants — defeats the
       global tertiary :hover lilac (#a78bfa) from above leaking
       through inheritance. */
    [class*="st-key-nav-item-"] button[kind="tertiary"] p,
    [class*="st-key-nav-item-ext-"] [data-testid="stLinkButton"] a {{
        display: inline-block !important;
        padding: 6px 14px !important;
        border-radius: 10px !important;
        margin: 0 !important;
        transition: background 0.15s ease, transform 0.15s ease,
                    color 0.15s ease !important;
    }}
    /* Inactive nav-item hover — lavender pill on the inner element only. */
    [class*="st-key-nav-item-"] button[kind="tertiary"]:hover p,
    [class*="st-key-nav-item-ext-"] [data-testid="stLinkButton"] a:hover {{
        background: rgba(167, 139, 250, 0.12) !important;
        transform: translateY(-1px) !important;
        color: #1f2937 !important;
    }}
    /* Outer button/link itself stays inert on hover — no wide bg, no jump. */
    [class*="st-key-nav-item-"] button[kind="tertiary"]:hover,
    [class*="st-key-nav-item-ext-"] [data-testid="stLinkButton"] a:hover {{
        background: transparent !important;
        transform: none !important;
    }}
    /* Defeat the global tertiary :hover lilac (#a78bfa) reaching the
       inner <p>/<div>/<span> through inheritance. */
    [class*="st-key-nav-item-"] button[kind="tertiary"]:hover,
    [class*="st-key-nav-item-"] button[kind="tertiary"]:hover *,
    [class*="st-key-nav-item-ext-"] [data-testid="stLinkButton"] a:hover * {{
        color: #1f2937 !important;
    }}
    /* Active nav state — violet text + violet underline only, NO pill,
       NO jump. Re-asserted so the new hover rules above don't fire. */
    [class*="st-key-nav-active-"] button[kind="tertiary"]:hover,
    [class*="st-key-nav-active-"] button[kind="tertiary"]:hover p {{
        background: transparent !important;
        transform: none !important;
    }}
    /* Active nav link — purple text + thin underline matching text width.
       Streamlit wraps button text in <div><p>, so the color must be set on
       both the button and its descendants. text-decoration on the inner
       element auto-matches the text width (what we want). */
    [class*="st-key-nav-active"] button,
    [class*="st-key-nav-active"] button *,
    [class*="st-key-nav-active"] button p,
    [class*="st-key-nav-active"] button div {{
        color: #7c3aed !important;
        font-weight: 600 !important;
    }}
    [class*="st-key-nav-active"] button p,
    [class*="st-key-nav-active"] button div[data-testid="stMarkdownContainer"] p {{
        text-decoration: underline !important;
        text-decoration-color: #7c3aed !important;
        text-decoration-thickness: 2.5px !important;
        text-underline-offset: 8px !important;
    }}

    /* Feature row — three items on one line, shrink rather than wrap.
       Hairline vertical dividers between items match the .fc-divider color
       used on the flashcard. */
    .features {{
        display: flex;
        gap: 1.1rem;
        margin-top: 2.5rem;
        flex-wrap: nowrap;
        align-items: center;
    }}
    .feature {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.65rem;
        flex: 1 1 0;
        min-width: 0;
        position: relative;
    }}
    .feature:not(:last-child)::after {{
        content: '';
        position: absolute;
        right: -0.55rem;
        top: 50%;
        transform: translateY(-50%);
        width: 1px;
        height: 1.6em;
        background: rgba(31, 41, 55, 0.10);
    }}
    .feature-text {{ min-width: 0; }}
    .feature-title {{
        font-family: 'Poppins', sans-serif;
        font-weight: 600; color: #1f2937; font-size: 0.9rem;
        white-space: nowrap;
    }}
    .feature-sub   {{
        font-family: 'Inter', sans-serif;
        font-size: 0.78rem; color: #7a7090;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    /* Flashcard mockup image */
    .card-img-wrap {{
        display: flex; justify-content: flex-end;
        padding-top: 0.5rem;
    }}
    .card-img {{
        max-width: 460px; width: 100%; height: auto;
        filter: drop-shadow(0 24px 50px rgba(184, 92, 255, 0.18));
    }}

    /* ===== Flashcards page ===== */
    [class*="st-key-fc-belowcard"] {{
        max-width: 720px;
        margin: -0.5rem auto 0 auto;
    }}

    /* Page-level title used by Ask Questions (Flashcards no longer has one). */
    .fc-page-title {{
        font-family: 'Poppins', sans-serif;
        font-size: clamp(1.6rem, 2vw + 1rem, 2.4rem);
        font-weight: 700;
        color: #1f2937;
        margin: 0 0 0.35rem 0;
        letter-spacing: -0.01em;
    }}
    .fc-page-sub {{
        font-family: 'Inter', sans-serif;
        color: #5a5170;
        font-size: 1rem;
        margin: 0 0 1rem 0;
    }}

    .fc-counter {{
        font-family: 'Inter', sans-serif;
        font-weight: 400;
        color: #6b7280;
        font-size: 0.95rem;
        text-align: right;
        transform: translateY(-8px);
    }}

    .fc-progress-track {{
        width: 100%;
        height: 6px;
        background: rgba(167, 139, 250, 0.18);
        border-radius: 999px;
        overflow: hidden;
        margin: 0.7rem auto 0.4rem auto;
        max-width: 720px;
        transform: translateY(-5px);
    }}
    .fc-progress-fill {{
        height: 100%;
        background: #7c3aed;
        border-radius: 999px;
        transition: width 0.25s ease;
    }}

    /* Previous / Next — neutralize Streamlit tertiary's purple focus
       state so they read like Shuffle (ink color throughout, no purple
       leak when keyboard or click focus lands on them). */
    [class*="st-key-fc-prev-wrap"] div[data-testid="stButton"] > button,
    [class*="st-key-fc-prev-wrap"] div[data-testid="stButton"] > button p,
    [class*="st-key-fc-next-wrap"] div[data-testid="stButton"] > button,
    [class*="st-key-fc-next-wrap"] div[data-testid="stButton"] > button p {{
        color: #1f2937 !important;
    }}
    [class*="st-key-fc-prev-wrap"] div[data-testid="stButton"] > button:hover,
    [class*="st-key-fc-prev-wrap"] div[data-testid="stButton"] > button:focus,
    [class*="st-key-fc-prev-wrap"] div[data-testid="stButton"] > button:focus-visible,
    [class*="st-key-fc-prev-wrap"] div[data-testid="stButton"] > button:active,
    [class*="st-key-fc-next-wrap"] div[data-testid="stButton"] > button:hover,
    [class*="st-key-fc-next-wrap"] div[data-testid="stButton"] > button:focus,
    [class*="st-key-fc-next-wrap"] div[data-testid="stButton"] > button:focus-visible,
    [class*="st-key-fc-next-wrap"] div[data-testid="stButton"] > button:active,
    [class*="st-key-fc-prev-wrap"] div[data-testid="stButton"] > button:hover p,
    [class*="st-key-fc-prev-wrap"] div[data-testid="stButton"] > button:focus p,
    [class*="st-key-fc-prev-wrap"] div[data-testid="stButton"] > button:focus-visible p,
    [class*="st-key-fc-prev-wrap"] div[data-testid="stButton"] > button:active p,
    [class*="st-key-fc-next-wrap"] div[data-testid="stButton"] > button:hover p,
    [class*="st-key-fc-next-wrap"] div[data-testid="stButton"] > button:focus p,
    [class*="st-key-fc-next-wrap"] div[data-testid="stButton"] > button:focus-visible p,
    [class*="st-key-fc-next-wrap"] div[data-testid="stButton"] > button:active p {{
        color: #1f2937 !important;
        outline: none !important;
        background: transparent !important;
    }}

    /* Hidden Quiz-mode reveal button — exists only so the Space keyboard
       shortcut has a click target. Never shown to the user. */
    [class*="st-key-fc_quiz_reveal_btn"] {{
        display: none !important;
    }}

    /* The card itself */
    [class*="st-key-fc-card"] {{
        background: white;
        border-radius: 24px;
        padding: 1.8rem 2.2rem 1.6rem 2.2rem;
        box-shadow: 0 18px 40px rgba(31, 41, 55, 0.08),
                    0 4px 14px rgba(31, 41, 55, 0.06);
        max-width: 860px;
        margin: 0.6rem auto 0.6rem auto;
        border: 1px solid rgba(31, 41, 55, 0.06);
    }}

    /* Custom CSS to bypass Streamlit's wrapper-hell layout.
       Streamlit wraps every keyed st.container in nested div blocks
       (stVerticalBlockBorderWrapper > stVerticalBlock > children) where
       the inner block defaults to flex-direction: column. To get a clean
       horizontal flex on the keyed container, we apply `display: contents`
       to the inner stVerticalBlock — that removes it from the layout tree
       entirely while keeping its children, so the children become direct
       flex items of our outer keyed container. Works in all modern browsers. */

    /* Card header — ONE flex row, ALL 6 items as direct flex children.
       fc-header is the only flex container; its inner stVerticalBlock is
       flattened with display:contents so the children become direct flex
       items of fc-header. Every child is forced to natural width so
       Streamlit's default 100% doesn't make them stretch. The 4th child
       (counter+bar markdown) gets margin-left:auto to push it + the
       shuffle + mode toggle that follow to the right edge. */
    /* ~= matches the exact class name (whole-word), so this rule applies
       to st-key-fc-header ONLY — not to st-key-fc-header-right. ONE
       continuous divider runs under the whole toolbar from this rule. */
    [class~="st-key-fc-header"] {{
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        width: 100% !important;
        gap: 12px !important;
        padding-bottom: 0.7rem !important;
        margin-bottom: 0.4rem !important;
        border-bottom: 1px solid rgba(31, 41, 55, 0.08) !important;
    }}
    /* Inner stVerticalBlock IS the flex container with two columns:
       fc-filter-tabs (left) and fc-header-right (right). */
    [class~="st-key-fc-header"] > [data-testid="stVerticalBlock"] {{
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        width: 100% !important;
    }}
    /* LEFT group — filter tabs, wide gap so labels breathe. */
    [class*="st-key-fc-filter-tabs"] {{
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 48px !important;
        flex: 0 0 auto !important;
    }}
    [class*="st-key-fc-filter-tabs"] > [data-testid="stVerticalBlock"] {{
        display: contents !important;
    }}
    [class*="st-key-fc-filter-tabs"] > [data-testid="stVerticalBlock"] > * {{
        width: auto !important;
        flex: 0 0 auto !important;
    }}

    /* RIGHT group — counter+bar, shuffle, mode toggle. margin-left:auto
       is the spacer that pushes the whole compact group to the right
       edge of the inner flex row. */
    [class*="st-key-fc-header-right"] {{
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 8px !important;
        flex: 0 0 auto !important;
        margin-left: auto !important;
    }}
    [class*="st-key-fc-header-right"] > [data-testid="stVerticalBlock"] {{
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 4px !important;
    }}
    [class*="st-key-fc-header-right"] > [data-testid="stVerticalBlock"] > * {{
        width: fit-content !important;
        flex: 0 0 auto !important;
        margin: 0 !important;
    }}
    /* Toggle wrapper — only layout/positioning (no fixed width). The
       wrapper sizes to fit-content of the inner segments. 4px margin
       is the gap to the shuffle on its left. */
    [class*="st-key-fc-mode-tabs"] {{
        width: fit-content !important;
        flex: 0 0 auto !important;
        margin-left: 4px !important;
    }}
    /* Base tab style — strip the default st.button pill so it reads as flat
       text. Higher specificity (0,3,2) than `button[kind="secondary"]`. */
    [class*="st-key-fc-tab-"] div[data-testid="stButton"] > button {{
        background: transparent !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        border-radius: 0 !important;
        padding: 4px 2px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.92rem !important;
        line-height: 1.3 !important;
        box-shadow: none !important;
        transform: none !important;
        transition: color 0.18s ease, border-color 0.18s ease !important;
        min-height: 0 !important;
        height: auto !important;
        min-width: 0 !important;
        white-space: nowrap !important;
    }}
    [class*="st-key-fc-tab-"] div[data-testid="stButton"] > button p,
    [class*="st-key-fc-tab-"] div[data-testid="stButton"] > button span {{
        font-size: 0.92rem !important;
        line-height: 1.3 !important;
        color: inherit !important;
        margin: 0 !important;
    }}
    /* Inactive tab — gray text, no underline */
    [class*="st-key-fc-tab-"][class*="-off"] div[data-testid="stButton"] > button {{
        color: #6b7280 !important;
        font-weight: 500 !important;
    }}
    [class*="st-key-fc-tab-"][class*="-off"] div[data-testid="stButton"] > button:hover {{
        color: #1f2937 !important;
        background: transparent !important;
        border-bottom-color: transparent !important;
    }}
    /* Active tab — violet text + violet underline */
    [class*="st-key-fc-tab-"][class*="-on"] div[data-testid="stButton"] > button {{
        color: #7c3aed !important;
        font-weight: 600 !important;
        border-bottom-color: #7c3aed !important;
    }}
    [class*="st-key-fc-tab-"][class*="-on"] div[data-testid="stButton"] > button:hover {{
        color: #7c3aed !important;
        background: transparent !important;
    }}

    /* Compact counter + mini progress bar (right side of card header).
       inline-flex sizes the meta div to its content (counter + bar);
       min-height matches the toggle/shuffle button height so it sits at
       the same vertical center as the other right-group items. */
    .fc-card-header-meta {{
        display: inline-flex;
        align-items: center;
        gap: 0.6rem;
        min-height: 32px;
    }}
    /* Force the stMarkdown chain that wraps it to content width AND zero
       vertical spacing so the meta div sits at the parent's vertical
       center (Streamlit's stMarkdown defaults add bottom padding that
       pushes the content visually low). */
    [class*="st-key-fc-header"] [data-testid="stMarkdownContainer"],
    [class*="st-key-fc-header"] [data-testid="stMarkdown"] {{
        width: auto !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    .fc-card-counter {{
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        color: #6b7280;
        font-size: 0.85rem;
        white-space: nowrap;
    }}
    .fc-mini-bar {{
        width: 90px;
        height: 4px;
        background: rgba(167, 139, 250, 0.18);
        border-radius: 999px;
        overflow: hidden;
    }}
    .fc-mini-bar-fill {{
        height: 100%;
        background: #7c3aed;
        border-radius: 999px;
        transition: width 0.25s ease;
    }}

    /* Shuffle slot — bare gray Material icon, transparent bg, lavender pill
       on hover. Broad selectors (button + button[kind="tertiary"]) defeat
       Streamlit's default-kind filled background. */
    [class*="st-key-fc-shuffle-tab"] button,
    [class*="st-key-fc-shuffle-tab"] button[kind="tertiary"],
    [class*="st-key-fc-shuffle-tab"] div[data-testid="stButton"] > button {{
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #6b7280 !important;
        padding: 4px 8px !important;
        min-width: 0 !important;
        height: 32px !important;
        border-radius: 8px !important;
        transition: color 0.18s ease, background 0.18s ease,
                    transform 0.18s ease !important;
    }}
    /* Higher-specificity selector + descendant target so the global
       tertiary :hover lilac doesn't reach the inner Material icon.
       Smaller jump (-0.5px) than other elements because the icon is
       small and -1px reads disproportionately large on it. */
    [class*="st-key-fc-shuffle-tab"] div[data-testid="stButton"] > button[kind="tertiary"]:hover,
    [class*="st-key-fc-shuffle-tab"] div[data-testid="stButton"] > button[kind="tertiary"]:hover *,
    [class*="st-key-fc-shuffle-tab"] button:hover {{
        background: transparent !important;
        color: #1f2937 !important;
        transform: translateY(-0.5px) !important;
    }}
    [class*="st-key-fc-shuffle-tab"] button [data-testid="stIconMaterial"] {{
        color: inherit !important;
        font-size: 1.05rem !important;
    }}

    /* Mode toggle — modern segmented control. Visual pill (white bg,
       border, rounded-full, fixed 160px width) lives on the INNER
       fc-mode-tabs container; layout (fit-content, flex, margin)
       lives on the OUTER fc-mode-tabs-wrapper below. ~= matches the
       exact class name so this rule applies to fc-mode-tabs ONLY,
       not to fc-mode-tabs-wrapper. */
    [class~="st-key-fc-mode-tabs"] {{
        position: relative !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: stretch !important;
        gap: 0 !important;
        background: white !important;
        border: 1px solid rgba(0, 0, 0, 0.20) !important;
        border-radius: 999px !important;
        padding: 0 !important;
        width: 160px !important;
        box-shadow: none !important;
        overflow: hidden !important;
    }}
    /* Flatten Streamlit's inner wrapper chain (outer keyed → tab keyed →
       inner stVerticalBlock → stElementContainer → stButton → button) so
       the button can stretch the full 50% slot. display:contents removes
       a wrapper from layout while keeping its children in place. */
    [class*="st-key-fc-mode-tabs"] > [data-testid="stVerticalBlock"],
    [class*="st-key-fc-mode-tab-"] > [data-testid="stVerticalBlock"] {{
        display: contents !important;
    }}
    /* Each tab takes EXACTLY 50% via flex:1. */
    [class*="st-key-fc-mode-tab-"] {{
        position: relative !important;
        flex: 1 1 0 !important;
        height: 100% !important;
    }}
    [class*="st-key-fc-mode-tab-"] [data-testid="stElementContainer"],
    [class*="st-key-fc-mode-tab-"] div[data-testid="stButton"],
    [class*="st-key-fc-mode-tab-"] div[data-testid="stButton"] > button {{
        width: 100% !important;
        height: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
        min-height: 0 !important;
    }}
    /* Segment button — fixed 30px height (= outer pill's content area),
       zero padding so the bg covers slot edge-to-edge, fully rounded so
       the active gradient pill conforms to the outer pill's curve. */
    [class*="st-key-fc-mode-tab-"] div[data-testid="stButton"] > button {{
        border: none !important;
        border-radius: 999px !important;
        padding: 0 !important;
        margin: 0 !important;
        height: 30px !important;
        min-height: 0 !important;
        min-width: 0 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        line-height: 1 !important;
        text-align: center !important;
        box-shadow: none !important;
        transition: all 200ms ease-in-out !important;
    }}
    [class*="st-key-fc-mode-tab-"] div[data-testid="stButton"] > button p {{
        font-size: 0.88rem !important;
        line-height: 1 !important;
        color: inherit !important;
        margin: 0 !important;
    }}
    /* Inactive segment — transparent, gray-400 text. Hover darkens text
       to ink only (no jump). */
    [class*="st-key-fc-mode-tab-"][class*="-off"]
        div[data-testid="stButton"] > button {{
        background: transparent !important;
        background-color: transparent !important;
        color: #9ca3af !important;
    }}
    [class*="st-key-fc-mode-tab-"][class*="-off"]
        div[data-testid="stButton"] > button:hover {{
        background: transparent !important;
        color: #1f2937 !important;
        transform: none !important;
    }}
    /* Active segment hover — no jump. */
    [class*="st-key-fc-mode-tab-"][class*="-on"]
        div[data-testid="stButton"] > button:hover {{
        transform: none !important;
    }}
    /* Active segment — violet→pink gradient, white text, fully rounded
       pill. No box-shadow (would be clipped by outer overflow:hidden). */
    [class*="st-key-fc-mode-tab-"][class*="-on"]
        div[data-testid="stButton"] > button {{
        background: linear-gradient(135deg, #A78BFA 0%, #F472B6 100%) !important;
        color: white !important;
        font-weight: 600 !important;
    }}
    [class*="st-key-fc-mode-tab-"][class*="-on"]
        div[data-testid="stButton"] > button p {{
        color: white !important;
    }}

    .fc-pill-row {{
        display: flex;
        justify-content: flex-end;
        align-items: center;
        margin-bottom: 1.4rem;
    }}
    .fc-pill {{
        font-family: 'Inter', sans-serif;
        display: inline-block;
        padding: 0.35rem 0.95rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
        letter-spacing: 0.01em;
    }}

    .fc-tile-row {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.7rem;
        margin-bottom: 1rem;
    }}
    .fc-tile {{
        aspect-ratio: 1 / 1;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 14px rgba(31, 41, 55, 0.06);
    }}
    .fc-tile img {{
        width: 100%; height: 100%;
        object-fit: cover; display: block;
    }}

    .fc-condition-name {{
        font-family: 'Poppins', sans-serif;
        font-size: 1.7rem;
        font-weight: 700;
        color: #1f2937;
        margin: 0 0 0.55rem 0;
        letter-spacing: -0.01em;
    }}
    .fc-short {{
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        color: #5a5170;
        line-height: 1.55;
        margin: 0 0 1.1rem 0;
    }}
    .fc-divider {{
        height: 1px;
        background: rgba(31, 41, 55, 0.06);
        margin: 0.4rem 0 0.9rem 0;
    }}
    .fc-rag-label {{
        font-family: 'Inter', sans-serif;
        font-size: 0.7rem;
        font-weight: 600;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin: 0 0 0.4rem 0;
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
    }}
    .fc-rag-text {{
        font-family: 'Inter', sans-serif;
        font-size: 0.92rem;
        color: #4a4360;
        line-height: 1.6;
        margin: 0 0 1rem 0;
    }}

    /* Self-assessment row under AI Explanation: two circular icon buttons
       (✓ / ✕) color-matched to the correct/wrong pill states. */
    [class*="st-key-fc-self-yes"] div[data-testid="stButton"] > button,
    [class*="st-key-fc-self-no"] div[data-testid="stButton"] > button {{
        width: 52px !important;
        height: 52px !important;
        min-width: 52px !important;
        min-height: 52px !important;
        border-radius: 50% !important;
        padding: 0 !important;
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        line-height: 1 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow:
            0 4px 14px rgba(31, 41, 55, 0.06),
            0 1px 3px rgba(31, 41, 55, 0.04) !important;
        transition: all 0.18s ease !important;
        margin: 0 auto !important;
    }}
    [class*="st-key-fc-self-yes"] div[data-testid="stButton"] > button {{
        background: #ecfdf5 !important;
        color: #047857 !important;
        border: 1px solid #a7f3d0 !important;
    }}
    [class*="st-key-fc-self-yes"] div[data-testid="stButton"] > button:hover,
    [class*="st-key-fc-self-yes"] div[data-testid="stButton"] > button:hover p {{
        color: #047857 !important;
    }}
    [class*="st-key-fc-self-yes"] div[data-testid="stButton"] > button:hover {{
        background: #d1fae5 !important;
        border-color: #a7f3d0 !important;
        transform: translateY(-1px) !important;
        box-shadow:
            0 8px 22px rgba(31, 41, 55, 0.10),
            0 2px 6px rgba(31, 41, 55, 0.06) !important;
    }}
    [class*="st-key-fc-self-no"] div[data-testid="stButton"] > button {{
        background: #fef2f2 !important;
        color: #b91c1c !important;
        border: 1px solid #fecaca !important;
    }}
    [class*="st-key-fc-self-no"] div[data-testid="stButton"] > button:hover,
    [class*="st-key-fc-self-no"] div[data-testid="stButton"] > button:hover p {{
        color: #b91c1c !important;
    }}
    [class*="st-key-fc-self-no"] div[data-testid="stButton"] > button:hover {{
        background: #fee2e2 !important;
        border-color: #fecaca !important;
        transform: translateY(-1px) !important;
        box-shadow:
            0 8px 22px rgba(31, 41, 55, 0.10),
            0 2px 6px rgba(31, 41, 55, 0.06) !important;
    }}
    /* Replace browser focus outline with a soft drop shadow so the
       picked self-grade button reads as "selected" without the purple
       focus ring fighting our color scheme. */
    [class*="st-key-fc-self-yes"] div[data-testid="stButton"] > button:focus,
    [class*="st-key-fc-self-yes"] div[data-testid="stButton"] > button:focus-visible,
    [class*="st-key-fc-self-yes"] div[data-testid="stButton"] > button:active,
    [class*="st-key-fc-self-yes"] div[data-testid="stButton"] > button:focus p,
    [class*="st-key-fc-self-yes"] div[data-testid="stButton"] > button:focus-visible p,
    [class*="st-key-fc-self-yes"] div[data-testid="stButton"] > button:active p {{
        color: #047857 !important;
    }}
    [class*="st-key-fc-self-yes"] div[data-testid="stButton"] > button:focus,
    [class*="st-key-fc-self-yes"] div[data-testid="stButton"] > button:focus-visible,
    [class*="st-key-fc-self-yes"] div[data-testid="stButton"] > button:active {{
        outline: none !important;
        background: #ecfdf5 !important;
        border-color: #a7f3d0 !important;
        box-shadow:
            0 8px 22px rgba(4, 120, 87, 0.18),
            0 2px 6px rgba(4, 120, 87, 0.10) !important;
    }}
    [class*="st-key-fc-self-no"] div[data-testid="stButton"] > button:focus,
    [class*="st-key-fc-self-no"] div[data-testid="stButton"] > button:focus-visible,
    [class*="st-key-fc-self-no"] div[data-testid="stButton"] > button:active,
    [class*="st-key-fc-self-no"] div[data-testid="stButton"] > button:focus p,
    [class*="st-key-fc-self-no"] div[data-testid="stButton"] > button:focus-visible p,
    [class*="st-key-fc-self-no"] div[data-testid="stButton"] > button:active p {{
        color: #b91c1c !important;
    }}
    [class*="st-key-fc-self-no"] div[data-testid="stButton"] > button:focus,
    [class*="st-key-fc-self-no"] div[data-testid="stButton"] > button:focus-visible,
    [class*="st-key-fc-self-no"] div[data-testid="stButton"] > button:active {{
        outline: none !important;
        background: #fef2f2 !important;
        border-color: #fecaca !important;
        box-shadow:
            0 8px 22px rgba(185, 28, 28, 0.18),
            0 2px 6px rgba(185, 28, 28, 0.10) !important;
    }}
    /* Pre-reveal: keep the ✕/✓ slots in place for layout stability but
       hide them so the bottom row doesn't shift when the answer is
       revealed. */
    [class*="st-key-fc-belowcard-prereveal"] [class*="st-key-fc-self-yes"],
    [class*="st-key-fc-belowcard-prereveal"] [class*="st-key-fc-self-no"] {{
        visibility: hidden !important;
    }}

    .fc-front-prompt {{
        font-family: 'Inter', sans-serif;
        color: #7a7090;
        text-align: center;
        margin: 0.4rem 0 1.1rem 0;
        font-size: 0.95rem;
    }}

    /* Multiple-choice options. Pre-pick: Streamlit buttons styled via
       keyed container `mc-opt`. Post-pick: HTML pills with state classes
       (correct-pick / wrong-pick / correct-reveal / faded). */
    [class*="st-key-mc-opt"] div[data-testid="stButton"] > button {{
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.98rem !important;
        color: #1f2937 !important;
        background: white !important;
        border: 1px solid rgba(31, 41, 55, 0.08) !important;
        border-radius: 16px !important;
        padding: 1.05rem 1.3rem !important;
        min-height: 60px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        box-shadow:
            0 4px 14px rgba(31, 41, 55, 0.06),
            0 1px 3px rgba(31, 41, 55, 0.04) !important;
        transition: all 0.18s ease !important;
        margin-bottom: 0.7rem !important;
    }}
    /* Force the inner text wrapper to also left-align (Streamlit centers
       button text by default via flex). */
    [class*="st-key-mc-opt"] div[data-testid="stButton"]
        > button > div,
    [class*="st-key-mc-opt"] div[data-testid="stButton"]
        > button > div > p {{
        text-align: left !important;
        justify-content: flex-start !important;
        width: 100% !important;
    }}
    [class*="st-key-mc-opt"] div[data-testid="stButton"] > button:hover {{
        background: #faf7ff !important;
        border-color: rgba(167, 139, 250, 0.32) !important;
        color: #6d28d9 !important;
        transform: translateY(-1px) !important;
        box-shadow:
            0 8px 22px rgba(31, 41, 55, 0.10),
            0 2px 6px rgba(31, 41, 55, 0.06) !important;
    }}

    /* Post-pick state overlays. Disabled buttons reuse the same DOM as
       pre-pick (so font, padding, shadow, and spacing are identical by
       construction); these rules only swap color/background/border per
       state and suppress the hover lift. */
    [class*="st-key-mc-opt-correct-"] div[data-testid="stButton"] > button,
    [class*="st-key-mc-opt-correct-"] div[data-testid="stButton"] > button p,
    [class*="st-key-mc-opt-reveal-"] div[data-testid="stButton"] > button,
    [class*="st-key-mc-opt-reveal-"] div[data-testid="stButton"] > button p {{
        color: #047857 !important;
    }}
    [class*="st-key-mc-opt-correct-"] div[data-testid="stButton"] > button,
    [class*="st-key-mc-opt-reveal-"] div[data-testid="stButton"] > button {{
        background: #ecfdf5 !important;
        border-color: #a7f3d0 !important;
        cursor: default !important;
        opacity: 1 !important;
    }}
    [class*="st-key-mc-opt-wrong-"] div[data-testid="stButton"] > button,
    [class*="st-key-mc-opt-wrong-"] div[data-testid="stButton"] > button p {{
        color: #b91c1c !important;
    }}
    [class*="st-key-mc-opt-wrong-"] div[data-testid="stButton"] > button {{
        background: #fef2f2 !important;
        border-color: #fecaca !important;
        cursor: default !important;
        opacity: 1 !important;
    }}
    [class*="st-key-mc-opt-faded-"] div[data-testid="stButton"] > button,
    [class*="st-key-mc-opt-faded-"] div[data-testid="stButton"] > button p {{
        color: #9ca3af !important;
    }}
    [class*="st-key-mc-opt-faded-"] div[data-testid="stButton"] > button {{
        background: #f9fafb !important;
        border-color: #e5e7eb !important;
        cursor: default !important;
        opacity: 0.75 !important;
    }}
    [class*="st-key-mc-opt-correct-"] div[data-testid="stButton"] > button:hover,
    [class*="st-key-mc-opt-reveal-"] div[data-testid="stButton"] > button:hover {{
        background: #ecfdf5 !important;
        color: #047857 !important;
        border-color: #a7f3d0 !important;
        transform: none !important;
    }}
    [class*="st-key-mc-opt-wrong-"] div[data-testid="stButton"] > button:hover {{
        background: #fef2f2 !important;
        color: #b91c1c !important;
        border-color: #fecaca !important;
        transform: none !important;
    }}
    [class*="st-key-mc-opt-faded-"] div[data-testid="stButton"] > button:hover {{
        background: #f9fafb !important;
        color: #9ca3af !important;
        border-color: #e5e7eb !important;
        transform: none !important;
    }}

    .mc-feedback-headline {{
        font-family: 'Inter', sans-serif;
        font-size: 0.98rem;
        font-weight: 600;
        margin: 1.4rem 0 0.15rem 0;
        letter-spacing: 0;
    }}
    .mc-feedback-headline.correct {{ color: #047857; }}
    .mc-feedback-headline.wrong {{ color: #b91c1c; }}
    .mc-feedback-sub {{
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: #6b7280;
        margin-bottom: 1.4rem;
    }}
    .mc-feedback-sub strong {{ color: #1f2937; font-weight: 600; }}

    /* Deck-complete state */
    .fc-complete-emoji {{
        font-size: 3rem;
        text-align: center;
        margin: 0.5rem 0 0.3rem 0;
    }}
    .fc-complete-title {{
        font-family: 'Poppins', sans-serif;
        font-size: 1.6rem;
        font-weight: 700;
        text-align: center;
        color: #1f2937;
        margin: 0 0 0.4rem 0;
    }}
    .fc-complete-sub {{
        font-family: 'Inter', sans-serif;
        color: #5a5170;
        text-align: center;
        margin: 0 0 1.5rem 0;
    }}
    /* Empty / complete state body wrapper. Matches the natural body height
       of a Learn-mode pre-reveal flashcard (3 image tiles + prompt + See
       Answer button) so transitions between states don't visibly jump.
       Content is vertically centered in the reserved space. */
    .fc-state-body {{
        min-height: 22rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }}

    /* ===== Flashcards hero (cloud + 3 layered cards) ===== */
    /* Allow the hero cloud to bleed past Streamlit's column boundaries. */
    [data-testid="stHorizontalBlock"],
    [data-testid="stColumn"],
    [data-testid="stVerticalBlock"] {{
        overflow: visible !important;
    }}

    .fc-hero {{
        position: relative;
        margin: 0.4rem auto 1.5rem auto;
        max-width: 720px;
        height: 460px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: visible;
    }}
    .fc-hero-cloud {{
        position: absolute;
        inset: -20px -140px;
        background:
            /* fluffy cloud puff silhouette, centered behind cards */
            url("{CLOUD_PUFF_SVG}") center 95% / 110% auto no-repeat,
            /* soft purple/lavender base wash */
            radial-gradient(ellipse 65% 55% at 50% 50%,
                rgba(192, 132, 252, 0.32), transparent 72%),
            radial-gradient(ellipse 48% 42% at 28% 30%,
                rgba(167, 139, 250, 0.30), transparent 68%),
            radial-gradient(ellipse 42% 38% at 74% 65%,
                rgba(244, 114, 182, 0.20), transparent 72%);
        z-index: 0;
        pointer-events: none;
    }}
    .fc-hero-cloud::after {{
        content: '';
        position: absolute; inset: 0;
        background-image: url("{SPARKLE_SVG}");
        background-size: 300px 300px;
        background-repeat: repeat;
        opacity: 0.7;
        pointer-events: none;
    }}
    .fc-hero-stack {{
        position: relative;
        width: 390px;
        height: 430px;
        z-index: 1;
    }}
    .fc-hero-card {{
        position: absolute;
        background: white;
        border-radius: 22px;
        box-shadow: 0 22px 48px rgba(167, 139, 250, 0.20),
                    0 4px 14px rgba(167, 139, 250, 0.10);
        border: 1px solid rgba(167, 139, 250, 0.10);
        width: 320px;
        height: 418px;
    }}
    .fc-hero-card.behind-2 {{
        left: 60px; top: 14px;
        z-index: 1;
        transform: rotate(8deg);
    }}
    .fc-hero-card.behind-1 {{
        left: 32px; top: 6px;
        z-index: 2;
        transform: rotate(4deg);
    }}
    .fc-hero-card.front {{
        left: 0; top: 0;
        z-index: 3;
        padding: 1.55rem 1.6rem 0.8rem 1.6rem;
        transform: rotate(-5deg);
    }}
    .fc-hero-pills {{
        display: flex;
        justify-content: flex-end;
        align-items: center;
        margin-bottom: 0.85rem;
    }}
    .fc-hero-pill {{
        font-family: 'Inter', sans-serif;
        padding: 0.22rem 0.65rem;
        border-radius: 999px;
        font-size: 0.66rem;
        font-weight: 700;
        letter-spacing: 0.01em;
    }}
    .fc-hero-title {{
        font-family: 'Poppins', sans-serif;
        font-size: 1.18rem;
        font-weight: 700;
        color: #1f2937;
        margin: 0.15rem 0 0.2rem 0;
        letter-spacing: -0.01em;
    }}
    .fc-hero-tiles {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.45rem;
        margin-bottom: 0.7rem;
    }}
    .fc-hero-tiles img {{
        width: 100%;
        aspect-ratio: 4 / 3;
        object-fit: cover;
        border-radius: 7px;
        display: block;
        box-shadow: 0 4px 14px rgba(31, 41, 55, 0.06);
    }}
    .fc-hero-desc {{
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        color: #5a5170;
        line-height: 1.45;
        margin-bottom: 0.45rem;
    }}
    .fc-hero-divider {{
        height: 1px;
        background: rgba(31, 41, 55, 0.06);
        margin: 0.3rem 0 0.25rem 0;
    }}
    .fc-hero-rag-label {{
        font-family: 'Inter', sans-serif;
        font-size: 0.55rem;
        font-weight: 600;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin: 0 0 0.2rem 0;
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
    }}
    .fc-hero-rag-label svg {{
        width: 10px;
        height: 10px;
    }}
    .fc-hero-rag-text {{
        font-family: 'Inter', sans-serif;
        font-size: 0.74rem;
        color: #4a4360;
        line-height: 1.5;
        margin: 0 0 0.3rem 0;
    }}
    .fc-hero-nav {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
        margin-top: 0.9rem;
    }}
    .fc-hero-nav-side {{
        font-family: 'Inter', sans-serif;
        font-size: 0.7rem;
        font-weight: 600;
        color: #1f2937;
        flex: 1;
    }}
    .fc-hero-nav-side.prev {{ text-align: left; }}
    .fc-hero-nav-side.next {{ text-align: right; }}
    .fc-hero-nav-circles {{
        display: flex;
        gap: 0.4rem;
    }}
    .fc-hero-nav-circle {{
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
        font-weight: 700;
        line-height: 1;
    }}
    .fc-hero-nav-circle.no {{
        background: #fef2f2;
        color: #b91c1c;
        border: 1px solid #fecaca;
    }}
    .fc-hero-nav-circle.yes {{
        background: #ecfdf5;
        color: #047857;
        border: 1px solid #a7f3d0;
    }}

    /* ===== Ask Questions page ===== */
    .chat-row {{
        display: flex;
        flex-direction: column;
        margin: 0.35rem auto;
        max-width: 720px;
    }}

    /* Reserves vertical space so the disclaimer doesn't jump when chips
       are replaced by the user-bubble + loading row on first click. */
    [class*="st-key-ask-state-slot"] {{
        min-height: 120px;
    }}
    .chat-row-user {{ align-items: flex-end; }}
    .chat-row-assistant {{ align-items: flex-start; }}

    .chat-bubble {{
        max-width: 80%;
        padding: 0.85rem 1.15rem;
        border-radius: 18px;
        font-family: 'Inter', sans-serif;
        line-height: 1.55;
        font-size: 0.95rem;
    }}
    .chat-bubble p {{ margin: 0 0 0.6rem 0; }}
    .chat-bubble p:last-child {{ margin-bottom: 0; }}
    .chat-bubble ul.chat-list {{
        margin: 0.2rem 0 0.6rem 0;
        padding-left: 1.2rem;
    }}
    .chat-bubble ul.chat-list li {{
        margin-bottom: 0.25rem;
    }}

    .chat-bubble-user {{
        background: linear-gradient(135deg, #f472b6 0%, #a78bfa 100%);
        color: white;
        border-bottom-right-radius: 6px;
    }}
    .chat-bubble-user strong {{ color: white; }}
    .chat-bubble-user em {{ color: white; opacity: 0.92; }}

    .chat-bubble-assistant {{
        background: white;
        color: #1f2937;
        border-bottom-left-radius: 6px;
        box-shadow: 0 4px 14px rgba(167, 139, 250, 0.10);
        border: 1px solid rgba(167, 139, 250, 0.10);
    }}
    .chat-bubble-assistant strong {{ color: #1f2937; }}

    /* In-text citation markers — academic-style [n] markers with a hover
       tooltip showing the source name, title, and clickable URL. */
    .chat-bubble .cite {{
        position: relative;
        margin: 0 2px 0 3px;
        cursor: pointer;
        font-family: 'Inter', sans-serif;
        font-size: 0.85em;
        font-weight: 500;
        color: #9CA3AF;
        transition: color 0.15s ease;
    }}
    .chat-bubble .cite:hover,
    .chat-bubble .cite:focus {{
        color: #111827;
        outline: none;
    }}
    /* Tighten spacing between adjacent citations so [1][2] reads as a unit. */
    .chat-bubble .cite + .cite {{
        margin-left: 0;
    }}
    .chat-bubble .cite .cite-tooltip {{
        position: absolute;
        bottom: calc(100% + 8px);
        left: 50%;
        transform: translateX(-50%);
        background: rgba(255, 255, 255, 0.96);
        backdrop-filter: blur(6px);
        -webkit-backdrop-filter: blur(6px);
        border: 1px solid rgba(167, 139, 250, 0.18);
        box-shadow:
            0 6px 18px rgba(124, 58, 237, 0.14),
            0 1px 3px rgba(31, 41, 55, 0.06);
        border-radius: 10px;
        padding: 7px 12px;
        width: max-content;
        max-width: min(360px, calc(100vw - 24px));
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        line-height: 1.5;
        color: #4B5563;
        text-align: left;
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
        transition: opacity 180ms ease, visibility 180ms ease;
        z-index: 50;
    }}
    /* Invisible bridge so the cursor can travel from [n] to the tooltip
       without crossing the 8px gap (which would otherwise close it). */
    .chat-bubble .cite .cite-tooltip::before {{
        content: '';
        position: absolute;
        bottom: -10px;
        left: 0;
        right: 0;
        height: 10px;
    }}
    .chat-bubble .cite:hover .cite-tooltip,
    .chat-bubble .cite:focus .cite-tooltip,
    .chat-bubble .cite .cite-tooltip:hover {{
        opacity: 1;
        visibility: visible;
        pointer-events: auto;
    }}
    .chat-bubble .cite .cite-tooltip-source {{
        font-weight: 700;
        color: #1F2937;
    }}
    .chat-bubble .cite .cite-tooltip-title {{
        font-weight: 400;
        color: #4B5563;
    }}
    .chat-bubble .cite .cite-tooltip-url {{
        font-weight: 500;
        color: #7C3AED;
        text-decoration: underline;
        text-decoration-color: rgba(124, 58, 237, 0.45);
        text-underline-offset: 2px;
        transition: color 0.15s ease, text-decoration-color 0.15s ease;
    }}
    .chat-bubble .cite .cite-tooltip-url:hover {{
        color: #5b21b6;
        text-decoration-color: #5b21b6;
    }}
    .chat-bubble .cite .cite-tooltip-accessed {{
        font-weight: 400;
        color: #6B7280;
    }}

    /* claude-assisted: pending-state loading row sits in the assistant column
       (max-width 720, margin auto) so the dots align flush-left with where
       the answer card will land once live_answer returns. */
    .ask-pending-loading {{
        display: flex;
        align-items: center;
        gap: 0.55rem;
        margin: 0.5rem auto 0.7rem auto;
        max-width: 720px;
        padding: 0.4rem 0.2rem;
        font-family: 'Inter', sans-serif;
        font-size: 0.92rem;
        color: #7a7090;
    }}
    .ask-pending-dots {{
        display: inline-flex;
        gap: 5px;
    }}
    .ask-pending-dots span {{
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: linear-gradient(135deg, #f472b6 0%, #a78bfa 100%);
        animation: ask-pending-bounce 1.2s infinite ease-in-out both;
    }}
    .ask-pending-dots span:nth-child(1) {{ animation-delay: -0.32s; }}
    .ask-pending-dots span:nth-child(2) {{ animation-delay: -0.16s; }}
    @keyframes ask-pending-bounce {{
        0%, 80%, 100% {{ transform: scale(0.6); opacity: 0.45; }}
        40%           {{ transform: scale(1.0); opacity: 1.0; }}
    }}

    /* Suggested-question chips — each row is a left-aligned flex row of
       auto-sized pills. No columns: each pill sizes to its own text. */
    .ask-chips-label {{
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: #7a7090;
        margin: 0.6rem auto 0.4rem auto;
        max-width: 720px;
        font-weight: 500;
    }}
    [class*="st-key-ask-chips-grid"] {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        justify-content: flex-start !important;
        gap: 1rem !important;
        max-width: 720px !important;
        margin: 0 auto !important;
    }}
    [class*="st-key-ask-chips-grid"] div[data-testid="stElementContainer"] {{
        flex: 0 0 auto !important;
        margin: 0 !important;
    }}
    /* Specificity (0,3,2) beats `div[data-testid="stButton"] > button[kind="secondary"]` (0,2,2). */
    [class*="st-key-ask-chips-grid"] div[data-testid="stButton"] > button {{
        background: white !important;
        border: 1px solid rgba(31, 41, 55, 0.08) !important;
        color: #5a5170 !important;
        font-weight: 500 !important;
        font-size: 0.87rem !important;
        border-radius: 10px !important;
        padding: 0.6rem 0.9rem !important;
        line-height: 1.4 !important;
        white-space: nowrap !important;
        text-align: center !important;
        box-shadow: none !important;
        transform: none !important;
        transition: border-color 160ms ease, background 160ms ease, color 160ms ease !important;
    }}
    [class*="st-key-ask-chips-grid"] div[data-testid="stButton"] > button:hover {{
        border-color: rgba(167, 139, 250, 0.45) !important;
        background: rgba(167, 139, 250, 0.04) !important;
        color: #1f2937 !important;
        transform: none !important;
    }}
    [class*="st-key-ask-chips-grid"] div[data-testid="stButton"] > button p {{
        margin: 0 !important;
        color: inherit !important;
    }}

    /* Bottom-bar background — kill Streamlit's dark band so the page
       gradient shows through behind the floating chat pill. */
    [data-testid="stBottom"],
    [data-testid="stBottomBlockContainer"],
    section[data-testid="stBottom"],
    .stBottom {{
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"] > div {{
        background: transparent !important;
    }}

    /* Chat input — glassmorphism pill: translucent white + backdrop blur,
       fully rounded, soft lavender shadow. Sits on the page background
       with no opaque bar behind it. */
    [data-testid="stChatInput"] {{
        background: rgba(255, 255, 255, 0.55) !important;
        backdrop-filter: blur(22px) saturate(160%) !important;
        -webkit-backdrop-filter: blur(22px) saturate(160%) !important;
        border: 1px solid rgba(255, 255, 255, 0.65) !important;
        border-radius: 999px !important;
        box-shadow:
            0 10px 30px rgba(167, 139, 250, 0.20),
            0 1px 0 rgba(255, 255, 255, 0.7) inset !important;
        padding: 0.3rem 0.5rem !important;
        max-width: 720px !important;
        margin: 0 auto 0.5rem auto !important;
    }}
    /* Strip the dark BaseWeb wrappers that Streamlit nests around the
       textarea, so the outer pill's glassmorphism shows through. */
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] > div > div,
    [data-testid="stChatInputContainer"],
    [data-testid="stChatInputTextArea"],
    [data-baseweb="textarea"],
    [data-baseweb="textarea"] > div,
    [data-baseweb="base-input"],
    [data-baseweb="base-input"] > div {{
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    [data-testid="stChatInput"] textarea {{
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 999px !important;
        padding: 0.55rem 0.9rem !important;
        color: #1f2937 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem !important;
        caret-color: #7c3aed !important;
    }}
    [data-testid="stChatInput"] textarea:focus {{
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }}
    [data-testid="stChatInput"] textarea::placeholder {{
        color: rgba(122, 112, 144, 0.75) !important;
    }}
    /* Submit button — brand gradient circle */
    [data-testid="stChatInput"] button {{
        background: linear-gradient(135deg, #f472b6 0%, #a78bfa 100%) !important;
        border: none !important;
        border-radius: 999px !important;
        color: white !important;
        box-shadow: 0 2px 8px rgba(167, 139, 250, 0.25) !important;
    }}
    [data-testid="stChatInput"] button:hover {{
        box-shadow: 0 4px 14px rgba(167, 139, 250, 0.40) !important;
    }}
    [data-testid="stChatInput"] button svg {{
        color: white !important;
        fill: white !important;
    }}

    .ask-disclaimer {{
        max-width: 720px;
        margin: 1.4rem auto 0 auto;
        padding: 0.85rem 1.1rem;
        background: rgba(255, 184, 162, 0.10);
        border: 1px solid rgba(255, 184, 162, 0.35);
        border-radius: 12px;
        font-family: 'Inter', sans-serif;
        font-size: 0.82rem;
        color: #5a5170;
        line-height: 1.5;
    }}
    .ask-disclaimer strong {{ color: #c2410c; }}

    /* Home-page disclaimer (body text) */
    .home-disclaimer {{
        font-family: 'Inter', sans-serif;
        font-size: 0.82rem;
        color: #7a7090;
        margin-top: 1.4rem;
        max-width: 500px;
        line-height: 1.5;
    }}
    .home-disclaimer strong {{ color: #5a5170; }}

    .mission-card {{
        display: flex;
        align-items: center;
        gap: 1rem;
        background: linear-gradient(135deg,
            rgba(192, 132, 252, 0.10),
            rgba(244, 114, 182, 0.08));
        border: 1px solid rgba(167, 139, 250, 0.18);
        border-radius: 18px;
        padding: 1.1rem 1.4rem;
        margin: 2.5rem auto 0 auto;
        max-width: 1100px;
        width: 100%;
    }}
    .mission-icon {{
        flex-shrink: 0;
        width: 38px; height: 38px;
        border-radius: 50%;
        background: linear-gradient(135deg, #ede9fe, #fce7f3);
        display: flex; align-items: center; justify-content: center;
    }}
    .mission-icon svg {{ width: 18px; height: 18px; }}
    .mission-text {{
        font-family: 'Inter', sans-serif;
        font-size: 0.94rem;
        color: #1f2937;
        line-height: 1.5;
    }}
    .mission-text strong {{
        font-weight: 700;
        color: #6d28d9;
    }}

    /* Secondary CTA rendered as <a> (matches button[kind="secondary"]). */
    .cta-secondary-link {{
        display: block;
        width: 100%;
        box-sizing: border-box;
        background: rgba(255, 255, 255, 0.85);
        color: #7c3aed !important;
        border: 1.5px solid #a78bfa;
        border-radius: 12px;
        padding: 0.7rem 1.5rem;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: 0.95rem;
        text-align: center;
        text-decoration: none !important;
        white-space: nowrap;
        min-width: max-content;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }}
    .cta-secondary-link:hover {{
        background: rgba(255, 255, 255, 1);
        border-color: #7c3aed;
        color: #7c3aed !important;
        text-decoration: none !important;
        transform: translateY(-1px);
    }}

    /* ===== How It Works section ===== */
    .hiw-anchor {{
        /* Anchor target — `scroll-margin-top` keeps the section title
           clear of the sticky/fixed nav when scrolled to. */
        scroll-margin-top: 80px;
        position: relative;
    }}
    .hiw-section {{
        margin: 4.5rem auto 1.5rem auto;
        max-width: 1200px;
        padding: 0 0.5rem;
    }}
    .hiw-header {{
        text-align: center;
        margin-bottom: 2.5rem;
    }}
    .hiw-title {{
        font-family: 'Poppins', sans-serif;
        font-size: clamp(1.8rem, 2.4vw + 1rem, 2.6rem);
        font-weight: 700;
        color: #1f2937;
        letter-spacing: -0.02em;
        margin: 0 0 0.6rem 0;
    }}
    .hiw-sub {{
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        color: #5a5170;
        line-height: 1.55;
        max-width: 580px;
        margin: 0 auto;
    }}
    .hiw-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.2rem;
    }}
    @media (max-width: 980px) {{
        .hiw-grid {{ grid-template-columns: repeat(2, 1fr); }}
    }}
    @media (max-width: 560px) {{
        .hiw-grid {{ grid-template-columns: 1fr; }}
    }}
    .hiw-card {{
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(167, 139, 250, 0.18);
        border-radius: 18px;
        padding: 1.6rem 1.4rem 1.5rem 1.4rem;
        box-shadow: 0 8px 28px rgba(167, 139, 250, 0.10);
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }}
    .hiw-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 14px 36px rgba(167, 139, 250, 0.18);
    }}
    .hiw-num {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2rem;
        height: 2rem;
        border-radius: 999px;
        background: linear-gradient(135deg, #f472b6 0%, #a78bfa 100%);
        color: white;
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(167, 139, 250, 0.28);
    }}
    .hiw-card-title {{
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        color: #1f2937;
        font-size: 1.05rem;
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.01em;
    }}
    .hiw-card-body {{
        font-family: 'Inter', sans-serif;
        color: #5a5170;
        font-size: 0.9rem;
        line-height: 1.55;
    }}
    .hiw-footnote {{
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        color: #5a5170;
        line-height: 1.55;
        text-align: center;
        max-width: 720px;
        margin: 2rem auto 0 auto;
    }}
    .coverage-section {{
        margin: 2.5rem auto 1.5rem auto;
        max-width: 1200px;
        padding: 0 0.5rem;
    }}
    .coverage-chips {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        justify-content: center;
        max-width: 880px;
        margin: 0 auto;
    }}
    .coverage-chip {{
        font-family: 'Inter', sans-serif;
        font-size: 0.88rem;
        font-weight: 500;
        padding: 0.45rem 0.95rem;
        border-radius: 999px;
        white-space: nowrap;
    }}
    .coverage-chip.benign {{
        background: #e0f2fe;
        color: #0369a1;
    }}
    .coverage-chip.malignant {{
        background: #fee2e2;
        color: #b91c1c;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# Block right-click context menu on every <img> in the parent Streamlit
# document. Uses components.html (iframe) because st.markdown strips
# <script> tags. Attaches once per session via a window flag.
components.html(
    """
    <script>
    (function() {
        var VERSION = 1;
        if (window.parent.__imgProtectVersion === VERSION) return;
        window.parent.__imgProtectVersion = VERSION;
        var doc = window.parent.document;
        doc.addEventListener('contextmenu', function(e) {
            if (e.target && e.target.tagName === 'IMG') {
                e.preventDefault();
            }
        }, true);
    })();
    </script>
    """,
    height=0,
)


# -------------------- Top Nav --------------------
def render_nav() -> None:
    # Whole top nav (logo + links) lives under one keyed container so
    # every nav-bar-level CSS rule can be scoped under
    # `[class*="st-key-menu-bar"]`. Per-item containers below stay as-is.
    with st.container(key="menu-bar"):
        nav_brand, nav_links, nav_right = st.columns(
            [2.2, 7, 1.2], vertical_alignment="center"
        )

        with nav_brand:
            st.markdown(
                f"<img class='brand-logo' "
                f"src='data:image/svg+xml;base64,{LOGO_SVG_B64}' "
                f"alt='SkinSight AI'/>",
                unsafe_allow_html=True,
            )

        with nav_links:
            # Each nav item is either an internal page (`page`) or an
            # external link (`url`). Code ↗ jumps straight to the GitHub
            # repo.
            nav_items = [
                {"label": "Home", "page": "home"},
                {"label": "Flashcards", "page": "flashcards"},
                {"label": "Ask Questions", "page": "ask"},
                {"label": "Code ↗",
                 "url": "https://github.com/madigwall/derm-clip-rag"},
            ]
            nl = st.columns(len(nav_items), vertical_alignment="center")
            for i, item in enumerate(nav_items):
                with nl[i]:
                    # Wrap every nav item in a keyed container so all
                    # share the same DOM depth (prevents vertical drift).
                    # Active uses a distinct key so CSS can highlight it.
                    if "url" in item:
                        with st.container(key=f"nav-item-ext-{i}"):
                            st.link_button(item["label"], item["url"],
                                           type="tertiary",
                                           use_container_width=True)
                    else:
                        page = item["page"]
                        key_suffix = (
                            f"nav-active-{page}"
                            if st.session_state.page == page
                            else f"nav-item-{page}"
                        )
                        with st.container(key=key_suffix):
                            if st.button(item["label"], key=f"nav_{page}",
                                         type="tertiary",
                                         use_container_width=True):
                                go(page)

        with nav_right:
            ic_night, ic_avatar = st.columns(2, vertical_alignment="center")
            with ic_night:
                with st.container(key="nav-icon-night"):
                    if st.button("", key="nav_night_mode",
                                 icon=":material/dark_mode:",
                                 type="tertiary"):
                        st.toast("Dark mode coming soon ✨", icon="🌙")
            with ic_avatar:
                with st.container(key="nav-icon-avatar"):
                    if st.button("MW", key="nav_avatar",
                                 type="tertiary"):
                        st.toast("Profile coming soon ✨", icon="👤")


# -------------------- Home --------------------
def render_home() -> None:
    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)

    hero_l, hero_r = st.columns([1.3, 1], gap="large")

    with hero_l:
        st.markdown(
            f"<div class='eyebrow'>{sparkle_chip_svg('cg')} Built for diverse "
            "learning. Designed for better learning.</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='hero-title'>AI-powered flashcards<br>"
            "for visual <span class='hero-accent'>dermatology</span><br>"
            "learning.</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='hero-sub'>Each card pulls diverse skin-tone images "
            "of the condition. Distractor answers aren't random — they're "
            "the conditions AI finds most visually confusing. AI explanations "
            "help you master each one.</div>",
            unsafe_allow_html=True,
        )

        cta1, _ = st.columns([2.5, 2.4])
        with cta1:
            if st.button("Start Learning  →", key="cta_start", type="primary",
                         use_container_width=True):
                go("flashcards")

        st.markdown(
            f"""
            <div class='features'>
                <div class='feature'>
                    <div class='feature-text'>
                        <div class='feature-title'>Diverse Dataset</div>
                        <div class='feature-sub'>Across skin tones</div>
                    </div>
                </div>
                <div class='feature'>
                    <div class='feature-text'>
                        <div class='feature-title'>AI-Powered</div>
                        <div class='feature-sub'>Smart explanations</div>
                    </div>
                </div>
                <div class='feature'>
                    <div class='feature-text'>
                        <div class='feature-title'>Evidence-Based</div>
                        <div class='feature-sub'>Trusted sources</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with hero_r:
        st.markdown(
            f"""
            <div class='fc-hero'>
              <div class='fc-hero-cloud'></div>
              <div class='fc-hero-stack'>
                <div class='fc-hero-card behind-2'></div>
                <div class='fc-hero-card behind-1'></div>
                <div class='fc-hero-card front'>
                  <div class='fc-hero-pills'>
                    <span class='fc-hero-pill'
                          style='background:#fee2e2;color:#b91c1c;'>
                      Malignant
                    </span>
                  </div>
                  <div class='fc-hero-tiles'>
                    <img src='data:image/svg+xml;base64,{TILE_B64[0]}' alt=''/>
                    <img src='data:image/svg+xml;base64,{TILE_B64[1]}' alt=''/>
                    <img src='data:image/svg+xml;base64,{TILE_B64[2]}' alt=''/>
                  </div>
                  <div class='fc-hero-title'>Basal Cell Carcinoma</div>
                  <div class='fc-hero-desc'>
                    Well-defined, pearly papule with telangiectasias and a
                    rolled border on sun-exposed skin.
                  </div>
                  <div class='fc-hero-divider'></div>
                  <div class='fc-hero-rag-label'>
                    {sparkle_chip_svg('hero-rag', gray=True)} AI Explanation
                  </div>
                  <div class='fc-hero-rag-text'>
                    Basal Cell Carcinoma is a slow-growing skin cancer that
                    appears as a small, shiny, pearly bump on sun-exposed
                    skin — look for translucent texture, rolled borders, and
                    fine arborizing telangiectasias.
                  </div>
                  <div class='fc-hero-nav'>
                    <span class='fc-hero-nav-side prev'>← Previous</span>
                    <div class='fc-hero-nav-circles'>
                      <span class='fc-hero-nav-circle no'>✕</span>
                      <span class='fc-hero-nav-circle yes'>✓</span>
                    </div>
                    <span class='fc-hero-nav-side next'>Next →</span>
                  </div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ----- How It Works section (anchor target for the hero CTA) -----
    st.markdown(
        """
        <div id='how-it-works' class='hiw-anchor'></div>
        <section class='hiw-section'>
          <div class='hiw-header'>
            <div class='hiw-title'>How It Works</div>
            <div class='hiw-sub'>
              Visual similarity search, a curated knowledge base, and
              AI-generated explanations — all in one study tool.
            </div>
          </div>
          <div class='hiw-grid'>
            <div class='hiw-card'>
              <div class='hiw-num'>1</div>
              <div class='hiw-card-title'>Visual Embeddings</div>
              <div class='hiw-card-body'>
                CLIP encodes dermatology images into a vector space, so
                visually similar conditions cluster together — across
                all skin tones.
              </div>
            </div>
            <div class='hiw-card'>
              <div class='hiw-num'>2</div>
              <div class='hiw-card-title'>Curated Knowledge Base</div>
              <div class='hiw-card-body'>
                DermNet articles are chunked and indexed in Chroma so
                each answer can be grounded in real sources.
              </div>
            </div>
            <div class='hiw-card'>
              <div class='hiw-num'>3</div>
              <div class='hiw-card-title'>Smart Flashcards</div>
              <div class='hiw-card-body'>
                Distractor answers aren't random — they're the
                conditions CLIP finds most visually confusable with
                the correct one.
              </div>
            </div>
            <div class='hiw-card'>
              <div class='hiw-num'>4</div>
              <div class='hiw-card-title'>Cited Explanations</div>
              <div class='hiw-card-body'>
                Every AI response cites the knowledge-base entry it
                drew from. No hallucinated sources.
              </div>
            </div>
          </div>
          <div class='hiw-footnote'>
            Images were grouped into Fitzpatrick I–II, III–IV, and V–VI
            categories — the dermatological research standard — to ensure
            a more diverse representation of skin tones.
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # ----- What's Covered section (7 conditions chip row) -----
    st.markdown(
        """
        <section class='coverage-section'>
          <div class='hiw-header'>
            <div class='hiw-title'>What This Covers</div>
            <div class='hiw-sub'>
              Seven conditions from the Stanford DDI dataset, with
              explanations grounded in DermNet articles.
            </div>
          </div>
          <div class='coverage-chips'>
            <span class='coverage-chip benign'>Melanocytic Nevi</span>
            <span class='coverage-chip benign'>Seborrheic Keratosis</span>
            <span class='coverage-chip benign'>Verruca Vulgaris</span>
            <span class='coverage-chip benign'>Epidermal Cyst</span>
            <span class='coverage-chip malignant'>Basal Cell Carcinoma</span>
            <span class='coverage-chip malignant'>Mycosis Fungoides</span>
            <span class='coverage-chip malignant'>Squamous Cell Carcinoma In Situ</span>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # ----- Disclaimer band (full-width, sits below How It Works) -----
    st.markdown(
        f"<div class='mission-card'>"
        f"<div class='mission-icon'>{sparkle_chip_svg('mission')}</div>"
        f"<div class='mission-text'>"
        f"<strong>Disclaimer:</strong> SkinSight AI is a learning tool "
        f"for visual recognition practice. It is not intended for medical "
        f"diagnosis, treatment, or clinical use."
        f"</div></div>",
        unsafe_allow_html=True,
    )


# -------------------- Flashcards --------------------
def _scroll_to_revealed_anchor() -> None:
    """Smooth-scroll the parent page to the #fc-revealed-anchor div, used
    once when the user transitions from pre-pick to post-pick (or pre-reveal
    to revealed). Multiple delayed retries defeat Streamlit's own scroll."""
    components.html(
        """
        <script>
        function _scrollReveal() {
            var doc = window.parent.document;
            var t = doc.getElementById('fc-revealed-anchor');
            if (!t) return;
            t.scrollIntoView({behavior: 'smooth', block: 'start'});
            var y = window.parent.scrollY;
            if (y > 80) {
                window.parent.scrollTo({
                    top: y - 80, behavior: 'smooth'
                });
            }
        }
        setTimeout(_scrollReveal, 100);
        setTimeout(_scrollReveal, 400);
        setTimeout(_scrollReveal, 800);
        </script>
        """,
        height=0,
    )


def _render_reveal_mode(card: dict) -> None:
    """Reveal-mode card body: pre-reveal shows a 'See Answer' button;
    post-reveal shows the condition name, AI Explanation, and Next button."""
    if not st.session_state.fc_revealed:
        st.markdown(
            "<div class='fc-front-prompt'>"
            "Take a look — what condition is shown?</div>",
            unsafe_allow_html=True,
        )
        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            if st.button("See Answer", key="fc_reveal_btn",
                         type="secondary", use_container_width=True):
                fc_reveal()
                st.rerun()
        return

    # Strip ** and * markers from the AI Explanation so it renders as plain
    # text. TODO: when live RAG output replaces card["rag"], re-evaluate
    # — the LLM will likely emit markdown, and we may want to keep some
    # emphasis for differentiator words. For now: plain text only.
    explanation = re.sub(r'\*\*(.+?)\*\*', r'\1', card["rag"])
    explanation = re.sub(r'\*([^*]+?)\*', r'\1', explanation)
    # Learn mode has no pick, so the cached "Correct — " prefix from the
    # Quiz feedback paragraph is meaningless here. Strip it.
    explanation = re.sub(r'^Correct\s*[—–-]\s*', '', explanation)
    short = re.sub(
        r'\*\*(.+?)\*\*', r'<strong>\1</strong>', card["definition"]
    )
    short = re.sub(
        r'\*([^*]+?)\*', r'<em>\1</em>', short
    )
    st.markdown(
        f"<div id='fc-revealed-anchor'></div>"
        f"<div class='fc-condition-name'>{card['name']}</div>"
        f"<div class='fc-short'>{short}</div>"
        f"<div class='fc-divider'></div>"
        f"<div class='fc-rag-label'>"
        f"{sparkle_chip_svg('rgg', gray=True)} AI Explanation</div>"
        f"<div class='fc-rag-text'>{explanation}</div>",
        unsafe_allow_html=True,
    )
    if st.session_state.fc_just_revealed:
        st.session_state.fc_just_revealed = False


def _render_mc_mode(card: dict, pos: int, picked, correct: str) -> None:
    """MC-mode card body: pre-pick shows 4 option buttons; post-pick shows
    styled pills (with picked/correct/faded states) + AI Explanation + Next."""
    options = fc_options_for(pos)

    st.markdown(
        "<div class='fc-front-prompt'>"
        "<span id='fc-revealed-anchor'></span>"
        "What condition is this?</div>",
        unsafe_allow_html=True,
    )

    if picked is None:
        for opt in options:
            key_slug = re.sub(r'[^a-z0-9]+', '-', opt.lower()).strip('-')
            with st.container(key=f"mc-opt-{key_slug}"):
                if st.button(opt, key=f"fc_mc_{key_slug}",
                             use_container_width=True):
                    # Pass `correct` so fc_pick auto-marks familiarity from
                    # the result. (In Quiz mode the ✕/✓ buttons are hidden;
                    # the pick itself drives familiarity.)
                    fc_pick(opt, correct)
                    st.rerun()
        # Hidden button — Space-bar shortcut auto-picks the correct answer
        # so the user can skip straight to the AI Explanation.
        if st.button("Reveal", key="fc_quiz_reveal_btn"):
            fc_pick(correct)
            st.rerun()
        return

    is_correct = picked == correct
    # Reuse the same disabled-button-in-keyed-container DOM as pre-pick so
    # spacing/font/padding stay identical. State prefix in the container
    # key (mc-opt-correct/-wrong/-reveal/-faded) is what the CSS overlay
    # rules target to swap colors.
    for opt in options:
        key_slug = re.sub(r'[^a-z0-9]+', '-', opt.lower()).strip('-')
        if opt == correct:
            state = "correct" if is_correct else "reveal"
        elif opt == picked:
            state = "wrong"
        else:
            state = "faded"
        with st.container(key=f"mc-opt-{state}-{key_slug}"):
            st.button(opt, key=f"fc_mc_done_{state}_{key_slug}",
                      disabled=True, use_container_width=True)

    if is_correct:
        explanation = card["rag"]
    else:
        explanation = card["feedback"].get(
            picked,
            f"{picked} and {correct} can look visually similar in "
            "CLIP embedding space."
        )
    # Strip ** and * markers — see TODO above _render_card_body explanation.
    explanation = re.sub(r'\*\*(.+?)\*\*', r'\1', explanation)
    explanation = re.sub(r'\*([^*]+?)\*', r'\1', explanation)

    st.markdown(
        "<div class='fc-divider'></div>"
        "<div class='fc-rag-label'>"
        f"{sparkle_chip_svg('rgg', gray=True)} AI Explanation</div>"
        f"<div class='fc-rag-text'>{explanation}</div>",
        unsafe_allow_html=True,
    )

    if st.session_state.fc_just_revealed:
        st.session_state.fc_just_revealed = False


def render_flashcards() -> None:
    displayed = fc_displayed_order()
    deck_size = len(displayed)
    pos = st.session_state.fc_pos
    is_complete = deck_size > 0 and pos >= deck_size
    is_empty = deck_size == 0
    has_active_card = not is_empty and not is_complete

    with st.container(key="fc-card"):
        # Card header — single flex row with 4 sibling slots:
        # [filter tabs] [counter + mini bar] [shuffle icon] [Learn|Quiz pills].
        # ALWAYS rendered (even on empty / complete states) so the user can
        # switch filters/modes to escape an empty subset. Key intentionally
        # avoids the "fc-card" substring so the keyed-container CSS for
        # `.fc-card` (white pill + shadow) doesn't apply to it.
        with st.container(key="fc-header"):
            # Three-group layout: LEFT = filter tabs wrapper, SPACER (the
            # margin-left:auto on the right group acts as the spacer),
            # RIGHT = controls wrapper (progress + shuffle + toggle).
            with st.container(key="fc-filter-tabs"):
                fam = st.session_state.fc_familiarity
                counts = {
                    "All Cards": len(st.session_state.fc_order),
                    "Familiar": sum(1 for v in fam.values() if v == "familiar"),
                    "Unfamiliar": sum(1 for v in fam.values() if v == "unfamiliar"),
                }
                for label in ["All Cards", "Familiar", "Unfamiliar"]:
                    slug = label.lower().replace(" ", "-")
                    is_active = st.session_state.fc_filter == label
                    suffix = "on" if is_active else "off"
                    with st.container(key=f"fc-tab-{slug}-{suffix}"):
                        if st.button(
                            f"{label} ({counts[label]})",
                            key=f"fc_filter_btn_{slug}",
                        ):
                            if not is_active:
                                fc_set_filter(label)
                                st.rerun()

            with st.container(key="fc-header-right"):
                display_num = min(pos + 1, deck_size) if deck_size else 0
                pct = (display_num / deck_size) * 100 if deck_size else 0
                st.markdown(
                    f"<div class='fc-card-header-meta'>"
                    f"<span class='fc-card-counter'>{display_num} / {deck_size}</span>"
                    f"<div class='fc-mini-bar'>"
                    f"<div class='fc-mini-bar-fill' style='width: {pct}%'></div>"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )

                with st.container(key="fc-shuffle-tab"):
                    if st.button(
                        "",
                        key="fc_shuffle",
                        icon=":material/shuffle:",
                        type="tertiary",
                    ):
                        fc_shuffle()
                        st.rerun()

                # Outer wrapper = layout (sizing, flex behavior, margins).
                # Inner pill (fc-mode-tabs) = visual styling (bg, border,
                # rounded-full). Separating these prevents layout overrides
                # from breaking the pill's appearance.
                with st.container(key="fc-mode-tabs-wrapper"):
                    with st.container(key="fc-mode-tabs"):
                        for mode_label in ["Learn", "Quiz"]:
                            mslug = mode_label.lower()
                            is_mode_active = st.session_state.fc_mode == mode_label
                            msuffix = "on" if is_mode_active else "off"
                            with st.container(key=f"fc-mode-tab-{mslug}-{msuffix}"):
                                if st.button(
                                    mode_label,
                                    key=f"fc_mode_btn_{mslug}",
                                    type="tertiary",
                                ):
                                    if not is_mode_active:
                                        fc_set_mode(mode_label)
                                        st.rerun()

        # Card body — empty / complete / active.
        if is_empty:
            fil = st.session_state.fc_filter
            label = "familiar" if fil == "Familiar" else "unfamiliar"
            st.markdown(
                "<div class='fc-state-body'>"
                "<div class='fc-complete-emoji'>📭</div>"
                f"<div class='fc-complete-title'>No {label} cards yet</div>"
                f"<div class='fc-complete-sub'>Mark cards with the "
                f"{'✓' if fil == 'Familiar' else '✕'} button to add them here.</div>"
                "</div>",
                unsafe_allow_html=True,
            )
        elif is_complete:
            # Show "Review Unfamiliar" only after finishing the full deck
            # (All Cards tab) — completing a filtered subset shouldn't
            # redirect the user to a different filter they didn't pick.
            unfamiliar_count = sum(
                1 for i in st.session_state.fc_order
                if st.session_state.fc_familiarity.get(i) == "unfamiliar"
            )
            offer_review = (
                st.session_state.fc_filter == "All Cards"
                and unfamiliar_count > 0
            )
            st.markdown(
                "<div class='fc-state-body'>"
                "<div class='fc-complete-emoji'>✨</div>"
                "<div class='fc-complete-title'>Deck complete</div>"
                f"<div class='fc-complete-sub'>You worked through all "
                f"{deck_size} cards. Shuffle to start a fresh round.</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            if offer_review:
                _, c1, c2, _ = st.columns([0.4, 1.5, 1.5, 0.4])
                with c1:
                    with st.container(key="fc-review-wrap"):
                        if st.button(
                            f"Review Unfamiliar ({unfamiliar_count})",
                            key="fc_review_unfamiliar",
                            type="secondary",
                            use_container_width=True,
                        ):
                            fc_set_filter("Unfamiliar")
                            st.rerun()
                with c2:
                    if st.button(
                        "Shuffle & Restart All",
                        key="fc_restart",
                        type="primary",
                        use_container_width=True,
                    ):
                        # True fresh start: drop all familiarity marks so
                        # Familiar/Unfamiliar tab counts return to 0.
                        st.session_state.fc_familiarity = {}
                        fc_set_filter("All Cards")
                        fc_shuffle()
                        st.rerun()
            else:
                _, mid, _ = st.columns([1, 2, 1])
                with mid:
                    if st.button(
                        "Shuffle & Restart",
                        key="fc_restart",
                        type="primary",
                        use_container_width=True,
                    ):
                        st.session_state.fc_familiarity = {}
                        fc_shuffle()
                        st.rerun()
        else:
            card = DECK[displayed[pos]]
            cat = card["category"]
            cat_bg, cat_fg = CATEGORY_COLORS[cat]
            card_name = card["name"]
            slug = _slugify(card_name)
            round_letter = card.get("round", "a")
            tiles = []
            for fst in ("12", "34", "56"):
                mime, payload = load_tile_b64(slug, round_letter, fst)
                tiles.append(
                    f"<div class='fc-tile'>"
                    f"<img src='data:{mime};base64,{payload}' "
                    f"alt='{card_name} FST {fst}'/></div>"
                )
            tile_html = "".join(tiles)
            st.markdown(
                f"<div class='fc-pill-row'>"
                f"<span class='fc-pill' "
                f"style='background:{cat_bg};color:{cat_fg};'>{cat}</span>"
                f"</div>"
                f"<div class='fc-tile-row'>{tile_html}</div>",
                unsafe_allow_html=True,
            )
            card_mode = current_card_mode(pos)
            picked = st.session_state.fc_picked
            if card_mode == "reveal":
                _render_reveal_mode(card)
            else:
                _render_mc_mode(card, pos, picked, card["name"])

    # Below-card navigation row — ALWAYS rendered for layout stability.
    # Buttons are disabled when there's no active card (empty/complete state).
    if has_active_card:
        card_mode = current_card_mode(pos)
        picked = st.session_state.fc_picked
        is_revealed = (
            st.session_state.fc_revealed if card_mode == "reveal"
            else picked is not None
        )
    else:
        card_mode = None
        is_revealed = False

    # In Quiz mode, the MC pick auto-marks familiarity, so the manual ✕/✓
    # buttons would be redundant — hide them. Always shown in Learn mode.
    show_self_grade = has_active_card and card_mode != "mc"

    state_key = "revealed" if is_revealed else "prereveal"
    with st.container(key=f"fc-belowcard-{state_key}"):
        c_prev, _gl, c_no, c_yes, _gr, c_next = st.columns(
            [1.2, 1, 0.7, 0.7, 1, 1.2]
        )
        with c_prev:
            with st.container(key="fc-prev-wrap"):
                if st.button("← Previous", key="fc_prev", type="tertiary",
                             use_container_width=True,
                             disabled=(not has_active_card or pos == 0)):
                    fc_prev()
                    st.rerun()
        with c_no:
            with st.container(key="fc-self-no"):
                if show_self_grade:
                    if st.button("✕", key="fc_self_no_btn"):
                        fc_mark("unfamiliar")
                        st.rerun()
        with c_yes:
            with st.container(key="fc-self-yes"):
                if show_self_grade:
                    if st.button("✓", key="fc_self_yes_btn"):
                        fc_mark("familiar")
                        st.rerun()
        with c_next:
            with st.container(key="fc-next-wrap"):
                if st.button("Next →", key="fc_next", type="tertiary",
                             use_container_width=True,
                             disabled=not has_active_card):
                    fc_advance()
                    st.rerun()

    # Keyboard shortcuts: ←/→ navigate Prev/Next, Enter triggers See Answer
    # (when present). Ignored while typing in inputs/textareas. Bound once per
    # parent window via a global flag so reruns don't stack listeners.
    components.html(
        """
        <script>
        (function() {
            var VERSION = 3;
            if (window.__fcKeysVersion === VERSION) return;
            var doc = window.parent.document;
            if (window.__fcKeysHandler) {
                doc.removeEventListener('keydown', window.__fcKeysHandler);
            }
            window.__fcKeysVersion = VERSION;
            function findBtn(key) {
                var wrap = doc.querySelector('[class*="st-key-' + key + '"]');
                if (!wrap) return null;
                var b = wrap.querySelector('button');
                return (b && !b.disabled) ? b : null;
            }
            window.__fcKeysHandler = function(e) {
                var t = e.target;
                if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA'
                          || t.isContentEditable)) return;
                var btn = null;
                if (e.key === 'ArrowLeft')  btn = findBtn('fc_prev');
                else if (e.key === 'ArrowRight') btn = findBtn('fc_next');
                else if (e.key === ' ' || e.code === 'Space') {
                    btn = findBtn('fc_reveal_btn')
                       || findBtn('fc_quiz_reveal_btn');
                } else return;
                if (!btn) return;
                e.preventDefault();
                btn.click();
            };
            doc.addEventListener('keydown', window.__fcKeysHandler);
        })();
        </script>
        """,
        height=0,
    )


# -------------------- Ask Questions --------------------
def render_ask() -> None:
    # claude-assisted: brand-styled hero replaces the plain page title
    st.markdown(
        f"<div class='ask-hero'>"
        f"<div class='ask-hero-icon'>"
        f"{chat_bubble_sparkle_svg('ask-hero-grad')}</div>"
        f"<div class='hero-title'>Ask about a condition, its look-alikes,"
        f" <span style='white-space: nowrap;'>or next steps.</span></div>"
        f"<div class='hero-sub'>Conversational search over the dermatology"
        f" knowledge base. Answers cite their sources.</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    pending = st.session_state.ask_pending

    for i, msg in enumerate(st.session_state.ask_messages):
        _render_chat_message(msg, i)

    # claude-assisted: defer live_answer until after render so the user bubble
    # + loading row are visible during the RAG wait. Chips and chat_input both
    # set ask_pending and rerun; the actual call happens at the bottom of this
    # function once the page has flushed.
    pending_loading_html = (
        "<div class='ask-pending-loading'>"
        "<span class='ask-pending-dots'>"
        "<span></span><span></span><span></span>"
        "</span>"
        "<span>Searching the knowledge base…</span>"
        "</div>"
    )
    if not st.session_state.ask_messages:
        # claude-assisted: keyed wrapper with min-height pins the disclaimer
        # so it doesn't jump up when chips are replaced by user-bubble + loader.
        with st.container(key="ask-state-slot"):
            if pending:
                _render_chat_message({"role": "user", "content": pending}, 0)
                st.markdown(pending_loading_html, unsafe_allow_html=True)
            else:
                st.markdown(
                    "<div class='ask-chips-label'>Try a question:</div>",
                    unsafe_allow_html=True,
                )
                with st.container(key="ask-chips-grid"):
                    for i, question in enumerate(CHIP_QUESTIONS):
                        if st.button(question, key=f"ask_chip_btn_{i}"):
                            st.session_state.ask_pending = question
                            st.rerun()
    elif pending:
        _render_chat_message(
            {"role": "user", "content": pending},
            len(st.session_state.ask_messages),
        )
        st.markdown(pending_loading_html, unsafe_allow_html=True)

    user_input = st.chat_input(
        "Ask about a condition, look-alike, or treatment…"
    )
    if user_input:
        st.session_state.ask_pending = user_input
        st.rerun()

    # Keyed wrapper gives the disclaimer a stable identity across renders so
    # Streamlit doesn't ghost the previous run's copy when the chips/pending
    # block above it changes shape.
    with st.container(key="ask-disclaimer-slot"):
        st.markdown(
            "<div class='ask-disclaimer'>"
            "<strong>Not medical advice.</strong> SkinSight AI is an educational "
            "tool. Always consult a qualified clinician for diagnosis or treatment."
            "</div>",
            unsafe_allow_html=True,
        )

    if pending:
        st.session_state.ask_pending = None
        from derm.rag.answer import answer as live_answer
        answer_msg = live_answer(pending, history=st.session_state.ask_messages)
        st.session_state.ask_messages.append({"role": "user", "content": pending})
        st.session_state.ask_messages.append(answer_msg)
        st.rerun()


# -------------------- Render --------------------
render_nav()

if st.session_state.page == "flashcards":
    render_flashcards()
elif st.session_state.page == "ask":
    render_ask()
else:
    render_home()


# -------------------- Click feedback --------------------
# Toast only for routes without a real page yet.
PAGE_DISPLAY_NAMES = {
    "resources": "Resources",
}
if st.session_state._just_clicked:
    target = st.session_state._just_clicked
    st.session_state._just_clicked = None
    if target not in ("home", "flashcards", "ask"):
        label = PAGE_DISPLAY_NAMES.get(target, target.title())
        st.toast(f"'{label}' page is coming soon.", icon="✨")
