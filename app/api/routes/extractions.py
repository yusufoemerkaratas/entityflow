from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.comparison import ComparisonResponse, ExtractionMeta, EntityOut
from app.services.extraction_pipeline import run_extractor_and_persist

router = APIRouter(tags=["extractions"])


@router.post("/documents/{document_id}/extract")
def extract_document(
    document_id: int,
    extractor: str = Query(...),
    db: Session = Depends(get_db),
):
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

    extraction_result = run_extractor_and_persist(
        db=db,
        document_id=document_id,
        raw_text=document_row["raw_text"],
        extractor=extractor,
    )

    db.commit()

    return {
        "document_id": document_id,
        "extraction_id": extraction_result.extraction_id,
        "extractor_name": extraction_result.extractor_name,
        "extractor_version": extraction_result.extractor_version,
        "entity_count": len(extraction_result.entities),
        "entities": [
            {
                "entity_type": entity.entity_type,
                "entity_text": entity.entity_text,
                "span_start": entity.span_start,
                "span_end": entity.span_end,
                "confidence": entity.confidence,
            }
            for entity in extraction_result.entities
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
                SELECT id, entity_type, entity_text, span_start, span_end,
                       confidence, review_status
                FROM entities
                WHERE extraction_id = :extraction_id
            """),
            {"extraction_id": row["id"]},
        ).mappings().all()

        entities = [
            EntityOut(
                id=e["id"],
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
