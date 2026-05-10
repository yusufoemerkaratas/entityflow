import os
import subprocess
import tempfile
from dataclasses import dataclass

import cv2
import numpy as np

from app.vision.preprocessing import InvalidImageError, preprocess_for_ocr


DEFAULT_TESSERACT_CMD = "tesseract"
DEFAULT_TESSERACT_LANGUAGE = "eng"
DEFAULT_TESSERACT_CONFIG = ("--psm", "6")


class OcrEngineUnavailableError(RuntimeError):
    """Raised when the OCR engine binary is not available."""


class OcrProcessingError(RuntimeError):
    """Raised when the OCR engine fails during processing."""


@dataclass(frozen=True)
class OcrExtractionResult:
    raw_text: str
    extracted_text: str
    char_count: int
    is_empty: bool
    engine: str = "tesseract"


def normalize_ocr_text(text: str) -> str:
    """Collapse OCR output into a cleaner single string for downstream NLP."""

    stripped_lines = [line.strip() for line in text.splitlines()]
    non_empty_lines = [line for line in stripped_lines if line]

    return "\n".join(non_empty_lines).strip()


def _resolve_tesseract_command() -> str:
    return os.getenv("TESSERACT_CMD", DEFAULT_TESSERACT_CMD)


def _run_tesseract_on_image(processed_image: np.ndarray) -> str:
    success, encoded = cv2.imencode(".png", processed_image)
    if not success:
        raise OcrProcessingError("Failed to encode the preprocessed image for OCR.")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as temp_image:
        temp_image.write(encoded.tobytes())
        temp_image.flush()

        command = [
            _resolve_tesseract_command(),
            temp_image.name,
            "stdout",
            "-l",
            os.getenv("TESSERACT_LANG", DEFAULT_TESSERACT_LANGUAGE),
            *DEFAULT_TESSERACT_CONFIG,
        ]

        try:
            completed = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise OcrEngineUnavailableError(
                "Tesseract OCR is not installed or not available in PATH."
            ) from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip() if exc.stderr else "unknown OCR failure"
            raise OcrProcessingError(f"Tesseract OCR failed: {stderr}") from exc

    return completed.stdout


def extract_text_from_image(image: np.ndarray) -> OcrExtractionResult:
    """Run OCR on a decoded OpenCV image and normalize the output text."""

    if image is None or image.size == 0:
        raise InvalidImageError("Cannot run OCR on an empty image.")

    processed_image = preprocess_for_ocr(image)
    raw_text = _run_tesseract_on_image(processed_image)
    normalized_text = normalize_ocr_text(raw_text)

    return OcrExtractionResult(
        raw_text=raw_text,
        extracted_text=normalized_text,
        char_count=len(normalized_text),
        is_empty=normalized_text == "",
    )
