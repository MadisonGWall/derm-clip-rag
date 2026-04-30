# claude-assisted: scaffolds notebooks/02_visual_similarity.ipynb cells 1–5
# into a one-shot script + adds .pt save schema
"""
Embed every DDI image with CLIP and save to data/private/embeddings_full.pt.

Ran once locally using MPS. Make sure to switch to cuda if using NVIDIA GPU.

Output is private (gitignored) to ensure I don't publish the dataset.  Uploaded to private HF Dataset later.
"""

from pathlib import Path

import open_clip
import pandas as pd
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset

# claude-assisted in writing root and directory code here
ROOT = Path(__file__).resolve().parents[1]
LABELS_CSV = ROOT / "data" / "private" / "labels.csv"
IMAGES_DIR = ROOT / "data" / "private" / "images"
OUT_PATH = ROOT / "data" / "private" / "embeddings_full.pt"

MODEL_ID = "ViT-B-32-quickgelu"
PRETRAINED = "openai"
BATCH_SIZE = 32


class DermImageDataset(Dataset):
    def __init__(self, image_dir, dataframe, label_col, transform):
        self.image_dir = Path(image_dir)
        self.df = dataframe.reset_index(drop=True)
        self.label_col = label_col
        self.transform = transform

    def __len__(self): # claude-assisted
        return len(self.df)

    def __getitem__(self, index):
        row = self.df.iloc[index]
        fname = row["DDI_file"]
        image = Image.open(self.image_dir / fname).convert("RGB") # claude-assisted with RGB
        return self.transform(image), row[self.label_col], fname, int(row["skin_tone"])


def clean_labels(df):
    s = df["disease"].str.replace("-", " ", regex=False).str.title()
    df["disease_clean"] = s.str.replace("(Nm)", "(NM)", regex=False)
    return df

# Madison wrote the embedding code and data loading loop. Claude assisted with line debugging.
def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Device: {device}")

    labels = clean_labels(pd.read_csv(LABELS_CSV))

    model, _, preprocess = open_clip.create_model_and_transforms(
        MODEL_ID, pretrained=PRETRAINED
    )
    model = model.to(device).eval()

    dataset = DermImageDataset(IMAGES_DIR, labels, "disease_clean", preprocess)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=False)

    embeddings, fnames, all_labels, skin_tone = [], [], [], []
    for batch_imgs, batch_labels, batch_fnames, batch_skin_tone in loader:
        batch_imgs = batch_imgs.to(device)
        with torch.no_grad():
            emb = model.encode_image(batch_imgs)
            emb = emb / emb.norm(dim=-1, keepdim=True)
        embeddings.append(emb.cpu())
        fnames.extend(batch_fnames)
        all_labels.extend(batch_labels)
        skin_tone.extend(batch_skin_tone.tolist())

    embeddings = torch.cat(embeddings, dim=0)

    torch.save(
        {
            "embeddings": embeddings,
            "fnames": fnames,
            "labels": all_labels,
            "skin_tone": skin_tone,
            "model_id": f"{MODEL_ID}/{PRETRAINED}",
        },
        OUT_PATH,
    )

    print(f"Embedded {embeddings.shape[0]} images, dim={embeddings.shape[1]}")
    print(f"Saved → {OUT_PATH.relative_to(ROOT)}")

# claude-assisted: added main guard
if __name__ == "__main__":
    main()
