from typing import Optional

import cv2
import numpy as np


ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB


class InvalidImageError(ValueError):
    """Raised when uploaded image data is invalid or unsupported."""


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
