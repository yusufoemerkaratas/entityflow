from __future__ import annotations

from dataclasses import dataclass
from typing import List

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.extractors.base import BaseExtractor
from app.extractors.llm_extractor import LlmExtractor
from app.extractors.regex_extractor import RegexExtractor
from app.extractors.spacy_extractor import SpacyExtractor


@dataclass(frozen=True)
class PersistedExtractionResult:
    extraction_id: int
    extractor_name: str
    extractor_version: str
    entities: list


def resolve_extractor(extractor: str) -> BaseExtractor:
    if extractor == "regex":
        return RegexExtractor()
    if extractor == "spacy_de":
        return SpacyExtractor()
    if extractor == "llm_mini":
        return LlmExtractor()

    raise HTTPException(
        status_code=400,
        detail="Supported extractors are 'regex', 'spacy_de', and 'llm_mini'.",
    )


def run_extractor_and_persist(
    *,
    db: Session,
    document_id: int,
    raw_text: str,
    extractor: str,
) -> PersistedExtractionResult:
    selected_extractor = resolve_extractor(extractor)
    extracted_entities = selected_extractor.extract(raw_text)

    extraction_row = db.execute(
        text(
            """
            INSERT INTO extractions (document_id, extractor_name, extractor_version, processing_ms)
            VALUES (:document_id, :extractor_name, :extractor_version, :processing_ms)
            RETURNING id, extractor_name, extractor_version
            """
        ),
        {
            "document_id": document_id,
            "extractor_name": selected_extractor.name,
            "extractor_version": selected_extractor.version,
            "processing_ms": 0,
        },
    ).mappings().first()

    for entity in extracted_entities:
        db.execute(
            text(
                """
                INSERT INTO entities (
                    extraction_id,
                    entity_type,
                    entity_text,
                    normalized_value,
                    confidence,
                    span_start,
                    span_end
                )
                VALUES (
                    :extraction_id,
                    :entity_type,
                    :entity_text,
                    :normalized_value,
                    :confidence,
                    :span_start,
                    :span_end
                )
                """
            ),
            {
                "extraction_id": extraction_row["id"],
                "entity_type": entity.entity_type,
                "entity_text": entity.entity_text,
                "normalized_value": entity.entity_text,
                "confidence": entity.confidence,
                "span_start": entity.span_start,
                "span_end": entity.span_end,
            },
        )

    return PersistedExtractionResult(
        extraction_id=extraction_row["id"],
        extractor_name=extraction_row["extractor_name"],
        extractor_version=extraction_row["extractor_version"],
        entities=extracted_entities,
    )


def parse_extractors(extractors: str) -> List[str]:
    parsed = [item.strip() for item in extractors.split(",") if item.strip()]
    if not parsed:
        raise HTTPException(status_code=400, detail="At least one extractor is required.")

    # De-duplicate while preserving order.
    return list(dict.fromkeys(parsed))
