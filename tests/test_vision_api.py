import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def _create_test_png_bytes() -> bytes:
    """Create a simple PNG image with a visible black rectangle."""

    image = np.full((300, 400, 3), 255, dtype=np.uint8)
    cv2.rectangle(image, (120, 80), (260, 160), (0, 0, 0), -1)

    success, encoded = cv2.imencode(".png", image)
    assert success

    return encoded.tobytes()


def test_vision_inspect_accepts_valid_png_upload():
    image_bytes = _create_test_png_bytes()

    response = client.post(
        "/vision/inspect",
        files={
            "file": (
                "sample-product.png",
                image_bytes,
                "image/png",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "sample-product.png"
    assert data["image_width"] == 400
    assert data["image_height"] == 300
    assert "detections" in data
    assert isinstance(data["detections"], list)

    assert len(data["detections"]) >= 1

    detection = data["detections"][0]

    assert detection["label"] == "visual_defect_candidate"
    assert 0.0 <= detection["confidence"] <= 1.0
    assert detection["review_status"] == "pending"

    bbox = detection["bbox"]

    assert bbox["x"] >= 0
    assert bbox["y"] >= 0
    assert bbox["width"] > 0
    assert bbox["height"] > 0


def test_vision_inspect_rejects_unsupported_file_type():
    response = client.post(
        "/vision/inspect",
        files={
            "file": (
                "not-image.txt",
                b"hello this is not an image",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert "detail" in data
    assert "Unsupported image content type" in data["detail"]
