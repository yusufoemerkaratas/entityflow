from typing import Optional

from pydantic import BaseModel

LlmFieldValue = str | list[str]


class LlmExtractionResult(BaseModel):
    name: Optional[LlmFieldValue] = None
    title: Optional[LlmFieldValue] = None
    company: Optional[LlmFieldValue] = None
    location: Optional[LlmFieldValue] = None
    country: Optional[LlmFieldValue] = None
    email: Optional[LlmFieldValue] = None
    phone: Optional[LlmFieldValue] = None
    domain: Optional[LlmFieldValue] = None
    url: Optional[LlmFieldValue] = None
    ip_like: Optional[LlmFieldValue] = None
    address: Optional[LlmFieldValue] = None
