"""Tests for the GET /documents/{id} endpoint."""

import hashlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.api.main import app
from app.db.database import get_db


client = TestClient(app)


def _get_db_session():
    """Get a raw DB session for test setup."""
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
def sample_document_id():
    """Insert a sample document and return its id. Clean up after test."""
    gen = _get_db_session()
    db = next(gen)

    raw_text = "This is a test document with enough characters for validation."
    content_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

    row = db.execute(
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
    doc_id = row["id"]

    yield doc_id

    # cleanup
    db.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})
    db.commit()
    db.close()


def test_get_document_returns_200(sample_document_id: int):
    response = client.get(f"/documents/{sample_document_id}")

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == sample_document_id
    assert "raw_text" in data
    assert data["raw_text"] == "This is a test document with enough characters for validation."
    assert data["source_type"] == "test"
    assert "char_count" in data
    assert "uploaded_at" in data


def test_get_document_returns_404_for_missing_id():
    response = client.get("/documents/999999")

    assert response.status_code == 404

    data = response.json()
    assert data["detail"] == "Document not found."
