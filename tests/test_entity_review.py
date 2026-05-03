import hashlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.api.main import app
from app.db.database import get_db


client = TestClient(app)


def _db_session():
    gen = get_db()
    db = next(gen)
    try:
        yield db
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


@pytest.fixture()
def extracted_entity_id():
    gen = _db_session()
    db = next(gen)

    raw_text = "Alice from EntityFlow lives in Berlin and uses alice@example.com."
    content_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

    doc_row = db.execute(
        text(
            """
            INSERT INTO documents (raw_text, source_type, content_hash, char_count)
            VALUES (:raw_text, :source_type, :content_hash, :char_count)
            RETURNING id
            """
        ),
        {
            "raw_text": raw_text,
            "source_type": "test",
            "content_hash": content_hash,
            "char_count": len(raw_text),
        },
    ).mappings().first()

    db.commit()
    document_id = doc_row["id"]

    extract_response = client.post(f"/documents/{document_id}/extract?extractor=regex")
    assert extract_response.status_code == 200

    entity_row = db.execute(
        text(
            """
            SELECT id
            FROM entities
            WHERE extraction_id = (
                SELECT id
                FROM extractions
                WHERE document_id = :document_id
                ORDER BY created_at DESC
                LIMIT 1
            )
            ORDER BY id ASC
            LIMIT 1
            """
        ),
        {"document_id": document_id},
    ).mappings().first()

    yield document_id, entity_row["id"]

    db.execute(text("DELETE FROM documents WHERE id = :id"), {"id": document_id})
    db.commit()
    db.close()


def test_review_entity_updates_status_and_comparison_response(extracted_entity_id):
    document_id, entity_id = extracted_entity_id

    response = client.patch(
        f"/entities/{entity_id}/review",
        json={"review_status": "approved"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == entity_id
    assert data["review_status"] == "approved"

    comparison_response = client.get(f"/documents/{document_id}/extractions")
    assert comparison_response.status_code == 200
    comparison = comparison_response.json()

    regex_entities = comparison["results"]["regex"]["entities"]
    assert regex_entities[0]["id"] == entity_id
    assert regex_entities[0]["review_status"] == "approved"

    second_response = client.patch(
        f"/entities/{entity_id}/review",
        json={"review_status": "rejected"},
    )

    assert second_response.status_code == 200
    assert second_response.json()["review_status"] == "rejected"


def test_review_entity_rejects_invalid_status(extracted_entity_id):
    _, entity_id = extracted_entity_id

    response = client.patch(
        f"/entities/{entity_id}/review",
        json={"review_status": "pending"},
    )

    assert response.status_code == 422


def test_review_entity_returns_404_for_missing_entity():
    response = client.patch(
        "/entities/999999/review",
        json={"review_status": "approved"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Entity not found."