from typing import Literal, Optional
from pydantic import BaseModel, Field

GarmentType = Literal["mu", "ao", "vay", "khan"]
ChartType = Literal["pixel", "symbol"]

# Subtype hop le theo tung garment_type - nguoi dung tu chon vi khong the
# suy ra tu ban ve tay (beanie/bucket, sweater/cardigan, vay don/vay beo la
# lua chon thiet ke, khong phai thuoc tinh hinh hoc doc duoc tu anh)
SUBTYPES_BY_GARMENT = {
    "mu": ("beanie", "bucket"),
    "ao": ("sweater", "cardigan"),
    "vay": ("don", "beo"),
    "khan": (None,),
}


class ClassifyResult(BaseModel):
    garment_type: GarmentType
    confidence: float
    diagnostics: dict


class Measurements(BaseModel):
    gauge_stitches_per_10cm: float = Field(..., gt=0, description="So mui tren 10cm")
    gauge_rows_per_10cm: float = Field(..., gt=0, description="So hang tren 10cm")

    # Khan
    scarf_width_cm: Optional[float] = None
    scarf_length_cm: Optional[float] = None

    # Mu (beanie + bucket)
    head_circumference_cm: Optional[float] = None
    hat_height_cm: Optional[float] = None
    bucket_brim_width_cm: Optional[float] = None  # do loe vanh, chi dung cho bucket

    # Ao (sweater + cardigan) - may theo manh (than truoc/sau + tay), khong phai top-down
    chest_circumference_cm: Optional[float] = None
    body_length_cm: Optional[float] = None
    sleeve_length_cm: Optional[float] = None
    sleeve_width_cm: Optional[float] = None  # chu vi bap tay, mac dinh uoc luong neu bo trong

    # Vay (don + beo)
    waist_circumference_cm: Optional[float] = None
    hip_circumference_cm: Optional[float] = None
    skirt_length_cm: Optional[float] = None
    ruffle_tiers: Optional[int] = None  # so tang beo, chi dung cho vay beo, mac dinh 3


class GenerateRequest(BaseModel):
    garment_type: GarmentType
    subtype: Optional[str] = None
    chart_type: ChartType
    measurements: Measurements


class PixelChart(BaseModel):
    rows: int
    cols: int
    grid: list[list[str]]
    legend: dict[str, str]


class SymbolRound(BaseModel):
    round_number: int
    instruction: str
    stitch_count: int


class SymbolChart(BaseModel):
    rounds: list[SymbolRound]


class PatternPiece(BaseModel):
    name: str
    width_cm: float
    height_cm: float
    written_pattern: list[str]
    symbol_chart: Optional[SymbolChart] = None
    pixel_chart: Optional[PixelChart] = None


class GenerateResponse(BaseModel):
    garment_type: GarmentType
    subtype: Optional[str] = None
    chart_type: ChartType
    pieces: list[PatternPiece]
    assembly_instructions: list[str] = []
    notes: list[str] = []
    schematic_svg: Optional[str] = None
    abbreviations: dict[str, str] = {}
    materials: list[str] = []
