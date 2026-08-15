import json
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas.pattern import (
    SUBTYPES_BY_GARMENT,
    ClassifyResult,
    GenerateResponse,
    Measurements,
    PatternPiece,
    PixelChart,
    SymbolChart,
)
from app.services import ai_classifier, color_chart, formulas, garment_regions, image_io, schematic

router = APIRouter(prefix="/api", tags=["pattern"])


@router.post("/classify", response_model=ClassifyResult)
async def classify(image: UploadFile = File(...)) -> ClassifyResult:
    content = await image.read()
    try:
        garment_type, confidence, diagnostics = ai_classifier.classify_garment_ai(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ClassifyResult(garment_type=garment_type, confidence=confidence, diagnostics=diagnostics)


def _region_key_for_piece(name: str) -> Optional[str]:
    """Ánh xạ tên mảnh -> vùng thực tế đã phân tích được trên ảnh (chỉ áp
    dụng cho áo, nơi ảnh chụp thường thấy rõ thân + 2 tay). Thân trước trái/
    phải (cardigan) dùng 2 nửa riêng của vùng thân (không dùng chung 1 ảnh).
    Thân sau chỉ có vùng riêng nếu người dùng upload thêm ảnh mặt sau."""
    if name == "Thân trước trái":
        return "body_left"
    if name == "Thân trước phải":
        return "body_right"
    if "Thân trước" in name:
        return "body"
    if name == "Tay áo trái":
        return "sleeve_left"
    if name == "Tay áo phải":
        return "sleeve_right"
    if name == "Thân sau":
        return "back"
    return None


def _split_left_right(image_array):
    """Chia đôi 1 vùng ảnh theo chiều ngang - dùng cho áo cardigan có 2 nửa
    thân trước riêng biệt, tránh việc cả 2 mảnh dùng chung 1 ảnh giống hệt nhau."""
    w = image_array.shape[1]
    mid = w // 2
    return image_array[:, :mid], image_array[:, mid:]


def _inject_color_bands(raw: dict, source_array) -> None:
    """Đổi màu THẬT theo từng dải hàng trong ảnh vào symbol chart - giống kỹ
    thuật đổi màu theo hàng trong graphgan/C2C. Tất định: cùng 1 ảnh (cùng
    source_array) luôn cho ra cùng kết quả vì KMeans dùng random_state cố
    định; ảnh khác sẽ cho màu/vị trí đổi màu khác vì nội dung ảnh khác nhau."""
    symbol_rounds = raw["symbol_rounds"]
    rows = len(symbol_rounds)
    if rows == 0:
        return

    bands = color_chart.color_bands_by_row(source_array, rows)
    segments = color_chart.run_length_encode(bands)

    if len(segments) <= 1:
        # Chỉ 1 màu duy nhất sau khi snap - vẫn báo rõ cho người dùng biết
        # (thay vì im lặng không hiện gì, dễ hiểu nhầm là lỗi/hỏng).
        only_hex = segments[0][2] if segments else "#000000"
        raw["written"].append(
            f"Màu phát hiện từ ảnh: 1 màu duy nhất ({only_hex}) - móc màu này xuyên suốt, không cần đổi màu."
        )
        return

    color_lines = []
    for start, _end, hex_color in segments:
        round_no = symbol_rounds[start].round_number
        symbol_rounds[start].instruction = f"{symbol_rounds[start].instruction} — đổi màu {hex_color}"
        color_lines.append(f"Vòng/Hàng {round_no}: đổi sang màu {hex_color}.")

    raw["written"].append(
        f"Đổi màu theo {len(segments)} khối màu trích xuất thật từ ảnh (tất định - cùng ảnh sẽ "
        "luôn ra cùng kết quả này):"
    )
    raw["written"].extend(color_lines)


@router.post("/generate", response_model=GenerateResponse)
async def generate(
    garment_type: str = Form(...),
    chart_type: str = Form(...),
    measurements: str = Form(..., description="JSON string của Measurements"),
    subtype: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    back_image: Optional[UploadFile] = File(None),
) -> GenerateResponse:
    try:
        measurements_obj = Measurements(**json.loads(measurements))
    except (json.JSONDecodeError, TypeError) as exc:
        raise HTTPException(status_code=400, detail="measurements không hợp lệ") from exc

    if garment_type not in formulas.GENERATORS:
        raise HTTPException(status_code=400, detail="garment_type không hợp lệ")
    if chart_type not in ("pixel", "symbol"):
        raise HTTPException(status_code=400, detail="chart_type không hợp lệ")

    allowed_subtypes = SUBTYPES_BY_GARMENT[garment_type]
    if subtype is not None and subtype not in allowed_subtypes:
        raise HTTPException(
            status_code=400,
            detail=f"subtype không hợp lệ cho {garment_type}, chỉ chấp nhận: {allowed_subtypes}",
        )

    if chart_type == "pixel" and image is None:
        raise HTTPException(status_code=400, detail="Cần upload ảnh để tạo pixel chart")

    try:
        raw_pieces, assembly, notes = formulas.GENERATORS[garment_type](measurements_obj, subtype)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    image_bytes: Optional[bytes] = None
    dominant_hex: Optional[str] = None
    foreground_full = None
    regions: dict = {}
    if image is not None:
        image_bytes = await image.read()
        try:
            dominant_hex = color_chart.dominant_color_hex(image_bytes)
            foreground_full = image_io.crop_to_foreground(image_io.load_cv2_image(image_bytes))
            if garment_type == "ao":
                regions = garment_regions.detect_ao_regions(image_bytes)
                if "sleeve_left" not in regions or "sleeve_right" not in regions:
                    notes = notes + [
                        "Không tách được vùng tay áo riêng biệt từ ảnh (có thể do góc chụp/ảnh không "
                        "thể hiện rõ 2 tay) - tay áo đang dùng màu chủ đạo chung."
                    ]
                if "body" in regions:
                    left, right = _split_left_right(regions["body"])
                    regions["body_left"] = left
                    regions["body_right"] = right

                if back_image is not None:
                    back_bytes = await back_image.read()
                    try:
                        regions["back"] = image_io.crop_to_foreground(image_io.load_cv2_image(back_bytes))
                    except ValueError as exc:
                        raise HTTPException(status_code=400, detail=f"Ảnh mặt sau lỗi: {exc}") from exc
                elif chart_type == "pixel":
                    notes = notes + [
                        "Thân sau không xuất hiện trong ảnh chụp (chỉ upload 1 ảnh mặt trước) - "
                        "đang dùng màu chủ đạo ước lượng. Upload thêm ảnh mặt sau để có pixel chart "
                        "chính xác cho thân sau."
                    ]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    pieces: list[PatternPiece] = []
    for raw in raw_pieces:
        pixel_chart_obj = None
        symbol_chart_obj = None
        region_key = _region_key_for_piece(raw["name"])
        region_array = regions.get(region_key) if region_key else None
        is_picture_piece = raw.get("is_picture_piece", True)

        if chart_type == "pixel":
            cols, rows = color_chart.grid_size_for_dimensions(raw["width_cm"], raw["height_cm"])
            try:
                if region_array is not None:
                    # Có dữ liệu vùng thật được tách từ ảnh -> luôn dùng, chính
                    # xác hơn là màu trơn ước lượng.
                    grid, legend = color_chart.generate_pixel_chart_from_array(region_array, cols, rows)
                elif is_picture_piece and image_bytes:
                    grid, legend = color_chart.generate_pixel_chart(image_bytes, cols=cols, rows=rows)
                else:
                    grid, legend = color_chart.solid_pixel_chart(cols, rows, dominant_hex or "#cccccc")
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            pixel_chart_obj = PixelChart(rows=rows, cols=cols, grid=grid, legend=legend)
        else:
            if image_bytes is not None and is_picture_piece:
                source_array = region_array if region_array is not None else foreground_full
                if source_array is not None:
                    _inject_color_bands(raw, source_array)
            symbol_chart_obj = SymbolChart(rounds=raw["symbol_rounds"])

        pieces.append(
            PatternPiece(
                name=raw["name"],
                width_cm=raw["width_cm"],
                height_cm=raw["height_cm"],
                written_pattern=raw["written"],
                symbol_chart=symbol_chart_obj,
                pixel_chart=pixel_chart_obj,
            )
        )

    schematic_svg = schematic.generate_svg_schematic(raw_pieces)
    materials = formulas.estimate_materials(
        raw_pieces, measurements_obj.gauge_stitches_per_10cm, measurements_obj.gauge_rows_per_10cm
    )

    return GenerateResponse(
        garment_type=garment_type,
        subtype=subtype,
        chart_type=chart_type,
        pieces=pieces,
        assembly_instructions=assembly,
        notes=notes,
        schematic_svg=schematic_svg,
        abbreviations=formulas.ABBREVIATIONS,
        materials=materials,
    )
