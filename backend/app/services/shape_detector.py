"""Nhan dien loai san pham (mu/ao/vay/khan) tu anh phac thao ve tay.

Khong dung deep learning: anh chup phac thao tren giay nen dung phan tich
hinh hoc (contour, ty le, do loi) la du. Diem kho thuc te la anh chup bang
dien thoai thuong co: bong do khong deu, canh to giay/ban lam contour ngoai
cung sai lech net ve that su. Vi vay pipeline duoc thiet ke de:
  1. Dung adaptive threshold (khong phai global Otsu) de chiu duoc anh sang
     khong deu tren mat giay.
  2. Loai bo cac contour qua lon (>85% dien tich anh) vi do thuong la vien
     giay/ban chup chu khong phai net ve.
  3. Uu tien contour co dang net ve (duong vien mo, khong dac ruot) bang
     cach so sanh dien tich contour voi dien tich hinh chu nhat bao quanh.
"""
from __future__ import annotations

import cv2
import numpy as np

GARMENT_TYPES = ("mu", "ao", "vay", "khan")

_MAX_DIMENSION = 1200  # resize truoc khi xu ly de on dinh + nhanh hon
_PAGE_AREA_RATIO = 0.85  # contour lon hon nguong nay coi la vien giay/nen, bo qua
_MIN_AREA_RATIO = 0.01  # contour nho hon nguong nay coi la nhieu, bo qua


def _resize_if_needed(image: np.ndarray) -> np.ndarray:
    h, w = image.shape[:2]
    scale = _MAX_DIMENSION / max(h, w)
    if scale < 1:
        image = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return image


def _binarize(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    # Adaptive threshold chiu duoc bong do / anh sang khong deu tot hon Otsu toan cuc
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 35, 10
    )
    # Dong net ve tay bi dut quang de contour lien mach
    kernel = np.ones((9, 9), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return binary


def _find_sketch_contour(binary: np.ndarray):
    image_area = binary.shape[0] * binary.shape[1]
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    candidates = []
    for c in contours:
        area = cv2.contourArea(c)
        ratio = area / image_area
        if ratio > _PAGE_AREA_RATIO or ratio < _MIN_AREA_RATIO:
            continue
        candidates.append((area, c))

    if not candidates:
        # fallback: khong loc duoc gi hop ly, dung contour lon nhat nhu cu
        return max(contours, key=cv2.contourArea)

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _bottom_component_count(binary: np.ndarray, contour) -> int:
    x, y, w, h = cv2.boundingRect(contour)
    bottom_band = binary[y + int(h * 0.85):y + h, x:x + w]
    if bottom_band.size == 0:
        return 0
    num_labels, _ = cv2.connectedComponents(bottom_band)
    return max(num_labels - 1, 0)


def _convexity_defect_count(contour) -> int:
    hull_indices = cv2.convexHull(contour, returnPoints=False)
    if hull_indices is None or len(hull_indices) < 4:
        return 0
    hull_indices = np.sort(hull_indices, axis=0)
    try:
        defects = cv2.convexityDefects(contour, hull_indices)
    except cv2.error:
        return 0
    if defects is None:
        return 0
    perimeter_scale = cv2.arcLength(contour, True)
    significant = 0
    for i in range(defects.shape[0]):
        _, _, _, depth = defects[i, 0]
        if depth / 256.0 > perimeter_scale * 0.02:
            significant += 1
    return significant


def classify_garment(image_bytes: bytes) -> tuple[str, float, dict]:
    from app.services.image_io import load_cv2_image

    image = load_cv2_image(image_bytes)
    image = _resize_if_needed(image)
    binary = _binarize(image)
    contour = _find_sketch_contour(binary)
    if contour is None:
        raise ValueError(
            "Khong tim thay net ve trong anh. Hay chup ro net ve, giay trang, "
            "anh sang deu, tranh bong do len ban ve."
        )

    x, y, w, h = cv2.boundingRect(contour)
    aspect = max(w, h) / max(min(w, h), 1)

    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    contour_area = cv2.contourArea(contour)
    solidity = contour_area / hull_area if hull_area > 0 else 0

    defects = _convexity_defect_count(contour)
    bottom_legs = _bottom_component_count(binary, contour)

    diagnostics = {
        "aspect_ratio": round(aspect, 2),
        "solidity": round(solidity, 2),
        "convexity_defects": defects,
        "bottom_components": bottom_legs,
        "bounding_box": {"w": w, "h": h},
    }

    scores = {t: 0.0 for t in GARMENT_TYPES}

    # Khan: dai va hep
    if aspect >= 2.3:
        scores["khan"] += 2.0
    elif aspect >= 1.6:
        scores["khan"] += 0.5

    # Vay: hinh thang/tam giac, thuong khong co "tay" nhung co the loe o day
    # (dung bottom rong hon top qua ty le vung duoi so voi vung tren)
    if 0.8 <= aspect <= 2.0 and bottom_legs <= 1:
        scores["vay"] += 0.8

    # Ao: co tay ao => nhieu diem loi/lom (defects)
    if defects >= 2 and aspect < 2.0:
        scores["ao"] += 1.5 + min(defects, 4) * 0.3
    if 0.9 <= aspect <= 1.8:
        scores["ao"] += 0.5

    # Mu: gan tron/oval, solidity cao, khong co tay/chan
    if solidity >= 0.85 and aspect <= 1.5:
        scores["mu"] += 1.5
    if defects <= 1:
        scores["mu"] += 0.5

    best_type = max(scores, key=scores.get)
    total = sum(scores.values()) or 1.0
    confidence = scores[best_type] / total

    return best_type, round(confidence, 2), diagnostics
