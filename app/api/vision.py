from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.vision.inspection import inspect_image
from app.vision.preprocessing import (
    InvalidImageError,
    decode_image_bytes,
    validate_image_content_type,
)
from app.db.database import get_db
from app.schemas.vision import (
    BoundingBox,
    VisionDetectionReviewRequest,
    VisionInspectionResponse,
    VisualDetectionOut,
)


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
