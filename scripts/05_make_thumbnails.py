# Entirely written by Claude with prompting by Madison. Builds CLIP-style center-cropped square 
# thumbnails for the flashcard tiles. Reads image_map.json, picks first up to 3 filenames per FST
# bucket (deterministic; the same indices always map to the same rounds), and
# writes 300x300 JPGs to data/private/thumbnails/<slug>/round-<a|b|c>/<fst>.jpg.
# Empty buckets (e.g. Basal Cell Carcinoma FST 56) are skipped silently — the
# app renders a "no sample" placeholder for missing tiles.
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
IMAGE_MAP = ROOT / "data" / "public" / "image_map.json"
SRC_DIR = ROOT / "data" / "private" / "images"
OUT_DIR = ROOT / "data" / "private" / "thumbnails"

TARGET = 300
ROUND_LETTERS = ("a", "b", "c")


def slugify(name: str) -> str:
    return name.lower().replace(" ", "-")


def make_thumbnail(src: Path, dst: Path) -> None:
    im = Image.open(src).convert("RGB")
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    im = im.crop((left, top, left + side, top + side))
    im = im.resize((TARGET, TARGET), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "JPEG", quality=85, optimize=True)


def main() -> None:
    image_map = json.loads(IMAGE_MAP.read_text())
    written = 0
    for condition, fst_buckets in image_map.items():
        slug = slugify(condition)
        for fst in ("12", "34", "56"):
            files = fst_buckets.get(fst, [])
            for i, letter in enumerate(ROUND_LETTERS):
                if i >= len(files):
                    break
                src = SRC_DIR / files[i]
                dst = OUT_DIR / slug / f"round-{letter}" / f"{fst}.jpg"
                make_thumbnail(src, dst)
                written += 1
    print(f"wrote {written} thumbnails to {OUT_DIR}")


if __name__ == "__main__":
    main()
