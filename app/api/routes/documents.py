import hashlib

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.document import DocumentCreate, DocumentDetailResponse, DocumentResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse)
def create_document(payload: DocumentCreate, db: Session = Depends(get_db)):
    content_hash = hashlib.sha256(payload.text.encode("utf-8")).hexdigest()
    char_count = len(payload.text)

    existing_document = db.execute(
        text(
            """
            SELECT id, char_count, content_hash, uploaded_at
            FROM documents
            WHERE content_hash = :content_hash
            """
        ),
        {"content_hash": content_hash},
    ).mappings().first()

    if existing_document:
        return DocumentResponse(
            id=existing_document["id"],
            char_count=existing_document["char_count"],
            content_hash=existing_document["content_hash"],
            is_duplicate=True,
            uploaded_at=existing_document["uploaded_at"],
        )

    inserted_document = db.execute(
        text(
            """
            INSERT INTO documents (raw_text, source_type, content_hash, char_count)
            VALUES (:raw_text, :source_type, :content_hash, :char_count)
            RETURNING id, char_count, content_hash, uploaded_at
            """
        ),
        {
            "raw_text": payload.text,
            "source_type": payload.source_type,
            "content_hash": content_hash,
            "char_count": char_count,
        },
    ).mappings().first()

    db.commit()

    return DocumentResponse(
        id=inserted_document["id"],
        char_count=inserted_document["char_count"],
        content_hash=inserted_document["content_hash"],
        is_duplicate=False,
        uploaded_at=inserted_document["uploaded_at"],
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    row = db.execute(
        text(
            """
            SELECT id, raw_text, source_type, char_count, uploaded_at
            FROM documents
            WHERE id = :document_id
            """
        ),
        {"document_id": document_id},
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Document not found.")

    return DocumentDetailResponse(
        id=row["id"],
        raw_text=row["raw_text"],
        source_type=row["source_type"],
        char_count=row["char_count"],
        uploaded_at=row["uploaded_at"],
    )
