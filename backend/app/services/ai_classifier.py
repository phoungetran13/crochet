"""Nhan dien loai san pham tu anh bang model AI pretrain (CLIP zero-shot).

Khac voi shape_detector.py (xu ly hinh hoc, chi hop voi net ve tay tren giay
trang), o day dung CLIP - model duoc OpenAI train tren hang tram trieu cap
anh-text that te - de phan loai zero-shot: so sanh embedding cua anh voi
embedding cua cac cau mo ta van ban ung voi tung loai san pham, chon loai co
do tuong dong (cosine similarity) cao nhat. Cach nay xu ly duoc ca anh chup
that (mau, nen phuc tap) lan anh phac thao, khong chi gioi han o net ve.
"""
from __future__ import annotations

import threading

import open_clip
import torch

from app.services.image_io import load_pil_image

_MODEL_NAME = "ViT-B-32"
_PRETRAINED = "openai"

# Moi loai san pham dung nhieu cau mo ta khac nhau (prompt ensembling) de
# tang do chinh xac zero-shot - CLIP nhay voi cach dien dat cau prompt.
_LABEL_PROMPTS = {
    "mu": [
        "a photo of a crochet hat",
        "a photo of a knitted beanie",
        "a photo of a bucket hat",
        "a sketch drawing of a hat",
    ],
    "ao": [
        "a photo of a crochet sweater",
        "a photo of a knitted cardigan",
        "a photo of a top or shirt",
        "a sketch drawing of a sweater",
    ],
    "vay": [
        "a photo of a crochet skirt",
        "a photo of a knitted skirt",
        "a photo of a ruffled skirt",
        "a sketch drawing of a skirt",
    ],
    "khan": [
        "a photo of a crochet scarf",
        "a photo of a knitted scarf",
        "a long rectangular knitted scarf",
        "a sketch drawing of a scarf",
    ],
}

_lock = threading.Lock()
_state: dict = {}


def _get_state():
    with _lock:
        if not _state:
            model, _, preprocess = open_clip.create_model_and_transforms(
                _MODEL_NAME, pretrained=_PRETRAINED
            )
            tokenizer = open_clip.get_tokenizer(_MODEL_NAME)
            model.eval()

            labels = list(_LABEL_PROMPTS.keys())
            all_prompts = []
            prompt_label_index = []
            for i, label in enumerate(labels):
                for prompt in _LABEL_PROMPTS[label]:
                    all_prompts.append(prompt)
                    prompt_label_index.append(i)

            with torch.no_grad():
                text_tokens = tokenizer(all_prompts)
                text_features = model.encode_text(text_tokens)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)

            _state["model"] = model
            _state["preprocess"] = preprocess
            _state["labels"] = labels
            _state["text_features"] = text_features
            _state["prompt_label_index"] = torch.tensor(prompt_label_index)
    return _state


def classify_garment_ai(image_bytes: bytes) -> tuple[str, float, dict]:
    state = _get_state()
    image = load_pil_image(image_bytes)
    image_input = state["preprocess"](image).unsqueeze(0)

    with torch.no_grad():
        image_features = state["model"].encode_image(image_input)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        similarities = (image_features @ state["text_features"].T).squeeze(0)

    labels = state["labels"]
    prompt_label_index = state["prompt_label_index"]

    # Lay similarity cao nhat trong cac prompt cua tung label (max-pooling)
    per_label_score = torch.full((len(labels),), -1.0)
    for i, sim in enumerate(similarities):
        label_idx = prompt_label_index[i]
        if sim > per_label_score[label_idx]:
            per_label_score[label_idx] = sim

    probs = torch.softmax(per_label_score * 100, dim=0)  # temperature scaling chuan CLIP
    best_idx = int(torch.argmax(probs))
    best_label = labels[best_idx]
    confidence = float(probs[best_idx])

    diagnostics = {
        "scores": {labels[i]: round(float(probs[i]), 3) for i in range(len(labels))},
        "model": f"{_MODEL_NAME} ({_PRETRAINED}, CLIP zero-shot)",
    }
    return best_label, round(confidence, 2), diagnostics
