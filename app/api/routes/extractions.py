from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.extractors.regex_extractor import RegexExtractor
from app.extractors.spacy_extractor import SpacyExtractor
from app.extractors.llm_extractor import LlmExtractor

from app.schemas.comparison import ComparisonResponse, ExtractionMeta, EntityOut

router = APIRouter(tags=["extractions"])


@router.post("/documents/{document_id}/extract")
def extract_document(
    document_id: int,
    extractor: str = Query(...),
    db: Session = Depends(get_db),
):
    if extractor == "regex":
        selected_extractor = RegexExtractor()
    elif extractor == "spacy_de":
        selected_extractor = SpacyExtractor()
    elif extractor == "llm_mini":
        selected_extractor = LlmExtractor()
    else:
        raise HTTPException(
            status_code=400,
            detail="Supported extractors are 'regex', 'spacy_de', and 'llm_mini'.")

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

    extracted_entities = selected_extractor.extract(document_row["raw_text"])

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
            "extractor_name": selected_extractor.name,
            "extractor_version": selected_extractor.version,
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

@router.get("/documents/{document_id}/extractions", response_model=ComparisonResponse)

def get_comparison(document_id: int, db: Session = Depends(get_db)):
    
    doc = db.execute(
        text("SELECT id FROM documents WHERE id = :document_id"),
        {"document_id": document_id},
    ).mappings().first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    extraction_rows = db.execute(
        text("""
            SELECT id, extractor_name, extractor_version
            FROM extractions
            WHERE document_id = :document_id
            ORDER BY created_at ASC
        """),
        {"document_id": document_id},
    ).mappings().all()

    results = {}

    for row in extraction_rows:
        entity_rows = db.execute(
            text("""
                SELECT entity_type, entity_text, span_start, span_end,
                       confidence, review_status
                FROM entities
                WHERE extraction_id = :extraction_id
            """),
            {"extraction_id": row["id"]},
        ).mappings().all()

        entities = [
            EntityOut(
                entity_type=e["entity_type"],
                entity_text=e["entity_text"],
                span_start=e["span_start"],
                span_end=e["span_end"],
                confidence=e["confidence"],
                review_status=e["review_status"],
            )
            for e in entity_rows
        ]

        results[row["extractor_name"]] = ExtractionMeta(
            extraction_id=row["id"],
            extractor_version=row["extractor_version"],
            entity_count=len(entities),
            entities=entities,
        )

    return ComparisonResponse(document_id=document_id, results=results)