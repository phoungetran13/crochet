"""Sinh so do kich thuoc (schematic) dang SVG cho tung manh - giong trang
"BODY / SLEEVE / FRONT / BACK" trong cac pattern crochet thuong mai that:
hinh khoi don gian kem so do (cm) ghi doc theo tung canh.

Day la thu duoc lam DUOC mot cach chinh xac (chi la ve hinh chu nhat theo
dung ty le width_cm/height_cm da tinh), khac voi viec co gang "bia" ra ky
thuat cable crochet phuc tap - dieu ma khong co cong thuc nao suy ra duoc
tu anh/so do mot cach tu dong.
"""
from __future__ import annotations

_PADDING = 24
_GAP = 40
_LABEL_SPACE = 46
_MAX_PIECE_PX = 220
_MIN_PIECE_PX = 60


def _scale_dimensions(width_cm: float, height_cm: float, max_px: int = _MAX_PIECE_PX) -> tuple[float, float]:
    longest = max(width_cm, height_cm, 1)
    scale = max_px / longest
    w = max(width_cm * scale, _MIN_PIECE_PX * (width_cm / longest))
    h = max(height_cm * scale, _MIN_PIECE_PX * (height_cm / longest))
    return round(w, 1), round(h, 1)


def generate_svg_schematic(pieces: list[dict]) -> str:
    if not pieces:
        return ""

    boxes = []
    x_cursor = _PADDING + _LABEL_SPACE
    max_h = 0
    for piece in pieces:
        w_px, h_px = _scale_dimensions(piece["width_cm"], piece["height_cm"])
        boxes.append({"piece": piece, "w_px": w_px, "h_px": h_px, "x": x_cursor})
        x_cursor += w_px + _GAP
        max_h = max(max_h, h_px)

    total_width = x_cursor - _GAP + _PADDING
    total_height = max_h + _PADDING * 2 + _LABEL_SPACE

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_width:.0f} {total_height:.0f}" '
        f'font-family="system-ui, sans-serif">',
        '<style>'
        '.box{fill:#fbf3ea;stroke:#c1694f;stroke-width:1.5;}'
        '.dim{font-size:11px;fill:#7a6f63;}'
        '.name{font-size:12px;fill:#2c2420;font-weight:600;}'
        '</style>',
    ]

    for b in boxes:
        piece = b["piece"]
        w_px, h_px = b["w_px"], b["h_px"]
        x = b["x"]
        y = _PADDING + (max_h - h_px)  # can day (giong huong gau ao/vay)

        svg_parts.append(f'<rect class="box" x="{x:.1f}" y="{y:.1f}" width="{w_px:.1f}" height="{h_px:.1f}" rx="4" />')

        # ten manh, canh tren
        svg_parts.append(
            f'<text class="name" x="{x + w_px / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle">{piece["name"]}</text>'
        )
        # do rong, duoi day
        svg_parts.append(
            f'<text class="dim" x="{x + w_px / 2:.1f}" y="{y + h_px + 16:.1f}" text-anchor="middle">'
            f'{piece["width_cm"]:g} cm</text>'
        )
        # do cao, canh trai (xoay doc)
        label_x = x - 8
        label_y = y + h_px / 2
        svg_parts.append(
            f'<text class="dim" x="{label_x:.1f}" y="{label_y:.1f}" text-anchor="middle" '
            f'transform="rotate(-90 {label_x:.1f} {label_y:.1f})">{piece["height_cm"]:g} cm</text>'
        )

    svg_parts.append('</svg>')
    return "".join(svg_parts)
