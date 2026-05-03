from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.comparison import EntityOut
from app.schemas.entity_review import EntityReviewRequest

router = APIRouter(prefix="/entities", tags=["entities"])


@router.patch("/{entity_id}/review", response_model=EntityOut)
def review_entity(
    entity_id: int,
    payload: EntityReviewRequest,
    db: Session = Depends(get_db),
):
    row = db.execute(
        text(
            """
            UPDATE entities
            SET review_status = :review_status
            WHERE id = :entity_id
            RETURNING id, entity_type, entity_text, span_start, span_end,
                      confidence, review_status
            """
        ),
        {"review_status": payload.review_status, "entity_id": entity_id},
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Entity not found.")

    db.commit()

    return EntityOut(
        id=row["id"],
        entity_type=row["entity_type"],
        entity_text=row["entity_text"],
        span_start=row["span_start"],
        span_end=row["span_end"],
        confidence=row["confidence"],
        review_status=row["review_status"],
    )