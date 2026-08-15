"""Doc anh dung chung cho toan bo backend.

Ly do can file rieng: anh chup tu iPhone mac dinh la dinh dang HEIC, ma
OpenCV (cv2.imdecode) va Pillow mac dinh deu KHONG doc duoc - day la nguyen
nhan pho bien nhat khien "upload anh binh thuong cung loi". pillow-heif dang
ky them HEIC vao Pillow, nen chuan hoa: luon doc bang PIL truoc (co ho tro
HEIC), roi convert sang numpy/cv2 array khi can dung cho OpenCV.
"""
from __future__ import annotations

import io

import cv2
import numpy as np
import pillow_heif
from PIL import Image, ImageOps

pillow_heif.register_heif_opener()


def load_pil_image(image_bytes: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image)  # sua anh bi xoay sai huong tu EXIF (thuong gap voi anh dien thoai)
        return image.convert("RGB")
    except Exception as exc:
        raise ValueError(
            "Không đọc được ảnh. Định dạng hỗ trợ: JPG, PNG, HEIC/HEIF, WEBP. "
            "Hãy thử chụp/lưu lại ảnh ở định dạng JPG hoặc PNG."
        ) from exc


_MAX_DIMENSION = 1000  # anh HEIC/iPhone co the toi 24-48MP, GrabCut tren anh
# full-res co the mat vai phut hoac lam treo server - phai resize truoc.


def load_cv2_image(image_bytes: bytes) -> np.ndarray:
    """Tra ve anh dang BGR numpy array (dinh dang OpenCV can)."""
    pil_image = load_pil_image(image_bytes)
    rgb = np.array(pil_image)
    image_bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    h, w = image_bgr.shape[:2]
    scale = _MAX_DIMENSION / max(h, w)
    if scale < 1:
        image_bgr = cv2.resize(
            image_bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA
        )
    return image_bgr


def segment_foreground(image_bgr: np.ndarray, border_inset_ratio: float = 0.06) -> tuple[np.ndarray, np.ndarray] | None:
    """Tach san pham ra khoi nen bang GrabCut.

    Tra ve (mask, image_goc) voi mask cung kich thuoc anh goc (255=san pham,
    0=nen), hoac None neu GrabCut khong tach duoc gi hop ly (anh qua don
    gian/nho, hoac gan nhu toan bo anh la foreground). Giu nguyen kich thuoc
    goc (khong crop) de con phan tich vi tri tung vung (than/tay ao) theo
    toa do that trong anh.
    """
    h, w = image_bgr.shape[:2]
    if h < 20 or w < 20:
        return None

    mask = np.zeros((h, w), np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    x0 = int(w * border_inset_ratio)
    y0 = int(h * border_inset_ratio)
    rect = (x0, y0, w - 2 * x0, h - 2 * y0)

    try:
        cv2.setRNGSeed(0)  # GrabCut dung RNG noi bo cua OpenCV cho GMM - phai co dinh seed
        # de dam bao tat dinh (cung 1 anh luon ra cung 1 ket qua tach nen).
        cv2.grabCut(image_bgr, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
    except cv2.error:
        return None

    fg_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    fg_ratio = fg_mask.sum() / (255 * h * w)
    if fg_ratio < 0.02 or fg_ratio > 0.97:
        return None

    return fg_mask, image_bgr


def fill_background(image_bgr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Thay pixel nen (mask=0) bang mau trung binh cua vung foreground, de
    khong lam nhieu mau khi luong tu hoa (k-means)."""
    filled = image_bgr.copy()
    fg_pixels = image_bgr[mask > 0]
    if len(fg_pixels) > 0:
        mean_color = fg_pixels.mean(axis=0).astype(np.uint8)
        filled[mask == 0] = mean_color
    return filled


def crop_to_foreground(image_bgr: np.ndarray, border_inset_ratio: float = 0.06) -> np.ndarray:
    """Crop anh sat vung san pham (dung cho cac san pham 1 manh: khan, mu, vay)."""
    result = segment_foreground(image_bgr, border_inset_ratio)
    if result is None:
        return image_bgr
    fg_mask, original = result

    ys, xs = np.where(fg_mask > 0)
    y_min, y_max = ys.min(), ys.max()
    x_min, x_max = xs.min(), xs.max()

    cropped = original[y_min:y_max + 1, x_min:x_max + 1]
    cropped_mask = fg_mask[y_min:y_max + 1, x_min:x_max + 1]
    return fill_background(cropped, cropped_mask)
