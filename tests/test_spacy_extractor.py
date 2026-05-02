from app.extractors.spacy_extractor import SpacyExtractor


def test_extracts_person_entity_with_spacy():
    extractor = SpacyExtractor()
    text = "Angela Merkel arbeitet heute in Berlin."

    entities = extractor.extract(text)
    entity_types = [entity.entity_type for entity in entities]
    entity_texts = [entity.entity_text for entity in entities]

    assert "person" in entity_types
    assert "Angela Merkel" in entity_texts


def test_extracts_organization_entity_with_spacy():
    extractor = SpacyExtractor()
    text = "SAP hat seinen Hauptsitz in Deutschland."

    entities = extractor.extract(text)
    entity_types = [entity.entity_type for entity in entities]
    entity_texts = [entity.entity_text for entity in entities]

    assert "organization" in entity_types
    assert "SAP" in entity_texts


def test_extracts_location_entity_with_spacy():
    extractor = SpacyExtractor()
    text = "Angela Merkel arbeitet bei SAP in Berlin."

    entities = extractor.extract(text)
    entity_types = [entity.entity_type for entity in entities]
    entity_texts = [entity.entity_text for entity in entities]

    assert "location" in entity_types
    assert "Berlin" in entity_texts


def test_extracts_multiple_entities_from_same_text_with_spacy():
    extractor = SpacyExtractor()
    text = "Angela Merkel arbeitet bei SAP in Berlin."

    entities = extractor.extract(text)
    entity_types = [entity.entity_type for entity in entities]
    entity_texts = [entity.entity_text for entity in entities]

    assert "person" in entity_types
    assert "organization" in entity_types
    assert "location" in entity_types
    assert "Angela Merkel" in entity_texts
    assert "SAP" in entity_texts
    assert "Berlin" in entity_texts


def test_returns_empty_list_for_text_without_supported_entities():
    extractor = SpacyExtractor()
    text = "und oder aber"

    entities = extractor.extract(text)

    assert entities == []