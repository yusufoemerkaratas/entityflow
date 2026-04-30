from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.extractors.regex_extractor import RegexExtractor

router = APIRouter(tags=["extractions"])


@router.post("/documents/{document_id}/extract")
def extract_document(
    document_id: int,
    extractor: str = Query(...),
    db: Session = Depends(get_db),
):
    if extractor != "regex":
        raise HTTPException(
            status_code=400,
            detail="Only the 'regex' extractor is supported right now.",
        )

    document_row = db.execute(
        text(
            """
            SELECT id, raw_text
            FROM documents
            WHERE id = :document_id
            """
        ),
        {"document_id": document_id},
    ).mappings().first()

    if not document_row:
        raise HTTPException(status_code=404, detail="Document not found.")

    regex_extractor = RegexExtractor()
    extracted_entities = regex_extractor.extract(document_row["raw_text"])

    extraction_row = db.execute(
        text(
            """
            INSERT INTO extractions (document_id, extractor_name, extractor_version, processing_ms)
            VALUES (:document_id, :extractor_name, :extractor_version, :processing_ms)
            RETURNING id, extractor_name, extractor_version, created_at
            """
        ),
        {
            "document_id": document_id,
            "extractor_name": regex_extractor.name,
            "extractor_version": regex_extractor.version,
            "processing_ms": 0,
        },
    ).mappings().first()

    for entity in extracted_entities:
        db.execute(
            text(
                """
                INSERT INTO entities (
                    extraction_id,
                    entity_type,
                    entity_text,
                    normalized_value,
                    confidence,
                    span_start,
                    span_end
                )
                VALUES (
                    :extraction_id,
                    :entity_type,
                    :entity_text,
                    :normalized_value,
                    :confidence,
                    :span_start,
                    :span_end
                )
                """
            ),
            {
                "extraction_id": extraction_row["id"],
                "entity_type": entity.entity_type,
                "entity_text": entity.entity_text,
                "normalized_value": entity.entity_text,
                "confidence": entity.confidence,
                "span_start": entity.span_start,
                "span_end": entity.span_end,
            },
        )

    db.commit()

    return {
        "document_id": document_id,
        "extraction_id": extraction_row["id"],
        "extractor_name": extraction_row["extractor_name"],
        "extractor_version": extraction_row["extractor_version"],
        "entity_count": len(extracted_entities),
        "entities": [
            {
                "entity_type": entity.entity_type,
                "entity_text": entity.entity_text,
                "span_start": entity.span_start,
                "span_end": entity.span_end,
                "confidence": entity.confidence,
            }
            for entity in extracted_entities
        ],
    }