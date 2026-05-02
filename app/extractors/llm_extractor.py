import json
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
        prompt = self._build_prompt(text)
        raw_response = self._call_model(prompt)
        parsed_result = self._parse_response(raw_response)
        return self._to_entities(parsed_result)

    def _build_prompt(self, text: str) -> str:
        return f"""
You are an information extraction system.

Extract the following fields from the input text:
- name
- title
- company
- email
- phone
- address

Rules:
- Return ONLY valid JSON.
- Use null for missing values.
- Do not invent facts.
- Keep extracted values exactly as they appear in the text when possible.

Expected JSON format:
{{
  "name": null,
  "title": null,
  "company": null,
  "email": null,
  "phone": null,
  "address": null
}}

Input text:
{text}
""".strip()

    def _call_model(self, prompt: str) -> str:
        raise NotImplementedError(
            "LLM provider integration will be added in the next commit."
        )

    def _parse_response(self, raw_response: str) -> LlmExtractionResult:
        data = json.loads(raw_response)
        return LlmExtractionResult.model_validate(data)

    def _to_entities(self, result: LlmExtractionResult) -> List[ExtractedEntity]:
        entities: List[ExtractedEntity] = []

        field_mapping = {
            "name": "person",
            "title": "title",
            "company": "organization",
            "email": "email",
            "phone": "phone",
            "address": "address",
        }

        for field_name, entity_type in field_mapping.items():
            value = getattr(result, field_name)

            if value is None or value.strip() == "":
                continue

            entities.append(
                ExtractedEntity(
                    entity_type=entity_type,
                    entity_text=value,
                    span_start=-1,
                    span_end=-1,
                    confidence=1.0,
                )
            )

        return entities