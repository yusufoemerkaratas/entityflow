from typing import Dict, List, Literal

from pydantic import BaseModel, Field


ReviewStatus = Literal["pending", "accepted", "rejected"]
ReviewAction = Literal["accepted", "rejected"]


class BoundingBox(BaseModel):

    x: int = Field(..., ge=0, description="Left coordinate of the bounding box in pixels.")
    y: int = Field(..., ge=0, description="Top coordinate of the bounding box in pixels.")
    width: int = Field(..., gt=0, description="Width of the bounding box in pixels.")
    height: int = Field(..., gt=0, description="Height of the bounding box in pixels.")


class VisualDetection(BaseModel):

    label: str = Field(
        default="visual_defect_candidate", description="Human-readable label for the detected visual region.",)
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Heuristic confidence score between 0.0 and 1.0.",
    )
    bbox: BoundingBox = Field(..., description="Bounding box of the detected region.")
    review_status: ReviewStatus = Field(
        default="pending",
        description="Human review status for the detection.",
    )


class VisualDetectionOut(VisualDetection):

    id: int = Field(..., description="Database identifier for the detected region.")


class VisionInspectionResponse(BaseModel):

    inspection_id: int = Field(..., description="Database identifier for the inspection run.")

    filename: str = Field(..., description="Original uploaded filename.")
    image_width: int = Field(..., gt=0, description="Width of the image coordinate space.")
    image_height: int = Field(..., gt=0, description="Height of the image coordinate space.")
    detections: List[VisualDetectionOut] = Field(
        default_factory=list,
        description="List of detected visual regions.",
    )


class VisionDetectionReviewRequest(BaseModel):

    review_status: ReviewAction = Field(
        ..., description="Updated human review state for the detection."
    )


class VisionOcrResponse(BaseModel):
    filename: str = Field(..., description="Original uploaded filename.")
    image_width: int = Field(..., gt=0, description="Width of the uploaded image in pixels.")
    image_height: int = Field(..., gt=0, description="Height of the uploaded image in pixels.")
    extracted_text: str = Field(..., description="OCR text normalized for downstream processing.")
    raw_text: str = Field(..., description="Raw OCR text before normalization.")
    char_count: int = Field(..., ge=0, description="Character count of the normalized OCR text.")
    is_empty: bool = Field(..., description="Whether OCR returned usable text.")
    engine: str = Field(..., description="OCR engine identifier used for extraction.")


class VisionOcrExtractionRun(BaseModel):
    extractor_name: str = Field(..., description="Extractor key used in the run.")
    extraction_id: int = Field(..., description="Created extraction row identifier.")
    entity_count: int = Field(..., ge=0, description="Entity count found by this extractor.")


class VisionOcrExtractionResponse(BaseModel):
    document_id: int = Field(..., description="Document id created/reused for OCR text.")
    source_type: str = Field(..., description="Document source marker for provenance.")
    is_duplicate_document: bool = Field(..., description="Whether OCR text matched an existing document.")
    ocr: VisionOcrResponse = Field(..., description="OCR output used as extraction input.")
    runs: List[VisionOcrExtractionRun] = Field(
        default_factory=list,
        description="Extractor runs executed for this OCR upload.",
    )
    results: Dict[str, List[dict]] = Field(
        default_factory=dict,
        description="Extractor output grouped by extractor name.",
    )
