"""Phan tach vung than/tay ao THAT tu anh, dua tren hinh dang (mask) chu
khong phai gia dinh dai khai.

Nguyen ly: voi anh chup ao (mac hoac trai phang), cot pixel thuoc vung THAN
thuong co do cao lien tuc lon nhat (keo dai tu vai xuong gau ao), trong khi
cot pixel thuoc vung TAY AO co do cao thap hon (tay ao ngan hon chieu dai
than, hoac chi noi ngang o vung nguc/vai khi ao trai phang). Bang cach do do
cao mask theo tung cot pixel (column-height profile), ta xac dinh duoc ranh
gioi than/tay that su tren anh, thay vi chia deu 1/3-1/3-1/3 mot cach vo can
cu.
"""
from __future__ import annotations

import cv2
import numpy as np

from app.services.image_io import fill_background, load_cv2_image, segment_foreground

BODY_HEIGHT_THRESHOLD_RATIO = 0.7  # cot duoc tinh la "than" neu cao >= 70% cot cao nhat
MIN_SLEEVE_COLUMNS = 5  # can it nhat vai cot pixel moi coi la co vung tay ao rieng biet


def _column_height_profile(mask: np.ndarray) -> np.ndarray:
    h, w = mask.shape
    heights = np.zeros(w, dtype=np.int32)
    for x in range(w):
        ys = np.where(mask[:, x] > 0)[0]
        if len(ys) > 0:
            heights[x] = ys.max() - ys.min() + 1
    return heights


def _crop_region(image_filled: np.ndarray, mask: np.ndarray, x0: int, x1: int) -> np.ndarray | None:
    """Cat vung [x0:x1) roi crop tiep theo dung do cao mask trong vung do (khong lay ca khung anh)."""
    if x1 <= x0:
        return None
    sub_mask = mask[:, x0:x1]
    ys, xs = np.where(sub_mask > 0)
    if len(ys) == 0:
        return None
    y_min, y_max = ys.min(), ys.max()
    sub_image = image_filled[y_min:y_max + 1, x0:x1]
    sub_mask_cropped = sub_mask[y_min:y_max + 1, :]
    return fill_background(sub_image, sub_mask_cropped)


def detect_ao_regions(image_bytes: bytes) -> dict[str, np.ndarray]:
    """Phan tich anh ao thanh cac vung: 'body' (than), 'sleeve_left', 'sleeve_right'.

    Neu khong tach duoc ro rang (anh khong du net, GrabCut that bai, hoac
    khong tim thay vung tay ao rieng biet), tra ve chi {'body': <ca anh da
    tach nen>} - tuc la fallback ve xu ly nhu 1 vung duy nhat, khong bia dat
    vung tay ao khong co that.
    """
    image = load_cv2_image(image_bytes)
    result = segment_foreground(image)
    if result is None:
        return {"body": image}

    mask, original = result
    ys, xs = np.where(mask > 0)
    x_min, x_max = xs.min(), xs.max()
    y_min, y_max = ys.min(), ys.max()

    # Gioi han vung lam viec ve bbox cua foreground de profile khong bi anh huong boi vien anh thua
    work_mask = mask[y_min:y_max + 1, x_min:x_max + 1]
    work_image = original[y_min:y_max + 1, x_min:x_max + 1]

    heights = _column_height_profile(work_mask)
    max_h = heights.max() if heights.max() > 0 else 1
    body_cols = np.where(heights >= BODY_HEIGHT_THRESHOLD_RATIO * max_h)[0]

    if len(body_cols) == 0:
        return {"body": fill_background(work_image, work_mask)}

    body_x0, body_x1 = int(body_cols.min()), int(body_cols.max()) + 1

    regions: dict[str, np.ndarray] = {}
    body_region = _crop_region(work_image, work_mask, body_x0, body_x1)
    regions["body"] = body_region if body_region is not None else fill_background(work_image, work_mask)

    if body_x0 >= MIN_SLEEVE_COLUMNS:
        left = _crop_region(work_image, work_mask, 0, body_x0)
        if left is not None:
            regions["sleeve_left"] = left

    if work_mask.shape[1] - body_x1 >= MIN_SLEEVE_COLUMNS:
        right = _crop_region(work_image, work_mask, body_x1, work_mask.shape[1])
        if right is not None:
            regions["sleeve_right"] = right

    return regions
