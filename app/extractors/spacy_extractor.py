from typing import List

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
        return []