from fastapi.testclient import TestClient
import cv2
import numpy as np

from app.api.main import app
from app.services.extraction_pipeline import PersistedExtractionResult
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


def test_vision_ocr_extract_runs_existing_pipeline(monkeypatch):
    def _fake_extract_text_from_image(image):
        return OcrExtractionResult(
            raw_text="Alice Example\nalice@example.com\n",
            extracted_text="Alice Example\nalice@example.com",
            char_count=len("Alice Example\nalice@example.com"),
            is_empty=False,
        )

    class _Entity:
        def __init__(self, entity_type: str, entity_text: str):
            self.entity_type = entity_type
            self.entity_text = entity_text
            self.span_start = 0
            self.span_end = len(entity_text)
            self.confidence = 0.95

    def _fake_run_extractor_and_persist(db, document_id, raw_text, extractor):
        return PersistedExtractionResult(
            extraction_id=100 if extractor == "regex" else 101,
            extractor_name=extractor,
            extractor_version="test",
            entities=[_Entity("email", "alice@example.com")],
        )

    monkeypatch.setattr("app.api.vision.extract_text_from_image", _fake_extract_text_from_image)
    monkeypatch.setattr("app.api.vision.run_extractor_and_persist", _fake_run_extractor_and_persist)

    response = client.post(
        "/vision/ocr/extract?extractors=regex,spacy_de",
        files={"file": ("ocr-sample.png", _create_test_png_bytes(), "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["source_type"] == "image_ocr"
    assert data["ocr"]["extracted_text"] == "Alice Example\nalice@example.com"
    assert len(data["runs"]) == 2
    assert data["runs"][0]["extractor_name"] == "regex"
    assert data["runs"][1]["extractor_name"] == "spacy_de"
    assert data["results"]["regex"][0]["entity_text"] == "alice@example.com"


def test_vision_ocr_extract_rejects_empty_ocr(monkeypatch):
    def _fake_extract_text_from_image(image):
        return OcrExtractionResult(
            raw_text="\n\n",
            extracted_text="",
            char_count=0,
            is_empty=True,
        )

    monkeypatch.setattr("app.api.vision.extract_text_from_image", _fake_extract_text_from_image)

    response = client.post(
        "/vision/ocr/extract?extractors=regex,spacy_de",
        files={"file": ("empty-ocr.png", _create_test_png_bytes(), "image/png")},
    )

    assert response.status_code == 422
    assert "OCR returned empty text" in response.json()["detail"]
