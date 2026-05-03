from typing import Dict, List, Optional
from pydantic import BaseModel


class EntityOut(BaseModel):
    id: int
    entity_type: str
    entity_text: str
    span_start: Optional[int] = None
    span_end: Optional[int] = None
    confidence: Optional[float] = None
    review_status: str


class ExtractionMeta(BaseModel):
    extraction_id: int
    extractor_version: str
    entity_count: int
    entities: List[EntityOut]


class ComparisonResponse(BaseModel):
    document_id: int
    results: Dict[str, ExtractionMeta]