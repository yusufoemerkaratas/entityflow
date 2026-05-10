from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.vision.inspection import inspect_image
from app.vision.preprocessing import (
    InvalidImageError,
    decode_image_bytes,
    validate_image_content_type,
)
from app.schemas.vision import VisionInspectionResponse


router = APIRouter(prefix="/vision", tags=["vision"])


@router.post("/inspect", response_model=VisionInspectionResponse)
async def inspect_uploaded_image(file: UploadFile = File(...)) -> VisionInspectionResponse:
    """Run lightweight visual inspection on an uploaded image."""

    try:
        validate_image_content_type(file.content_type)

        image_bytes = await file.read()
        image = decode_image_bytes(image_bytes)
        detections = inspect_image(image)

        height, width = image.shape[:2]

        return VisionInspectionResponse(
            filename=file.filename or "uploaded-image",
            image_width=width,
            image_height=height,
            detections=detections,
        )

    except InvalidImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
