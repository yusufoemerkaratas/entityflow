from typing import List

import cv2
import numpy as np

from app.vision.preprocessing import PreprocessedImage, preprocess_for_inspection
from app.schemas.vision import BoundingBox, VisualDetection


MIN_REGION_AREA_RATIO = 0.0005
MAX_REGION_AREA_RATIO = 0.35
MAX_DETECTIONS = 25
MORPH_KERNEL_SIZE = (5, 5)


def _clean_binary_image(binary_image: np.ndarray) -> np.ndarray:
    """Reduce tiny gaps and connect nearby foreground regions before contour detection."""

    kernel = np.ones(MORPH_KERNEL_SIZE, dtype=np.uint8)
    closed = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, kernel)
    cleaned = cv2.dilate(closed, kernel, iterations=1)

    return cleaned


def _calculate_confidence(area_ratio: float, fill_ratio: float) -> float:
    """Calculate a heuristic confidence score for a detected visual region."""

    area_component = min(area_ratio / 0.05, 1.0)
    fill_component = min(fill_ratio, 1.0)

    confidence = 0.35 + (0.50 * area_component) + (0.10 * fill_component)
    confidence = max(0.0, min(confidence, 0.95))

    return round(float(confidence), 2)


def _scale_bbox_to_original(
    x: int,
    y: int,
    width: int,
    height: int,
    preprocessed: PreprocessedImage,
) -> BoundingBox | None:
    """Convert a bounding box from working-image coordinates to original-image coordinates."""

    scale = preprocessed.scale if preprocessed.scale > 0 else 1.0

    original_x = int(round(x / scale))
    original_y = int(round(y / scale))
    original_width = int(round(width / scale))
    original_height = int(round(height / scale))

    original_x = max(0, min(original_x, preprocessed.original_width - 1))
    original_y = max(0, min(original_y, preprocessed.original_height - 1))

    original_width = min(original_width, preprocessed.original_width - original_x)
    original_height = min(original_height, preprocessed.original_height - original_y)

    if original_width <= 0 or original_height <= 0:
        return None

    return BoundingBox(
        x=original_x,
        y=original_y,
        width=original_width,
        height=original_height,
    )


def inspect_image(
    image: np.ndarray,
    max_detections: int = MAX_DETECTIONS,
) -> List[VisualDetection]:
    """Run lightweight contour-based visual inspection on a decoded OpenCV image."""

    preprocessed = preprocess_for_inspection(image)
    cleaned_binary = _clean_binary_image(preprocessed.binary_image)

    contours, _ = cv2.findContours(
        cleaned_binary,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    working_area = preprocessed.working_width * preprocessed.working_height
    min_area = working_area * MIN_REGION_AREA_RATIO
    max_area = working_area * MAX_REGION_AREA_RATIO

    detections: List[VisualDetection] = []

    for contour in contours:
        contour_area = cv2.contourArea(contour)

        if contour_area < min_area or contour_area > max_area:
            continue

        x, y, width, height = cv2.boundingRect(contour)

        if width <= 1 or height <= 1:
            continue

        bbox_area = width * height
        fill_ratio = contour_area / bbox_area if bbox_area > 0 else 0.0
        area_ratio = contour_area / working_area if working_area > 0 else 0.0

        bbox = _scale_bbox_to_original(
            x=x,
            y=y,
            width=width,
            height=height,
            preprocessed=preprocessed,
        )

        if bbox is None:
            continue

        confidence = _calculate_confidence(
            area_ratio=area_ratio,
            fill_ratio=fill_ratio,
        )

        detections.append(
            VisualDetection(
                confidence=confidence,
                bbox=bbox,
            )
        )

    detections.sort(key=lambda detection: detection.confidence, reverse=True)

    return detections[:max_detections]
