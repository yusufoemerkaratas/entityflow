import os
from typing import List

from app.extractors.base import BaseExtractor, ExtractedEntity
from app.schemas.llm_extraction import LlmExtractionResult


class LlmExtractor(BaseExtractor):
    name = "llm_mini"
    version = "v1"

    def __init__(self, model_name: str | None = None) -> None:
        self.api_key = os.getenv("LLM_API_KEY")
        self.model_name = model_name or os.getenv("LLM_MODEL_NAME", "llm-mini")

    def extract(self, text: str) -> List[ExtractedEntity]:
        return []