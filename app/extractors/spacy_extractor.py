from typing import List, Optional

import spacy
from spacy.language import Language

from app.extractors.base import BaseExtractor, ExtractedEntity


class SpacyExtractor(BaseExtractor):
    name = "spacy_de"
    version = "v1"

    def __init__(self, model_name: str = "de_core_news_sm") -> None:
        self.model_name = model_name
        self.nlp: Language = spacy.load(model_name)

    def extract(self, text: str) -> List[ExtractedEntity]:
        doc = self.nlp(text)
        entities: List[ExtractedEntity] = []

        for ent in doc.ents:
            mapped_label = self._map_label(ent.label_)

            if mapped_label is None:
                continue

            entities.append(
                ExtractedEntity(
                    entity_type=mapped_label,
                    entity_text=ent.text,
                    span_start=ent.start_char,
                    span_end=ent.end_char,
                    confidence=1.0,
                )
            )

        return entities

    def _map_label(self, label: str) -> Optional[str]:
        label_mapping = {
            "PERSON": "person",
            "PER": "person",
            "ORG": "organization",
            "GPE": "location",
            "LOC": "location",
        }

        return label_mapping.get(label)