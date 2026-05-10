from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np


ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_PROCESSING_WIDTH = 1200
BLUR_KERNEL_SIZE: Tuple[int, int] = (5, 5)
ADAPTIVE_THRESHOLD_BLOCK_SIZE = 31
ADAPTIVE_THRESHOLD_C = 5
OCR_THRESHOLD_BLOCK_SIZE = 21
OCR_THRESHOLD_C = 10


class InvalidImageError(ValueError):
    """Raised when uploaded image data is invalid or unsupported."""


@dataclass(frozen=True)
class PreprocessedImage:
    """Container for all image representations needed by the inspection pipeline."""

    original_width: int
    original_height: int
    working_width: int
    working_height: int
    scale: float
    working_image: np.ndarray
    grayscale_image: np.ndarray
    blurred_image: np.ndarray
    binary_image: np.ndarray


def validate_image_content_type(content_type: Optional[str]) -> None:
    """Validate that the uploaded file has a supported image content type."""

    if not content_type:
        raise InvalidImageError("Missing image content type.")

    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        supported = ", ".join(sorted(ALLOWED_IMAGE_CONTENT_TYPES))
        raise InvalidImageError(
            f"Unsupported image content type '{content_type}'. "
            f"Supported types are: {supported}."
        )


def validate_image_size(image_bytes: bytes) -> None:
    """Validate that uploaded image bytes are present and within the size limit."""

    if not image_bytes:
        raise InvalidImageError("Uploaded image file is empty.")

    if len(image_bytes) > MAX_IMAGE_BYTES:
        max_mb = MAX_IMAGE_BYTES // (1024 * 1024)
        raise InvalidImageError(f"Uploaded image exceeds the {max_mb} MB size limit.")


def decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    """Decode raw image bytes into an OpenCV BGR image array."""

    validate_image_size(image_bytes)

    image_buffer = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_buffer, cv2.IMREAD_COLOR)

    if image is None:
        raise InvalidImageError("Uploaded file could not be decoded as a valid image.")

    return image


def resize_for_processing(
    image: np.ndarray,
    max_width: int = MAX_PROCESSING_WIDTH,
) -> tuple[np.ndarray, float]:
    """Resize image for faster processing while preserving aspect ratio."""

    height, width = image.shape[:2]

    if width <= max_width:
        return image.copy(), 1.0

    scale = max_width / width
    new_height = max(1, int(height * scale))
    resized = cv2.resize(image, (max_width, new_height), interpolation=cv2.INTER_AREA)

    return resized, scale


def preprocess_for_inspection(image: np.ndarray) -> PreprocessedImage:
    """Prepare a decoded OpenCV image for contour-based visual inspection."""

    if image is None or image.size == 0:
        raise InvalidImageError("Cannot preprocess an empty image.")

    if image.ndim < 2:
        raise InvalidImageError("Invalid image shape for preprocessing.")

    original_height, original_width = image.shape[:2]

    working_image, scale = resize_for_processing(image)
    working_height, working_width = working_image.shape[:2]

    grayscale_image = cv2.cvtColor(working_image, cv2.COLOR_BGR2GRAY)
    blurred_image = cv2.GaussianBlur(grayscale_image, BLUR_KERNEL_SIZE, 0)

    binary_image = cv2.adaptiveThreshold(
        blurred_image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        ADAPTIVE_THRESHOLD_BLOCK_SIZE,
        ADAPTIVE_THRESHOLD_C,
    )

    return PreprocessedImage(
        original_width=original_width,
        original_height=original_height,
        working_width=working_width,
        working_height=working_height,
        scale=scale,
        working_image=working_image,
        grayscale_image=grayscale_image,
        blurred_image=blurred_image,
        binary_image=binary_image,
    )


def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    """Prepare a decoded OpenCV image for OCR-friendly thresholding."""

    if image is None or image.size == 0:
        raise InvalidImageError("Cannot preprocess an empty image.")

    if image.ndim < 2:
        raise InvalidImageError("Invalid image shape for preprocessing.")

    working_image, _ = resize_for_processing(image)
    grayscale_image = cv2.cvtColor(working_image, cv2.COLOR_BGR2GRAY)
    blurred_image = cv2.GaussianBlur(grayscale_image, BLUR_KERNEL_SIZE, 0)

    return cv2.adaptiveThreshold(
        blurred_image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        OCR_THRESHOLD_BLOCK_SIZE,
        OCR_THRESHOLD_C,
    )
