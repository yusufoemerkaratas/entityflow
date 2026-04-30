import re
from typing import List

from app.extractors.base import BaseExtractor, ExtractedEntity


class RegexExtractor(BaseExtractor):
    name = "regex"
    version = "v1"

    EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    
    PHONE_PATTERN = re.compile(r"(\+49|0)[\s\-]?\d{2,4}[\s\-]?\d{6,9}")
    
    URL_PATTERN = re.compile(r"https?://[^\s]+")

    def extract(self, text: str) -> List[ExtractedEntity]:
        entities: List[ExtractedEntity] = []

        entities.extend(self._extract_with_pattern(text, self.EMAIL_PATTERN, "email"))
        entities.extend(self._extract_with_pattern(text, self.PHONE_PATTERN, "phone"))
        entities.extend(self._extract_with_pattern(text, self.URL_PATTERN, "url"))

        return entities

    def _extract_with_pattern(self, text: str, pattern: re.Pattern, entity_type: str) -> List[ExtractedEntity]:
        matches: List[ExtractedEntity] = []

        for match in pattern.finditer(text):
            matches.append(
                ExtractedEntity(
                    entity_type=entity_type,
                    entity_text=match.group(0),
                    span_start=match.start(),
                    span_end=match.end(),
                    confidence=1.0,
                )
            )

        return matches