import json
import os
import urllib.error
import urllib.request
from typing import List

from dotenv import load_dotenv

from app.extractors.base import BaseExtractor, ExtractedEntity
from app.schemas.llm_extraction import LlmExtractionResult
 
load_dotenv()
# dotenv already loaded if available


class LlmExtractor(BaseExtractor):
    name = "llm_mini"
    version = "v1"

    def __init__(self, model_name: str | None = None) -> None:
             self.api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
             self.base_url = os.getenv("LLM_BASE_URL", "https://models.inference.ai.azure.com/chat/completions")
             self.model_name = model_name or os.getenv("LLM_MODEL_NAME","gpt-4o-mini")

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
        
        if not self.api_key:
            raise ValueError("LLM_API_KEY is not set.")

        if not self.base_url:
            raise ValueError("LLM_BASE_URL is not set.")

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a precise information extraction system. Return JSON only.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0,
        }

        request = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                 "Accept": "application/vnd.github+json",
                 "Authorization": f"Bearer {self.api_key}",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                response_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(
                f"LLM request failed with status {exc.code}: {error_body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"LLM request failed: {exc.reason}") from exc

        response_data = json.loads(response_body)
        return response_data["choices"][0]["message"]["content"]

    def _parse_response(self, raw_response: str) -> LlmExtractionResult:
        cleaned_response = raw_response.strip()

        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response.removeprefix("```json").removesuffix("```").strip()
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response.removeprefix("```").removesuffix("```").strip()

        data = json.loads(cleaned_response)
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