from fastapi.testclient import TestClient
import cv2
import numpy as np

from app.api.main import app
from app.vision.ocr import OcrExtractionResult


client = TestClient(app)


def _create_test_png_bytes() -> bytes:
    image = np.full((180, 420, 3), 255, dtype=np.uint8)
    cv2.putText(
        image,
        "alice@example.com",
        (20, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 0, 0),
        2,
        cv2.LINE_AA,
    )

    success, encoded = cv2.imencode(".png", image)
    assert success

    return encoded.tobytes()


def test_vision_ocr_returns_extracted_text(monkeypatch):
    def _fake_extract_text_from_image(image):
        return OcrExtractionResult(
            raw_text="Alice Example\nalice@example.com\n",
            extracted_text="Alice Example\nalice@example.com",
            char_count=len("Alice Example\nalice@example.com"),
            is_empty=False,
        )

    monkeypatch.setattr("app.api.vision.extract_text_from_image", _fake_extract_text_from_image)

    response = client.post(
        "/vision/ocr",
        files={"file": ("ocr-sample.png", _create_test_png_bytes(), "image/png")},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "ocr-sample.png"
    assert data["image_width"] == 420
    assert data["image_height"] == 180
    assert data["raw_text"] == "Alice Example\nalice@example.com\n"
    assert data["extracted_text"] == "Alice Example\nalice@example.com"
    assert data["char_count"] == len("Alice Example\nalice@example.com")
    assert data["is_empty"] is False
    assert data["engine"] == "tesseract"


def test_vision_ocr_handles_empty_text_result(monkeypatch):
    def _fake_extract_text_from_image(image):
        return OcrExtractionResult(
            raw_text="\n\n",
            extracted_text="",
            char_count=0,
            is_empty=True,
        )

    monkeypatch.setattr("app.api.vision.extract_text_from_image", _fake_extract_text_from_image)

    response = client.post(
        "/vision/ocr",
        files={"file": ("empty-ocr.png", _create_test_png_bytes(), "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_empty"] is True
    assert data["extracted_text"] == ""
    assert data["char_count"] == 0


def test_vision_ocr_rejects_unsupported_file_type():
    response = client.post(
        "/vision/ocr",
        files={"file": ("ocr.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 400
    assert "Unsupported image content type" in response.json()["detail"]
