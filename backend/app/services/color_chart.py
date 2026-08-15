"""Sinh pixel/color chart (kieu C2C) tu anh.

Nguyen tac: chi manh CHINH (thuong la than truoc, mang hoa tiet/hinh anh
thiet ke) moi duoc ve chart theo dung mau tu anh; cac manh PHU (than sau, tay
ao, cac tang vay khong phai tang chinh) moc mau tron dong bo theo mau chu dao
- giong cach mot pattern crochet thuc te duoc thiet ke (khong ai in nguyen tam
anh chup len ca 4-5 manh khac nhau).

Cac ham *_from_array lam viec truc tiep tren vung anh (ndarray) da duoc
garment_regions.py phan tich rieng cho tung manh (vd: chi vung tay ao trai
tren anh that, khong phai ca buc anh) - de chart phan anh dung hinh dang/mau
sac that cua tung manh, khong uoc luong dai khai.
"""
from __future__ import annotations

import colorsys

import cv2
import numpy as np
from sklearn.cluster import KMeans

from app.services.image_io import crop_to_foreground, load_cv2_image

# Chi "snap" (chuan hoa) mau gan nhu KHONG CO sac mau (trang/den/xam) - vi
# day la vung de bi lech mau do anh sang/can bang trang cua camera. Mau co
# sac ro rang (do, xanh, vang...) thi GIU NGUYEN mau that trich xuat tu anh,
# khong ep ve mot bang mau co dinh - tranh mat mau goc cua san pham that.
_SATURATION_THRESHOLD = 0.12


def snap_to_basic_color(rgb: tuple[int, int, int]) -> tuple[str, str]:
    """Neu mau gan nhu trung tinh (trang/den/xam) thi chuan hoa ve dung mau
    do; neu la mau co sac ro rang thi giu nguyen mau goc tu anh (khong doan/
    ep ve bang mau co dinh)."""
    r, g, b = rgb
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    original_hex = "#{:02x}{:02x}{:02x}".format(r, g, b)

    _, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if s < _SATURATION_THRESHOLD:
        if v > 0.9:
            return "trang", "#ffffff"
        if v < 0.15:
            return "den", "#111111"
        return "xam", "#9e9e9e"

    return "mau goc", original_hex


def grid_size_for_dimensions(width_cm: float, height_cm: float, max_cells: int = 60, min_cells: int = 4) -> tuple[int, int]:
    """Tinh so cot/hang giu dung ty le that cua manh (vd: khan dai phai ra
    luoi dai, khong bi ep vuong nhu truoc)."""
    longest = max(width_cm, height_cm, 1)
    scale = max_cells / longest
    cols = max(round(width_cm * scale), min_cells)
    rows = max(round(height_cm * scale), min_cells)
    return cols, rows


def generate_pixel_chart_from_array(
    image_bgr: np.ndarray,
    cols: int,
    rows: int,
    num_colors: int = 6,
) -> tuple[list[list[str]], dict[str, str]]:
    resized = cv2.resize(image_bgr, (cols, rows), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    pixels = rgb.reshape(-1, 3).astype(np.float32)

    k = min(num_colors, cols * rows)
    kmeans = KMeans(n_clusters=k, n_init=4, random_state=0).fit(pixels)
    labels = kmeans.labels_.reshape(rows, cols)
    centers = kmeans.cluster_centers_.astype(int)
    # Snap tung tam cum ve mau co ban gan nhat (trang/do/xam/...) thay vi giu
    # mau pha tho tu k-means - de nhan biet va giong cach chon mau soi thuc te.
    snapped_centers = [snap_to_basic_color(tuple(c))[1] for c in centers]

    legend: dict[str, str] = {}
    grid: list[list[str]] = []
    for r in range(rows):
        row_hex = []
        for c in range(cols):
            hex_code = snapped_centers[labels[r, c]]
            row_hex.append(hex_code)
            legend.setdefault(hex_code, hex_code)
        grid.append(row_hex)

    return grid, legend


def dominant_color_hex_from_array(image_bgr: np.ndarray) -> str:
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB).reshape(-1, 3).astype(np.float32)
    mean_color = tuple(rgb.mean(axis=0).astype(int))
    return snap_to_basic_color(mean_color)[1]


def solid_pixel_chart(cols: int, rows: int, hex_color: str) -> tuple[list[list[str]], dict[str, str]]:
    grid = [[hex_color] * cols for _ in range(rows)]
    return grid, {hex_color: hex_color}


def color_bands_by_row(
    image_bgr: np.ndarray,
    rows: int,
    num_colors: int = 3,
    min_segment_ratio: float = 0.05,
) -> list[str]:
    """Mau trung binh cua tung 'dai hang' that trong anh (tren xuong duoi),
    gom nhom lai thanh toi da num_colors mau bang k-means de tao cac khoi
    mau doi lien tuc (giong ky thuat doi mau theo hang trong graphgan/C2C),
    thay vi doi mau lien tuc tung hang mot gay roi mat.

    num_colors mac dinh THAP (3) vi hau het ao/khan thuc te chi co 1-3 mau
    chinh (khong phai anh nhieu mau nhu tranh). Sau khi phan cum, con lam
    min bang bo phieu da so trong 1 cua so truot (~5% tong so hang) de loai
    nhieu tung hang le - tranh tinh trang "doi mau lien tuc" khi ranh gioi
    mau trong anh khong hoan toan sac net.

    Tat dinh 100%: cung 1 anh + cung so rows luon cho ra cung 1 ket qua
    (random_state co dinh), khac anh se cho ket qua khac (mau/vi tri doi
    mau phu thuoc that vao noi dung anh).
    """
    resized = cv2.resize(image_bgr, (1, rows), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).reshape(rows, 3).astype(np.float32)

    k = min(num_colors, rows)
    kmeans = KMeans(n_clusters=k, n_init=4, random_state=0).fit(rgb)
    centers = kmeans.cluster_centers_.astype(int)
    labels = kmeans.labels_
    # Snap tung tam cum ve mau co ban gan nhat truoc khi lam min - dam bao
    # "trang la trang, do la do, xam la xam" thay vi mau pha kho hieu.
    snapped_centers = [snap_to_basic_color(tuple(c))[1] for c in centers]

    window = max(3, int(rows * min_segment_ratio))
    half = window // 2
    smoothed = np.empty_like(labels)
    for i in range(rows):
        lo, hi = max(0, i - half), min(rows, i + half + 1)
        counts = np.bincount(labels[lo:hi], minlength=k)
        smoothed[i] = int(np.argmax(counts))

    return [snapped_centers[label] for label in smoothed]


def run_length_encode(values: list[str]) -> list[tuple[int, int, str]]:
    """Gom danh sach gia tri lien tiep giong nhau thanh (start_idx, end_idx, value),
    idx 0-based, end_idx la idx cuoi cung (bao gom) cua doan do."""
    if not values:
        return []
    segments: list[tuple[int, int, str]] = []
    start = 0
    current = values[0]
    for i in range(1, len(values)):
        if values[i] != current:
            segments.append((start, i - 1, current))
            start = i
            current = values[i]
    segments.append((start, len(values) - 1, current))
    return segments


# ---- Cac ham tien ich lam viec truc tiep tu bytes (dung khi khong can tach vung) ----

def generate_pixel_chart(image_bytes: bytes, cols: int, rows: int, num_colors: int = 6) -> tuple[list[list[str]], dict[str, str]]:
    image = crop_to_foreground(load_cv2_image(image_bytes))
    return generate_pixel_chart_from_array(image, cols, rows, num_colors)


def dominant_color_hex(image_bytes: bytes) -> str:
    """Mau chu dao cua san pham (sau khi tach nen) - dung cho cac manh phu
    (than sau...) moc mau tron dong bo, khong bi nhieu theo nen anh."""
    image = crop_to_foreground(load_cv2_image(image_bytes))
    return dominant_color_hex_from_array(image)
