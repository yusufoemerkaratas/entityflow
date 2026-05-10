import subprocess

import numpy as np
import pytest

from app.vision.ocr import (
    OcrEngineUnavailableError,
    OcrProcessingError,
    extract_text_from_image,
    normalize_ocr_text,
)


def _create_test_image() -> np.ndarray:
    return np.full((120, 240, 3), 255, dtype=np.uint8)


def test_normalize_ocr_text_removes_empty_lines():
    raw_text = "\n  Alice Example  \n\n alice@example.com \n"

    normalized = normalize_ocr_text(raw_text)

    assert normalized == "Alice Example\nalice@example.com"


def test_extract_text_from_image_raises_when_tesseract_missing(monkeypatch):
    def _fake_run(*args, **kwargs):
        raise FileNotFoundError("tesseract not found")

    monkeypatch.setattr("app.vision.ocr.subprocess.run", _fake_run)

    with pytest.raises(OcrEngineUnavailableError):
        extract_text_from_image(_create_test_image())


def test_extract_text_from_image_returns_normalized_result(monkeypatch):
    def _fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="Alice Example\n\nalice@example.com\n",
            stderr="",
        )

    monkeypatch.setattr("app.vision.ocr.subprocess.run", _fake_run)

    result = extract_text_from_image(_create_test_image())

    assert result.raw_text == "Alice Example\n\nalice@example.com\n"
    assert result.extracted_text == "Alice Example\nalice@example.com"
    assert result.char_count == len("Alice Example\nalice@example.com")
    assert result.is_empty is False


def test_extract_text_from_image_surfaces_ocr_failure(monkeypatch):
    def _fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=args[0],
            stderr="ocr crashed",
        )

    monkeypatch.setattr("app.vision.ocr.subprocess.run", _fake_run)

    with pytest.raises(OcrProcessingError, match="ocr crashed"):
        extract_text_from_image(_create_test_image())
