import hashlib

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.vision.inspection import inspect_image
from app.vision.ocr import (
    OcrEngineUnavailableError,
    OcrProcessingError,
    extract_text_from_image,
)
from app.vision.preprocessing import (
    InvalidImageError,
    decode_image_bytes,
    validate_image_content_type,
)
from app.db.database import get_db
from app.schemas.vision import (
    BoundingBox,
    VisionDetectionReviewRequest,
    VisionOcrExtractionResponse,
    VisionOcrExtractionRun,
    VisionInspectionResponse,
    VisionOcrResponse,
    VisualDetectionOut,
)
from app.services.extraction_pipeline import parse_extractors, run_extractor_and_persist


router = APIRouter(prefix="/vision", tags=["vision"])


def _build_detection_response(row) -> VisualDetectionOut:
    return VisualDetectionOut(
        id=row["id"],
        label=row["label"],
        confidence=row["confidence"],
        bbox=BoundingBox(
            x=row["bbox_x"],
            y=row["bbox_y"],
            width=row["bbox_width"],
            height=row["bbox_height"],
        ),
        review_status=row["review_status"],
    )


@router.post("/ocr", response_model=VisionOcrResponse)
async def extract_ocr_text(
    file: UploadFile = File(...),
) -> VisionOcrResponse:
    """Extract readable text from an uploaded image using OCR."""

    try:
        validate_image_content_type(file.content_type)

        image_bytes = await file.read()
        image = decode_image_bytes(image_bytes)
        ocr_result = extract_text_from_image(image)

        height, width = image.shape[:2]

        return VisionOcrResponse(
            filename=file.filename or "uploaded-image",
            image_width=width,
            image_height=height,
            extracted_text=ocr_result.extracted_text,
            raw_text=ocr_result.raw_text,
            char_count=ocr_result.char_count,
            is_empty=ocr_result.is_empty,
            engine=ocr_result.engine,
        )
    except InvalidImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except OcrEngineUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except OcrProcessingError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/ocr/extract", response_model=VisionOcrExtractionResponse)
async def extract_ocr_and_run_extractors(
    file: UploadFile = File(...),
    extractors: str = "regex,spacy_de",
    db: Session = Depends(get_db),
) -> VisionOcrExtractionResponse:
    """Run OCR and feed the text into the existing entity extraction pipeline."""

    try:
        validate_image_content_type(file.content_type)
        selected_extractors = parse_extractors(extractors)

        image_bytes = await file.read()
        image = decode_image_bytes(image_bytes)
        ocr_result = extract_text_from_image(image)

        if ocr_result.is_empty:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="OCR returned empty text. Use an image with readable text.",
            )

        source_type = "image_ocr"
        content_hash = hashlib.sha256(ocr_result.extracted_text.encode("utf-8")).hexdigest()
        char_count = len(ocr_result.extracted_text)

        existing_document = db.execute(
            text(
                """
                SELECT id
                FROM documents
                WHERE content_hash = :content_hash
                """
            ),
            {"content_hash": content_hash},
        ).mappings().first()

        is_duplicate_document = existing_document is not None
        if existing_document:
            document_id = existing_document["id"]
        else:
            inserted_document = db.execute(
                text(
                    """
                    INSERT INTO documents (raw_text, source_type, content_hash, char_count)
                    VALUES (:raw_text, :source_type, :content_hash, :char_count)
                    RETURNING id
                    """
                ),
                {
                    "raw_text": ocr_result.extracted_text,
                    "source_type": source_type,
                    "content_hash": content_hash,
                    "char_count": char_count,
                },
            ).mappings().first()
            document_id = inserted_document["id"]

        run_summaries = []
        results = {}

        for extractor in selected_extractors:
            extraction_result = run_extractor_and_persist(
                db=db,
                document_id=document_id,
                raw_text=ocr_result.extracted_text,
                extractor=extractor,
            )
            run_summaries.append(
                VisionOcrExtractionRun(
                    extractor_name=extractor,
                    extraction_id=extraction_result.extraction_id,
                    entity_count=len(extraction_result.entities),
                )
            )
            results[extractor] = [
                {
                    "entity_type": entity.entity_type,
                    "entity_text": entity.entity_text,
                    "span_start": entity.span_start,
                    "span_end": entity.span_end,
                    "confidence": entity.confidence,
                }
                for entity in extraction_result.entities
            ]

        db.commit()

        height, width = image.shape[:2]
        return VisionOcrExtractionResponse(
            document_id=document_id,
            source_type=source_type,
            is_duplicate_document=is_duplicate_document,
            ocr=VisionOcrResponse(
                filename=file.filename or "uploaded-image",
                image_width=width,
                image_height=height,
                extracted_text=ocr_result.extracted_text,
                raw_text=ocr_result.raw_text,
                char_count=ocr_result.char_count,
                is_empty=ocr_result.is_empty,
                engine=ocr_result.engine,
            ),
            runs=run_summaries,
            results=results,
        )
    except InvalidImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except OcrEngineUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except OcrProcessingError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/inspect", response_model=VisionInspectionResponse)
async def inspect_uploaded_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> VisionInspectionResponse:
    """Run lightweight visual inspection on an uploaded image."""

    try:
        validate_image_content_type(file.content_type)

        image_bytes = await file.read()
        image = decode_image_bytes(image_bytes)
        detections = inspect_image(image)

        height, width = image.shape[:2]

        inspection_row = db.execute(
            text(
                """
                INSERT INTO vision_inspections (filename, image_width, image_height)
                VALUES (:filename, :image_width, :image_height)
                RETURNING id
                """
            ),
            {
                "filename": file.filename or "uploaded-image",
                "image_width": width,
                "image_height": height,
            },
        ).mappings().first()

        if not inspection_row:
            raise HTTPException(status_code=500, detail="Failed to persist vision inspection.")

        inspection_id = inspection_row["id"]

        persisted_detections = []
        for detection in detections:
            detection_row = db.execute(
                text(
                    """
                    INSERT INTO vision_detections (
                        inspection_id, label, confidence, bbox_x, bbox_y, bbox_width, bbox_height, review_status
                    )
                    VALUES (
                        :inspection_id, :label, :confidence, :bbox_x, :bbox_y, :bbox_width, :bbox_height, :review_status
                    )
                    RETURNING id, label, confidence, bbox_x, bbox_y, bbox_width, bbox_height, review_status
                    """
                ),
                {
                    "inspection_id": inspection_id,
                    "label": detection.label,
                    "confidence": detection.confidence,
                    "bbox_x": detection.bbox.x,
                    "bbox_y": detection.bbox.y,
                    "bbox_width": detection.bbox.width,
                    "bbox_height": detection.bbox.height,
                    "review_status": detection.review_status,
                },
            ).mappings().first()

            if detection_row:
                persisted_detections.append(_build_detection_response(detection_row))

        db.commit()

        return VisionInspectionResponse(
            inspection_id=inspection_id,
            filename=file.filename or "uploaded-image",
            image_width=width,
            image_height=height,
            detections=persisted_detections,
        )

    except InvalidImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch("/detections/{detection_id}/review", response_model=VisualDetectionOut)
def review_detection(
    detection_id: int,
    payload: VisionDetectionReviewRequest,
    db: Session = Depends(get_db),
) -> VisualDetectionOut:
    row = db.execute(
        text(
            """
            UPDATE vision_detections
            SET review_status = :review_status
            WHERE id = :detection_id
            RETURNING id, label, confidence, bbox_x, bbox_y, bbox_width, bbox_height, review_status
            """
        ),
        {"review_status": payload.review_status, "detection_id": detection_id},
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Visual detection not found.")

    db.commit()

    return _build_detection_response(row)
