from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class ExtractedEntity:
    entity_type: str
    entity_text: str
    span_start: int
    span_end: int
    confidence: float = 1.0


class BaseExtractor(ABC):
    name: str = "base"
    version: str = "v1"

    @abstractmethod
    def extract(self, text: str) -> List[ExtractedEntity]:
        raise NotImplementedError