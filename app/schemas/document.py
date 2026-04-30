from datetime import datetime

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    text: str = Field(..., min_length=10, max_length=100000)
    source_type: str = Field(default="manual", min_length=1, max_length=50)


class DocumentResponse(BaseModel):
    id: int
    char_count: int
    content_hash: str
    is_duplicate: bool
    uploaded_at: datetime