"""Công thức móc len chuẩn hóa theo từng loại sản phẩm + subtype.

Công thức dựa trên nguyên tắc crochet phổ biến (tăng/giảm mũi theo cấp số,
gauge-based sizing). Các sản phẩm cần may/ghép nhiều mảnh (áo, váy bèo) được
trả về dạng danh sách "pieces" riêng biệt, kèm hướng dẫn ghép nối cuối cùng -
giống cách các pattern crochet thực tế trình bày (thân trước/sau móc riêng,
tay áo móc riêng, rồi khâu lại).

Loại mũi dùng cho từng sản phẩm THAM KHẢO từ các pattern thương mại thật
(không phải chỉ dùng mỗi sc cho mọi thứ):
- Khăn: sc (giống "Effortless Scarf").
- Mũ (beanie/bucket): sc, móc vòng tròn kiểu amigurumi (giống "Easy Crochet
  Baby Bucket Hat").
- Áo (sweater/cardigan): hdc - thân/tay áo thật hầu như không dùng sc thuần
  vì quá dày/chậm cho cả bộ áo (giống "Getting Cozy Crochet Pullover" dùng
  hdc làm mũi chính).
- Váy: dc - vải rủ hơn, lên hàng nhanh hơn (giống pattern "mini skirt"/
  "ruffle skirt" đều dùng dc cho thân váy).
"""
from __future__ import annotations

from app.schemas.pattern import Measurements, SymbolRound

Piece = dict  # {"name", "width_cm", "height_cm", "written", "symbol_rounds"}

# Thong tin ky thuat theo tung loai mui - dung de sinh dung huong dan chain/
# turning chain cho tung loai (sc/hdc/dc khac nhau ve so ch bo sung va vi tri
# bat dau tinh tu moc).
_STITCH_INFO = {
    "sc": {"chain_extra": 1, "start_from_hook": 2, "turn_instruction": "ch 1, quay đầu"},
    "hdc": {"chain_extra": 2, "start_from_hook": 3, "turn_instruction": "ch 2 (tính là mũi hdc đầu), quay đầu"},
    "dc": {"chain_extra": 3, "start_from_hook": 4, "turn_instruction": "ch 3 (tính là mũi dc đầu), quay đầu"},
}


def _stitches_for_width(width_cm: float, gauge_stitches_per_10cm: float) -> int:
    return max(round(width_cm / 10 * gauge_stitches_per_10cm), 1)


def _rows_for_length(length_cm: float, gauge_rows_per_10cm: float) -> int:
    return max(round(length_cm / 10 * gauge_rows_per_10cm), 1)


def _flat_rectangle_piece(
    name: str,
    width_cm: float,
    height_cm: float,
    m: Measurements,
    is_picture_piece: bool = True,
    stitch: str = "sc",
) -> Piece:
    """Mảnh hình chữ nhật móc bẹt qua lại (dùng cho thân áo, khăn)."""
    info = _STITCH_INFO[stitch]
    stitches = _stitches_for_width(width_cm, m.gauge_stitches_per_10cm)
    rows = _rows_for_length(height_cm, m.gauge_rows_per_10cm)

    written = [
        f"[{name}] Chain {stitches + info['chain_extra']} mũi.",
        f"Hàng 1: {stitch} vào mũi thứ {info['start_from_hook']} tính từ móc, "
        f"{stitch} hết hàng ({stitches} mũi).",
        f"Hàng 2 - {rows}: {info['turn_instruction']}, {stitch} hết hàng ({stitches} mũi).",
        f"Móc đến khi đủ {rows} hàng (khoảng {height_cm}cm) rồi cắt chỉ.",
    ]
    if not is_picture_piece:
        written.append("Mảnh này móc màu trơn, đồng bộ theo màu chủ đạo của thiết kế (xem pixel chart để biết màu).")
    symbol_rounds = [SymbolRound(round_number=1, instruction=f"{stitch} x{stitches}", stitch_count=stitches)]
    for r in range(2, rows + 1):
        symbol_rounds.append(
            SymbolRound(round_number=r, instruction=f"{stitch} x{stitches}", stitch_count=stitches)
        )
    return {
        "name": name,
        "width_cm": width_cm,
        "height_cm": height_cm,
        "written": written,
        "symbol_rounds": symbol_rounds,
        "is_picture_piece": is_picture_piece,
    }


# ---------------------------------------------------------------- KHĂN ----

def generate_khan(m: Measurements, subtype: str | None) -> tuple[list[Piece], list[str], list[str]]:
    if not m.scarf_width_cm or not m.scarf_length_cm:
        raise ValueError("Cần nhập scarf_width_cm và scarf_length_cm")

    piece = _flat_rectangle_piece("Khăn", m.scarf_width_cm, m.scarf_length_cm, m, stitch="sc")
    notes = [
        f"Tổng số mũi mỗi hàng: {_stitches_for_width(m.scarf_width_cm, m.gauge_stitches_per_10cm)}.",
        f"Tổng số hàng: {_rows_for_length(m.scarf_length_cm, m.gauge_rows_per_10cm)}.",
    ]
    return [piece], [], notes


# ------------------------------------------------------------------ MŨ ----

def _hat_crown_and_side(m: Measurements, total_stitches: int, straight_height_cm: float) -> tuple[list[str], list[SymbolRound], int]:
    increase_rounds = max(round(total_stitches / 6), 1)
    written = ["Vòng 1: 6 sc vào magic ring (6 mũi)."]
    symbol_rounds = [SymbolRound(round_number=1, instruction="6 sc vào magic ring", stitch_count=6)]

    current = 6
    for rnd in range(2, increase_rounds + 1):
        current = min(current + 6, total_stitches)
        written.append(f"Vòng {rnd}: tăng đều, tăng 6 mũi ({current} mũi).")
        symbol_rounds.append(SymbolRound(round_number=rnd, instruction="tăng đều +6 mũi", stitch_count=current))

    rows_for_height = _rows_for_length(straight_height_cm, m.gauge_rows_per_10cm)
    straight_rounds = max(rows_for_height, 1)
    start_rnd = increase_rounds + 1
    written.append(
        f"Vòng {start_rnd} - {start_rnd + straight_rounds - 1}: sc thẳng không tăng, "
        f"giữ {total_stitches} mũi mỗi vòng."
    )
    for rnd in range(start_rnd, start_rnd + straight_rounds):
        symbol_rounds.append(
            SymbolRound(round_number=rnd, instruction=f"sc x{total_stitches} (không tăng)", stitch_count=total_stitches)
        )
    last_round = start_rnd + straight_rounds - 1
    return written, symbol_rounds, last_round


def generate_mu(m: Measurements, subtype: str | None) -> tuple[list[Piece], list[str], list[str]]:
    if not m.head_circumference_cm or not m.hat_height_cm:
        raise ValueError("Cần nhập head_circumference_cm và hat_height_cm")

    subtype = subtype or "beanie"
    stitches_per_cm = m.gauge_stitches_per_10cm / 10
    total_stitches = max(round(m.head_circumference_cm * stitches_per_cm), 6)

    if subtype == "beanie":
        written, symbol_rounds, last_rnd = _hat_crown_and_side(m, total_stitches, m.hat_height_cm)
        written.append("Kết thúc: sl st đóng vòng, cắt chỉ, giấu đầu chỉ. (Có thể gập viền mép làm bâm.)")
        piece = {
            "name": "Mũ beanie (móc vòng tròn liên tục)",
            "width_cm": m.head_circumference_cm,
            "height_cm": m.hat_height_cm,
            "written": written,
            "symbol_rounds": symbol_rounds,
            "is_picture_piece": True,
        }
        notes = [f"Tổng số mũi mỗi vòng: {total_stitches}."]
        return [piece], [], notes

    if subtype == "bucket":
        side_height = max(m.hat_height_cm - 4, 4)  # dành ~4cm cuối cho vành loe
        written, symbol_rounds, last_rnd = _hat_crown_and_side(m, total_stitches, side_height)

        brim_width = m.bucket_brim_width_cm or 5.0
        brim_extra_stitches = _stitches_for_width(brim_width, m.gauge_stitches_per_10cm)
        brim_total = total_stitches + brim_extra_stitches
        brim_increase_rounds = max(round(brim_extra_stitches / (total_stitches / 8 or 1)), 2)

        written.append("-- Bắt đầu móc vành loe (brim) --")
        current = total_stitches
        step = max(round(brim_extra_stitches / brim_increase_rounds), 1)
        for i in range(brim_increase_rounds):
            rnd = last_rnd + 1 + i
            current = min(current + step, brim_total)
            written.append(f"Vòng {rnd}: tăng đều để vành loe ra ({current} mũi).")
            symbol_rounds.append(SymbolRound(round_number=rnd, instruction="tăng đều (vành loe)", stitch_count=current))
        written.append("Kết thúc: sl st đóng vòng, cắt chỉ, giấu đầu chỉ.")

        piece = {
            "name": "Mũ bucket hat (đỉnh + thân + vành loe, móc vòng tròn liên tục)",
            "width_cm": m.head_circumference_cm + brim_width,
            "height_cm": m.hat_height_cm,
            "written": written,
            "symbol_rounds": symbol_rounds,
            "is_picture_piece": True,
        }
        notes = [
            f"Tổng số mũi thân mũ: {total_stitches}, sau khi loe vành: {brim_total}.",
            "Vành bucket hat có thể cần hồ cứng (interfacing) để đứng form khi đội thực tế.",
        ]
        return [piece], [], notes

    raise ValueError("subtype cho mũ phải là 'beanie' hoặc 'bucket'")


# ------------------------------------------------------------------ ÁO ----

def _sleeve_piece(name: str, m: Measurements, stitch: str = "hdc") -> Piece:
    info = _STITCH_INFO[stitch]
    sleeve_width = m.sleeve_width_cm or round((m.chest_circumference_cm or 90) * 0.32, 1)
    wrist_width = round(sleeve_width * 0.6, 1)
    rows = _rows_for_length(m.sleeve_length_cm, m.gauge_rows_per_10cm)
    start_st = _stitches_for_width(wrist_width, m.gauge_stitches_per_10cm)
    end_st = _stitches_for_width(sleeve_width, m.gauge_stitches_per_10cm)
    increase_every = max(round(rows / max(end_st - start_st, 1)), 1)

    written = [
        f"[{name}] Chain {start_st + info['chain_extra']} mũi (cổ tay áo).",
        f"Hàng 1: {stitch} vào mũi thứ {info['start_from_hook']} tính từ móc, "
        f"{stitch} hết hàng ({start_st} mũi).",
        f"Hàng 2 - {rows}: {info['turn_instruction']}, {stitch} hết hàng; cứ mỗi {increase_every} hàng thì "
        f"tăng 1 mũi mỗi đầu hàng cho đến khi đạt {end_st} mũi (vòng bắp tay/nách).",
        f"Móc thẳng đến khi đủ {m.sleeve_length_cm}cm rồi cắt chỉ.",
    ]
    symbol_rounds = [SymbolRound(round_number=1, instruction=f"{stitch} x{start_st}", stitch_count=start_st)]
    current = start_st
    for r in range(2, rows + 1):
        if (r - 1) % increase_every == 0 and current < end_st:
            current += 1
        symbol_rounds.append(SymbolRound(round_number=r, instruction=f"{stitch} x{current}", stitch_count=current))

    return {
        "name": name,
        "width_cm": sleeve_width,
        "height_cm": m.sleeve_length_cm,
        "width_stitches": start_st,
        "written": written,
        "symbol_rounds": symbol_rounds,
        "is_picture_piece": True,
    }


def _sl_st_ribbing_strip(name: str, fit_description: str, m: Measurements, strip_width_cm: float = 2.5) -> Piece:
    """Dai vien sl-st ribbing (Neckband/Cuff/Body Edging) - dung dung ky
    thuat tu pattern ao thuong mai that (Cerulean Cabled Crochet Sweater):
    moc 1 dai hep bang sl st vao bong chi sau (back loop only), moc dai dan
    ra theo do vua thuc te ("do khi hoi keo gian nhe vua voi mep can dinh"),
    vua dan vua dinh vao mep bang mattress stitch - khong tinh truoc so hang
    vi day la ky thuat "fit-as-you-go", dung nhu tai lieu goc trinh bay."""
    width_stitches = _stitches_for_width(strip_width_cm, m.gauge_stitches_per_10cm)
    written = [
        f"[{name}] Chain {width_stitches + 1} mũi.",
        f"Hàng 1: (RS). sl st vào mũi thứ 2 tính từ móc, sl st hết hàng ({width_stitches} mũi).",
        "Hàng 2 trở đi: ch 1, sl st vào bọng chỉ sau (back loop only) của mỗi mũi hết hàng, quay đầu.",
        f"Lặp lại hàng 2 đến khi dải đo được (khi hơi kéo giãn nhẹ) vừa {fit_description}.",
        "Vừa đan dải vừa đính vào mép tương ứng bằng mattress stitch (giống kỹ thuật Neckband/"
        "Cuff/Body Edging trong pattern áo thương mại thật).",
    ]
    symbol_rounds = [
        SymbolRound(round_number=1, instruction=f"sl st x{width_stitches} (dải viền, đan đến khi vừa)", stitch_count=width_stitches)
    ]
    return {
        "name": name,
        "width_cm": strip_width_cm,
        "height_cm": 3.0,
        "written": written,
        "symbol_rounds": symbol_rounds,
        "is_picture_piece": False,
    }


def generate_ao(m: Measurements, subtype: str | None) -> tuple[list[Piece], list[str], list[str]]:
    required = (m.chest_circumference_cm, m.body_length_cm, m.sleeve_length_cm)
    if not all(required):
        raise ValueError("Cần nhập chest_circumference_cm, body_length_cm, sleeve_length_cm")

    subtype = subtype or "sweater"
    half_chest = round(m.chest_circumference_cm / 2, 1)
    AO_STITCH = "hdc"  # than/tay ao dung hdc, giong pattern ao crochet thuong mai that

    if subtype == "sweater":
        than_truoc = _flat_rectangle_piece("Thân trước", half_chest, m.body_length_cm, m, is_picture_piece=True, stitch=AO_STITCH)
        than_sau = _flat_rectangle_piece("Thân sau", half_chest, m.body_length_cm, m, is_picture_piece=False, stitch=AO_STITCH)
        tay_trai = _sleeve_piece("Tay áo trái", m, stitch=AO_STITCH)
        tay_phai = _sleeve_piece("Tay áo phải", m, stitch=AO_STITCH)
        neckband = _sl_st_ribbing_strip("Neckband (viền cổ)", "quanh mép cổ áo", m)
        cuff_trai = _sl_st_ribbing_strip("Cuff tay trái (viền cổ tay)", "quanh gấu tay áo trái", m)
        cuff_phai = _sl_st_ribbing_strip("Cuff tay phải (viền cổ tay)", "quanh gấu tay áo phải", m)
        body_edging = _sl_st_ribbing_strip("Body Edging (viền gấu áo)", "quanh gấu thân áo", m)
        pieces = [than_truoc, than_sau, tay_trai, tay_phai, neckband, cuff_trai, cuff_phai, body_edging]

        assembly = [
            "1. Đặt thân trước và thân sau úp mặt phải vào nhau, khâu/móc slip stitch nối 2 đường vai (mỗi bên ~10-12cm tính từ viền cổ).",
            "2. Khâu/móc slip stitch nối 2 đường sườn thân (từ gấu áo lên đến vòng nách, chừa sao chân vòng nách lại).",
            "3. Gập đôi tay áo, khâu/móc nối đường sống tay áo thành hình ống.",
            "4. Gắn miếng tay áo vào vòng nách của thân áo, móc sc/slip stitch cố định vòng quanh.",
            "5. Móc Neckband (dải sl-st ribbing) vừa đan vừa đính quanh mép cổ áo bằng mattress stitch.",
            "6. Móc Cuff trái/phải vừa đan vừa đính quanh gấu mỗi tay áo bằng mattress stitch.",
            "7. Móc Body Edging vừa đan vừa đính quanh gấu thân áo bằng mattress stitch.",
        ]
        notes = [
            f"Thân trước/sau mỗi mảnh rộng {half_chest}cm (bằng 1/2 vòng ngực). Dùng mũi hdc (half double "
            "crochet) làm mũi chính, giống các pattern áo crochet thương mại thật (sc thuần quá dày/chậm "
            "cho cả bộ áo).",
            "Neckband/Cuff/Body Edging dùng đúng kỹ thuật sl-st ribbing (đan dải hẹp, sl st vào bọng chỉ "
            "sau, đan-đến-khi-vừa) tham khảo từ pattern áo thương mại thật, không tính trước số hàng vì "
            "đây là kỹ thuật đo trực tiếp lên người/mẫu khi đan.",
            "Đây là công thức đơn giản hóa (beta), chưa tính chi tiết dáng xéo vai/vòng nách cong - "
            "phù hợp áo form rộng, chưa tối ưu cho áo form ôm.",
        ]
        return pieces, assembly, notes

    if subtype == "cardigan":
        quarter_chest = round(m.chest_circumference_cm / 4, 1)
        than_truoc_trai = _flat_rectangle_piece("Thân trước trái", quarter_chest, m.body_length_cm, m, is_picture_piece=True, stitch=AO_STITCH)
        than_truoc_phai = _flat_rectangle_piece("Thân trước phải", quarter_chest, m.body_length_cm, m, is_picture_piece=True, stitch=AO_STITCH)
        than_sau = _flat_rectangle_piece("Thân sau", half_chest, m.body_length_cm, m, is_picture_piece=False, stitch=AO_STITCH)
        tay_trai = _sleeve_piece("Tay áo trái", m, stitch=AO_STITCH)
        tay_phai = _sleeve_piece("Tay áo phải", m, stitch=AO_STITCH)
        neckband = _sl_st_ribbing_strip("Neckband (viền cổ)", "quanh mép cổ áo", m)
        cuff_trai = _sl_st_ribbing_strip("Cuff tay trái (viền cổ tay)", "quanh gấu tay áo trái", m)
        cuff_phai = _sl_st_ribbing_strip("Cuff tay phải (viền cổ tay)", "quanh gấu tay áo phải", m)
        body_edging = _sl_st_ribbing_strip("Body Edging (viền gấu áo)", "quanh gấu thân áo", m)
        front_band = _sl_st_ribbing_strip("Nẹp cài nút (Button Band)", "dọc 2 mép thân trước trái và phải cộng lại", m)
        pieces = [than_truoc_trai, than_truoc_phai, than_sau, tay_trai, tay_phai, neckband, cuff_trai, cuff_phai, body_edging, front_band]

        assembly = [
            "1. Khâu/móc nối vai: thân trước trái + thân sau, thân trước phải + thân sau (mỗi bên ~10-12cm từ viền cổ).",
            "2. Khâu/móc nối 2 đường sườn thân (thân trước trái với thân sau, thân trước phải với thân sau).",
            "3. Gập đôi từng tay áo, nối đường sống tay thành hình ống, rồi gắn vào vòng nách.",
            "4. Móc Neckband vừa đan vừa đính quanh mép cổ áo bằng mattress stitch.",
            "5. Móc Cuff trái/phải vừa đan vừa đính quanh gấu mỗi tay áo bằng mattress stitch.",
            "6. Móc Body Edging vừa đan vừa đính quanh gấu thân áo bằng mattress stitch.",
            "7. Móc Nẹp cài nút (Button Band) vừa đan vừa đính dọc 2 mép trước; đính khuyết/nút hoặc khóa theo ý thích.",
        ]
        notes = [
            f"Mỗi mảnh thân trước rộng {quarter_chest}cm (1/4 vòng ngực), thân sau rộng {half_chest}cm. "
            "Dùng mũi hdc làm mũi chính, giống pattern áo khoác crochet thương mại thật.",
            "Đây là công thức đơn giản hóa (beta) cho form áo khoác rộng; chưa tính độ chênh nút/khuyết.",
        ]
        return pieces, assembly, notes

    raise ValueError("subtype cho áo phải là 'sweater' hoặc 'cardigan'")


# ----------------------------------------------------------------- VÁY ----

def generate_vay(m: Measurements, subtype: str | None) -> tuple[list[Piece], list[str], list[str]]:
    required = (m.waist_circumference_cm, m.skirt_length_cm)
    if not all(required):
        raise ValueError("Cần nhập waist_circumference_cm và skirt_length_cm")

    subtype = subtype or "don"
    stitches_per_cm = m.gauge_stitches_per_10cm / 10
    waist_stitches = max(round(m.waist_circumference_cm * stitches_per_cm), 4)

    if subtype == "don":
        # Dung mui dc (double crochet) cho than vay - vai ru hon, len hang
        # nhanh hon sc, giong cac pattern vay crochet thuc te (mini skirt,
        # ruffle skirt).
        hip_cm = m.hip_circumference_cm or round(m.waist_circumference_cm * 1.15, 1)
        hip_stitches = max(round(hip_cm * stitches_per_cm), waist_stitches)
        total_rows = _rows_for_length(m.skirt_length_cm, m.gauge_rows_per_10cm)
        increase_rows = max(round(total_rows * 0.3), 1)

        written = [
            f"[Váy đơn] Chain {waist_stitches} mũi, nối vòng (không xoắn).",
            f"Vòng 1 - {increase_rows}: ch 3 (tính là mũi dc đầu), tăng đều mỗi vòng bằng dc cho đến khi "
            f"đạt {hip_stitches} mũi (vòng hông).",
            f"Vòng {increase_rows + 1} - {total_rows}: ch 3, dc thẳng không tăng, giữ {hip_stitches} mũi "
            f"mỗi vòng cho đến khi đủ {m.skirt_length_cm}cm.",
            "Viền eo: móc 1-2 hàng sc chần hoặc để khoảng luồn thun (elastic) ở vòng eo.",
            "Kết thúc: sl st đóng vòng, cắt chỉ, giấu đầu chỉ.",
        ]
        symbol_rounds = []
        current = waist_stitches
        step = max(round((hip_stitches - waist_stitches) / max(increase_rows, 1)), 0)
        for r in range(1, total_rows + 1):
            if r <= increase_rows and current < hip_stitches:
                current = min(current + step, hip_stitches)
            symbol_rounds.append(SymbolRound(round_number=r, instruction=f"dc x{current}", stitch_count=current))

        piece = {
            "name": "Váy đơn (móc vòng tròn từ eo xuống, mũi dc)",
            "width_cm": hip_cm,
            "height_cm": m.skirt_length_cm,
            "written": written,
            "symbol_rounds": symbol_rounds,
            "is_picture_piece": True,
        }
        notes = [f"Số mũi eo: {waist_stitches}, số mũi hông: {hip_stitches}."]
        return [piece], [], notes

    if subtype == "beo":
        # Kỹ thuật bèo THẬT, tham khảo từ pattern váy ruffle thực tế: móc thân
        # váy thẳng (dc rounds), rồi CHỈ 1 vòng bèo duy nhất ở gấu bằng cách
        # lặp *5 dc vào cùng 1 mũi, 1 dc vào mũi kế tiếp* quanh vòng. Lưu ý:
        # kỹ thuật này làm số mũi tăng gấp ~3 lần chỉ trong 1 vòng - áp dụng
        # nhiều lần liên tiếp (nhiều "tầng") sẽ khiến số mũi nổ ra phi thực tế
        # (hàng nghìn mũi/vòng), nên CHỈ áp dụng 1 lần duy nhất ở gấu, đúng
        # như tài liệu tham khảo, thay vì bịa thêm nhiều tầng chồng lên nhau.
        requested_tiers = m.ruffle_tiers or 1
        total_rows = _rows_for_length(m.skirt_length_cm, m.gauge_rows_per_10cm)
        body_rows = max(total_rows - 1, 1)

        written = [f"[Váy bèo] Chain {waist_stitches} mũi, nối vòng (không xoắn)."]
        symbol_rounds: list[SymbolRound] = []
        for r in range(1, body_rows + 1):
            written.append(f"Vòng {r}: ch 2, 1 dc trong mỗi mũi quanh vòng, ss đóng vòng. ({waist_stitches} mũi)")
            symbol_rounds.append(
                SymbolRound(round_number=r, instruction=f"dc x{waist_stitches}", stitch_count=waist_stitches)
            )

        repeats = max(waist_stitches // 2, 1)
        ruffle_stitches = repeats * 6
        ruffle_rnd = body_rows + 1
        written.append(
            f"Vòng {ruffle_rnd} (vòng bèo ở gấu): ch 2. Lặp lại quanh vòng: *5 dc vào cùng 1 mũi, "
            f"1 dc vào mũi kế tiếp*. ({ruffle_stitches} mũi)"
        )
        symbol_rounds.append(
            SymbolRound(
                round_number=ruffle_rnd,
                instruction=f"*5dc cùng 1 mũi, 1dc* x{repeats} lần",
                stitch_count=ruffle_stitches,
            )
        )
        written.append("Kết thúc: sl st đóng vòng, cắt chỉ, giấu đầu chỉ.")

        piece = {
            "name": "Váy bèo (thân thẳng + 1 vòng bèo ở gấu, kỹ thuật shell-stitch)",
            "width_cm": round(ruffle_stitches / stitches_per_cm, 1),
            "height_cm": m.skirt_length_cm,
            "written": written,
            "symbol_rounds": symbol_rounds,
            "is_picture_piece": True,
        }
        notes = [
            "Kỹ thuật bèo: *5 dc vào cùng 1 mũi, 1 dc vào mũi kế tiếp* - shell-stitch chuẩn "
            "(tham khảo từ pattern váy ruffle thực tế), làm số mũi tăng gấp ~3 lần ngay trong 1 vòng.",
        ]
        if requested_tiers > 1:
            notes.append(
                f"Bạn chọn {requested_tiers} tầng bèo, nhưng tài liệu tham khảo chỉ mô tả 1 vòng bèo "
                "duy nhất ở gấu váy (áp dụng nhiều vòng bèo liên tiếp sẽ làm số mũi tăng phi thực tế, "
                "hàng nghìn mũi/vòng). Đang áp dụng 1 vòng bèo ở gấu - để có nhiều tầng bèo xếp chồng "
                "thật (kiểu flamenco), cần thiết kế riêng từng tầng như váy may ghép, không nằm trong "
                "tài liệu tham khảo hiện có."
            )
        return [piece], [], notes

    raise ValueError("subtype cho váy phải là 'don' hoặc 'beo'")


GENERATORS = {
    "khan": generate_khan,
    "mu": generate_mu,
    "ao": generate_ao,
    "vay": generate_vay,
}

# Chỉ liệt kê các ký hiệu THẬT SỰ được dùng trong công thức sinh ra ở trên -
# giống mục ABBREVIATIONS trong các pattern crochet chuyên nghiệp.
ABBREVIATIONS = {
    "ch": "chain (bắt mũi)",
    "sc": "single crochet (mũi đơn)",
    "hdc": "half double crochet (mũi nửa kép)",
    "dc": "double crochet (mũi kép)",
    "sl st": "slip stitch (mũi trượt)",
    "rnd": "round (vòng)",
    "st(s)": "stitch(es) (mũi)",
}

# Ước lượng trung bình cm sợi tiêu hao cho 1 mũi - dựa theo kinh nghiệm chung
# giữa sc/hdc/dc (không chính xác tuyệt đối vì phụ thuộc loại sợi/độ chặt tay
# đan, nhưng đủ để người dùng ước lượng số sợi cần mua).
_AVG_CM_PER_STITCH = 3.5


def estimate_materials(pieces: list[Piece], gauge_stitches_per_10cm: float, gauge_rows_per_10cm: float) -> list[str]:
    """Sinh mục MATERIALS giống các pattern crochet thương mại (tên mục,
    không phải nội dung chính xác vì không biết loại sợi cụ thể người dùng
    sẽ dùng - chỉ ước lượng tổng mét sợi cần và nhắc kim/dụng cụ cần có)."""
    total_stitches = sum(r.stitch_count for p in pieces for r in p.get("symbol_rounds", []))
    total_length_m = max(round(total_stitches * _AVG_CM_PER_STITCH / 100), 1)

    return [
        f"Sợi: ước lượng cần khoảng {total_length_m}m (dựa trên tổng {total_stitches} mũi, "
        f"mức tiêu hao trung bình ~{_AVG_CM_PER_STITCH}cm/mũi) - CHỈ MANG TÍNH THAM KHẢO, "
        "nên mua dư thêm 10-15% vì còn phụ thuộc loại sợi và độ chặt tay đan của bạn.",
        f"Kim móc: chọn cỡ kim phù hợp để đạt đúng gauge đã nhập "
        f"({gauge_stitches_per_10cm:g} mũi và {gauge_rows_per_10cm:g} hàng / 10cm) - "
        "không thể nói trước số mm chính xác nếu chưa biết loại sợi cụ thể, vì gauge phụ "
        "thuộc cả sợi lẫn kim, nên đan thử mẫu trước để chọn đúng cỡ kim.",
        "Kim khâu len (để ghép nối các mảnh), kéo cắt chỉ.",
    ]
