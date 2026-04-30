from app.extractors.regex_extractor import RegexExtractor


def test_extracts_email_entity():
    extractor = RegexExtractor()
    text = "Contact me at beyza@snapaddy.com"

    entities = extractor.extract(text)

    assert len(entities) == 1
    assert entities[0].entity_type == "email"
    assert entities[0].entity_text == "beyza@snapaddy.com"
    assert entities[0].span_start == text.index("beyza@snapaddy.com")
    assert entities[0].span_end == text.index("beyza@snapaddy.com") + len("beyza@snapaddy.com")
    assert entities[0].confidence == 1.0


def test_extracts_url_entity():
    extractor = RegexExtractor()
    text = "Visit https://snapaddy.com for more information"

    entities = extractor.extract(text)

    assert len(entities) == 1
    assert entities[0].entity_type == "url"
    assert entities[0].entity_text == "https://snapaddy.com"
    assert entities[0].confidence == 1.0


def test_extracts_phone_entity():
    extractor = RegexExtractor()
    text = "Call me at +49 931 1234567 tomorrow"

    entities = extractor.extract(text)

    assert len(entities) == 1
    assert entities[0].entity_type == "phone"
    assert entities[0].entity_text == "+49 931 1234567"
    assert entities[0].confidence == 1.0


def test_extracts_multiple_entities_from_same_text():
    extractor = RegexExtractor()
    text = "Email beyza@snapaddy.com or visit https://snapaddy.com"

    entities = extractor.extract(text)
    entity_types = [entity.entity_type for entity in entities]
    entity_texts = [entity.entity_text for entity in entities]

    assert len(entities) == 2
    assert "email" in entity_types
    assert "url" in entity_types
    assert "beyza@snapaddy.com" in entity_texts
    assert "https://snapaddy.com" in entity_texts


def test_returns_empty_list_when_no_pattern_matches():
    extractor = RegexExtractor()
    text = "This sentence contains no contact data."

    entities = extractor.extract(text)

    assert entities == []