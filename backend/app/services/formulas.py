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
    """Khan than dan theo chieu doc (lengthwise), mui Seed Stitch - dung
    dung ky thuat va cau truc cua pattern "Effortless Scarf" (Patons):
    chain bang chieu DAI khan, dan theo be RONG cho den khi du, moi hang
    xen ke sc/ch-1 tao be mat lam tam hat, ket thuc bang tua rua 2 dau."""
    if not m.scarf_width_cm or not m.scarf_length_cm:
        raise ValueError("Cần nhập scarf_width_cm và scarf_length_cm")

    # Dan lengthwise: chain theo chieu DAI khan, "hang" la be RONG khan.
    chain_stitches = _stitches_for_width(m.scarf_length_cm, m.gauge_stitches_per_10cm)
    if chain_stitches % 2 == 0:
        chain_stitches += 1  # can le de foundation row (sc, ch1-skip-sc lap lai) khep dung
    rows = _rows_for_length(m.scarf_width_cm, m.gauge_rows_per_10cm)

    written = [
        f"[Khăn] Chain {chain_stitches} mũi (bằng chiều dài khăn mong muốn — khăn đan theo chiều dọc).",
        f"Hàng nền (Foundation Row): sc vào mũi thứ 2 tính từ móc. *Ch 1, bỏ 1 mũi, sc vào mũi kế "
        f"tiếp*, lặp lại đến hết hàng. Quay đầu.",
        "Hàng 1: ch 1, sc vào mũi đầu tiên, sc vào khoảng ch-1 kế tiếp. *Ch 1, bỏ qua sc, sc vào "
        "khoảng ch-1 kế tiếp*, lặp lại đến mũi cuối, sc vào mũi cuối. Quay đầu.",
        "Hàng 2: ch 1, sc vào mũi đầu tiên. *Ch 1, bỏ qua sc, sc vào khoảng ch-1 kế tiếp*, lặp lại "
        "đến mũi cuối, ch 1, sc vào mũi cuối. Quay đầu.",
        f"Lặp lại Hàng 1 và Hàng 2 (mẫu Seed Stitch) cho đến khi khăn đạt đủ bề rộng {m.scarf_width_cm}cm "
        f"(khoảng {rows} hàng) rồi cắt chỉ.",
        "Tua rua: cắt sợi thành từng đoạn dài 35cm, gộp 3 sợi thành 1 chùm, gập đôi và móc luồn qua "
        "mép 2 đầu khăn, chia đều khoảng cách. Cắt tỉa tua rua cho gọn.",
    ]
    symbol_rounds = [
        SymbolRound(round_number=1, instruction=f"Seed Stitch (sc + ch1 xen kẽ) x{chain_stitches} mắt chain", stitch_count=chain_stitches)
    ]
    for r in range(2, rows + 1):
        symbol_rounds.append(
            SymbolRound(round_number=r, instruction=f"Seed Stitch x{chain_stitches}", stitch_count=chain_stitches)
        )

    piece = {
        "name": "Khăn than (đan lengthwise, mẫu Seed Stitch + tua rua)",
        "width_cm": m.scarf_width_cm,
        "height_cm": m.scarf_length_cm,
        "written": written,
        "symbol_rounds": symbol_rounds,
        "is_picture_piece": True,
    }
    notes = [
        f"Số mắt chain khởi đầu (= chiều dài khăn): {chain_stitches}.",
        f"Số hàng (= chiều rộng khăn): {rows}.",
        "Mẫu Seed Stitch tham khảo từ pattern \"Effortless Scarf\" (Patons) — bề mặt lấm tấm hạt, "
        "không cuộn mép, không cần đan biên riêng.",
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
        # Ky thuat dung theo pattern "Easy Crochet Baby Bucket Hat" (Bernat):
        # dinh moc tang deu tung 1/6 tong so mui moi vong (giong amigurumi),
        # noi dinh-sang-than bang 1 vong back loop only (tao duong gap nep
        # tu nhien), than moc ca 2 bong chi, vanh bat dau bang 1 vong tang
        # vao front loop only roi xen ke vai vong tang deu / vai vong thang.
        side_height = max(m.hat_height_cm - 4, 4)  # dành ~4cm cuối cho vành loe
        increase_rounds = max(round(total_stitches / 6), 1)
        written = ["Vòng 1: 7 sc vào magic ring (7 mũi)."]
        symbol_rounds = [SymbolRound(round_number=1, instruction="7 sc vào magic ring", stitch_count=7)]
        current = 7
        for rnd in range(2, increase_rounds + 1):
            current = min(current + 7, total_stitches)
            written.append(f"Vòng {rnd}: *2 sc vào 1 mũi, sc đều các mũi còn lại* quanh vòng ({current} mũi).")
            symbol_rounds.append(SymbolRound(round_number=rnd, instruction="tăng đều +7 mũi", stitch_count=current))
        written.append(
            f"Vòng {increase_rounds + 1}: móc vào bọng chỉ sau (back loop only) quanh vòng, sl st đóng vòng "
            "— vòng này tạo đường gấp nếp giữa đỉnh và thân mũ. PM (đặt ghim đánh dấu)."
        )
        symbol_rounds.append(SymbolRound(round_number=increase_rounds + 1, instruction=f"sc back loop only x{total_stitches}", stitch_count=total_stitches))
        last_rnd = increase_rounds + 1

        side_rows = max(_rows_for_length(side_height, m.gauge_rows_per_10cm), 1)
        written.append(
            f"Vòng {last_rnd + 1} - {last_rnd + side_rows}: sc vào cả 2 bọng chỉ (both loops), thẳng không "
            f"tăng, giữ {total_stitches} mũi mỗi vòng cho đến khi thân mũ đạt {side_height}cm."
        )
        for rnd in range(last_rnd + 1, last_rnd + side_rows + 1):
            symbol_rounds.append(SymbolRound(round_number=rnd, instruction=f"sc x{total_stitches} (không tăng)", stitch_count=total_stitches))
        last_rnd = last_rnd + side_rows

        brim_width = m.bucket_brim_width_cm or 5.0
        brim_extra_stitches = _stitches_for_width(brim_width, m.gauge_stitches_per_10cm)
        brim_total = total_stitches + brim_extra_stitches
        brim_increase_rounds = max(round(brim_extra_stitches / (total_stitches / 8 or 1)), 2)

        written.append("-- Bắt đầu móc vành loe (brim) --")
        current = total_stitches
        step = max(round(brim_extra_stitches / brim_increase_rounds), 1)
        first_brim = True
        for i in range(brim_increase_rounds):
            rnd = last_rnd + 1 + i
            current = min(current + step, brim_total)
            loop_note = "vào bọng chỉ trước (front loop only), " if first_brim else ""
            written.append(f"Vòng {rnd}: {loop_note}tăng đều để vành loe ra ({current} mũi).")
            symbol_rounds.append(SymbolRound(round_number=rnd, instruction="tăng đều (vành loe)", stitch_count=current))
            first_brim = False
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
            "Kỹ thuật back loop only (nối đỉnh-thân) và front loop only (bắt đầu vành) tham khảo từ "
            "pattern \"Easy Crochet Baby Bucket Hat\" (Bernat) — tạo đường gấp nếp tự nhiên giữa các "
            "phần thay vì mũ phồng tròn đều.",
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
    """Dai vien ribbing (Neckband/Cuff/Body Edging/Button Band) - dung dung
    ky thuat scbl (single crochet vao bong chi sau) tu pattern ao thuong
    mai that (vd "Simply Perfect Crochet Cardigan"): moc 1 dai hep, hang 1
    la sc thuong, tu hang 2 tro di CHI sc vao bong chi SAU lien tuc - chinh
    nhip lap lai nay tao cac duong gan doc co gian that (khac voi sl st don
    thuan gan nhu khong co do day). Dai vua dan vua dinh vao mep bang
    mattress stitch, khong tinh truoc so hang vi day la ky thuat do truc
    tiep len nguoi/mau khi dan ("fit-as-you-go"), dung nhu tai lieu goc."""
    width_stitches = _stitches_for_width(strip_width_cm, m.gauge_stitches_per_10cm)
    written = [
        f"[{name}] Chain {width_stitches + 1} mũi.",
        f"Hàng 1: (RS). sc vào mũi thứ 2 tính từ móc, sc hết hàng ({width_stitches} mũi).",
        "Hàng 2 trở đi: ch 1, scbl (sc vào bọng chỉ sau — back loop only) mỗi mũi hết hàng, quay đầu.",
        f"Lặp lại hàng 2 đến khi dải đo được (khi hơi kéo giãn nhẹ) vừa {fit_description}.",
        "Vừa đan dải vừa đính vào mép tương ứng bằng mattress stitch (giống kỹ thuật Neckband/"
        "Cuff/Body Edging trong pattern áo thương mại thật).",
    ]
    symbol_rounds = [
        SymbolRound(round_number=1, instruction=f"scbl x{width_stitches} (dải viền, đan đến khi vừa)", stitch_count=width_stitches)
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
        # Ky thuat bam sat pattern "Crochet Ruffle Skirt" (Meladora's
        # Creations): than vay moc bang CLUSTER STITCH (chum 3 mui, moi
        # chum = 3 lan [YO, mov vao 1 mui, keo len, YO keo qua 2 vong] roi
        # keo qua ca 7 vong tren kim, chain 2 giua cac chum; vong sau moc
        # vao dung khoang ch-2 cua vong truoc, khong moc vao than chum).
        # Gau vay chuyen sang DC BAT CHEO CHI VAO BONG CHI SAU (crossover
        # dc, back loop only) - day la ky thuat that tao gon xoe tung lop,
        # KHONG PHAI shell-stitch (5dc cung 1 mui) don gian hoa.
        requested_tiers = m.ruffle_tiers or 1
        total_rows = _rows_for_length(m.skirt_length_cm, m.gauge_rows_per_10cm)
        cluster_count = max(waist_stitches // 3, 3)
        body_rows = max(total_rows - 2, 1)

        written = [
            f"[Váy bèo] Chain {waist_stitches} mũi, sl st nối thành vòng tròn (không xoắn chain). "
            f"Vòng chuẩn bị: sc vào từng mũi quanh vòng."
        ]
        symbol_rounds: list[SymbolRound] = []
        symbol_rounds.append(SymbolRound(round_number=1, instruction=f"sc x{waist_stitches}", stitch_count=waist_stitches))

        written.append(
            f"Vòng 2 (bắt đầu Cluster Stitch): mỗi cụm gồm 3 mũi — *(YO, móc vào mũi, kéo lên, YO, kéo "
            "qua 2 vòng) lặp lại đúng 3 lần liên tiếp vào 3 mũi kế nhau, được 7 vòng trên kim, kéo qua "
            f"cả 7 vòng cùng lúc, ch 2* — lặp lại quanh vòng ({cluster_count} cụm). Sl st vào đỉnh cụm đầu."
        )
        symbol_rounds.append(SymbolRound(round_number=2, instruction=f"Cluster stitch x{cluster_count} cụm", stitch_count=cluster_count))
        for r in range(3, body_rows + 2):
            written.append(
                f"Vòng {r}: lặp lại Cluster Stitch, nhưng móc vào đúng khoảng ch-2 phía trên (không móc "
                f"vào thân cụm của vòng dưới) — tạo lớp gợn phồng chồng lên nhau ({cluster_count} cụm)."
            )
            symbol_rounds.append(SymbolRound(round_number=r, instruction=f"Cluster stitch (vào ch-2) x{cluster_count} cụm", stitch_count=cluster_count))
        last_rnd = body_rows + 1

        written.append("-- Chuyển sang phần gấu (ruffle) bằng dc bắt chéo, back loop only --")
        ruffle_rounds = 3 if requested_tiers <= 1 else min(requested_tiers + 1, 5)
        skip_count = 0
        for i in range(ruffle_rounds):
            rnd = last_rnd + 1 + i
            if i == 0:
                written.append(
                    f"Vòng {rnd} (Round 1 gấu): dc vào bọng chỉ sau (back loop only) của 3 mũi liên tiếp. "
                    "Sau đó dùng bọng chỉ trước (front loops) của chính 3 mũi dc vừa móc, dc bắt chéo lại "
                    "vào từng mũi đó (bắt đầu từ mũi dc đầu tiên). Lặp lại quanh vòng, không bỏ mũi nào."
                )
            else:
                skip_count = 2
                written.append(
                    f"Vòng {rnd}: lặp lại như Round 1 của gấu, nhưng bỏ qua {skip_count} mũi trước khi bắt "
                    "đầu mỗi cụm dc bắt chéo kế tiếp."
                )
            symbol_rounds.append(SymbolRound(round_number=rnd, instruction="dc bắt chéo, back loop only", stitch_count=cluster_count * 3))
        last_rnd = last_rnd + ruffle_rounds
        written.append(
            f"Vòng {last_rnd + 1} (vòng viền cuối gấu, có thể đổi màu): lặp lại Round 1 của gấu — không bỏ "
            "mũi nào — để tạo độ bồng tối đa ở mép ngoài."
        )
        symbol_rounds.append(SymbolRound(round_number=last_rnd + 1, instruction="dc bắt chéo, back loop only (không bỏ mũi)", stitch_count=cluster_count * 3))
        last_rnd += 1

        written.append("-- Phần lưng eo --")
        written.append(
            "Xoay váy lại, móc phần lưng eo: sc gắn vào mép trên, *5 sc rồi giảm 1 mũi (sc2tog)*, lặp lại "
            "quanh vòng, tổng cộng 6 vòng — sau đó luồn dây thun vào bên trong để co giãn ôm vừa vòng eo."
        )
        written.append("Kết thúc: sl st đóng vòng, cắt chỉ, giấu đầu chỉ.")

        hem_width_cm = m.hip_circumference_cm or round(m.waist_circumference_cm * 1.2, 1)
        piece = {
            "name": "Váy bèo (thân cluster stitch + gấu dc bắt chéo back-loop, đan vòng tròn)",
            "width_cm": hem_width_cm,
            "height_cm": m.skirt_length_cm,
            "written": written,
            "symbol_rounds": symbol_rounds,
            "is_picture_piece": True,
        }
        notes = [
            f"Số cụm cluster mỗi vòng thân: {cluster_count}.",
            "Kỹ thuật cluster stitch (thân) và dc bắt chéo back-loop-only (gấu) tham khảo trực tiếp từ "
            "pattern \"Crochet Ruffle Skirt\" (Meladora's Creations) — không phải shell-stitch đơn giản hóa.",
        ]
        if requested_tiers > 1:
            notes.append(
                f"Bạn chọn {requested_tiers} tầng bèo — đã tăng số vòng dc bắt chéo ở phần gấu tương ứng "
                "(mỗi vòng thêm là 1 lớp bèo xếp chồng lên vòng trước)."
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
    "scbl": "single crochet vào bọng chỉ sau (single crochet in back loop only)",
    "sl st": "slip stitch (mũi trượt)",
    "rnd": "round (vòng)",
    "st(s)": "stitch(es) (mũi)",
}

# Ước lượng trung bình cm sợi tiêu hao cho 1 mũi - dựa theo kinh nghiệm chung
# giữa sc/hdc/dc (không chính xác tuyệt đối vì phụ thuộc loại sợi/độ chặt tay
# đan, nhưng đủ để người dùng ước lượng số sợi cần mua).
_AVG_CM_PER_STITCH = 3.5

# Bang quy doi gauge (so mui / 10cm) -> co kim va do sui len tuong ung -
# tong hop tu bang gauge chuan cua Craft Yarn Council (giong bang gauge in
# tren vo cuon len that), dung de LUON dua ra 1 goi y kim cu the thay vi
# noi "khong the xac dinh truoc".
_HOOK_GAUGE_TABLE = [
    (28, "2.25mm (US B/1)", "sợi lace / fingering mảnh"),
    (24, "3mm (US C/2 - D/3)", "sợi fingering / sport"),
    (20, "4mm (US G/6)", "sợi sport / DK"),
    (16, "5mm (US H/8)", "sợi DK / worsted"),
    (13, "5.5mm (US I/9)", "sợi worsted / aran"),
    (10, "6.5mm (US K/10.5)", "sợi aran / bulky"),
    (7, "9mm (US M/13)", "sợi bulky / super bulky"),
    (0, "10mm (US N/15) trở lên", "sợi super bulky / jumbo"),
]


def _suggest_hook(gauge_stitches_per_10cm: float) -> tuple[str, str]:
    for threshold, hook, yarn_weight in _HOOK_GAUGE_TABLE:
        if gauge_stitches_per_10cm >= threshold:
            return hook, yarn_weight
    return _HOOK_GAUGE_TABLE[-1][1], _HOOK_GAUGE_TABLE[-1][2]


def estimate_materials(pieces: list[Piece], gauge_stitches_per_10cm: float, gauge_rows_per_10cm: float) -> list[str]:
    """Sinh mục MATERIALS giống các pattern crochet thương mại: ước lượng
    tổng mét sợi cần và gợi ý cỡ kim cụ thể theo đúng bảng gauge chuẩn
    (Craft Yarn Council), thay vì chỉ nói chung chung không xác định được."""
    total_stitches = sum(r.stitch_count for p in pieces for r in p.get("symbol_rounds", []))
    total_length_m = max(round(total_stitches * _AVG_CM_PER_STITCH / 100), 1)
    hook_size, yarn_weight = _suggest_hook(gauge_stitches_per_10cm)

    return [
        f"Sợi: ước lượng cần khoảng {total_length_m}m (dựa trên tổng {total_stitches} mũi, "
        f"mức tiêu hao trung bình ~{_AVG_CM_PER_STITCH}cm/mũi) — nên mua dư thêm 10-15% để phòng "
        "hao hụt khi ghép nối và sửa lỗi.",
        f"Kim móc: {hook_size} — cỡ kim phù hợp nhất với gauge bạn nhập "
        f"({gauge_stitches_per_10cm:g} mũi / 10cm), thường dùng với {yarn_weight}. Nếu đan mẫu thử ra "
        "gauge khác, đổi sang kim to hơn 1 cỡ (đan lỏng hơn) hoặc nhỏ hơn 1 cỡ (đan chặt hơn).",
        "Kim khâu len (để ghép nối các mảnh), kéo cắt chỉ, ghim đánh dấu (stitch markers).",
    ]
