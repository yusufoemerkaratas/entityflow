from app.extractors.llm_extractor import LlmExtractor
from app.schemas.llm_extraction import LlmExtractionResult


def test_build_prompt_contains_expected_fields():
    extractor = LlmExtractor(model_name="test-model")
    text = "Hi, I am Beyza Kara from snapAddy."

    prompt = extractor._build_prompt(text)

    assert "name" in prompt
    assert "title" in prompt
    assert "company" in prompt
    assert "email" in prompt
    assert "phone" in prompt
    assert "address" in prompt
    assert text in prompt


def test_parse_response_handles_plain_json():
    extractor = LlmExtractor(model_name="test-model")
    raw_response = """
    {
        "name": "Beyza Kara",
        "title": "Junior Developer",
        "company": "snapAddy GmbH",
        "email": "beyza@snapaddy.com",
        "phone": null,
        "address": null
    }
    """

    result = extractor._parse_response(raw_response)

    assert isinstance(result, LlmExtractionResult)
    assert result.name == "Beyza Kara"
    assert result.title == "Junior Developer"
    assert result.company == "snapAddy GmbH"
    assert result.email == "beyza@snapaddy.com"
    assert result.phone is None
    assert result.address is None


def test_parse_response_handles_markdown_code_fence():
    extractor = LlmExtractor(model_name="test-model")
    raw_response = """```json
    {
        "name": "Beyza Kara",
        "title": "Junior Developer",
        "company": "snapAddy GmbH",
        "email": "beyza@snapaddy.com",
        "phone": null,
        "address": null
    }
    ```"""

    result = extractor._parse_response(raw_response)

    assert result.name == "Beyza Kara"
    assert result.company == "snapAddy GmbH"
    assert result.email == "beyza@snapaddy.com"


def test_to_entities_maps_schema_fields_correctly():
    extractor = LlmExtractor(model_name="test-model")
    result = LlmExtractionResult(
        name="Beyza Kara",
        title="Junior Developer",
        company="snapAddy GmbH",
        email="beyza@snapaddy.com",
        phone=None,
        address=None,
    )

    entities = extractor._to_entities(result)

    entity_types = [entity.entity_type for entity in entities]
    entity_texts = [entity.entity_text for entity in entities]

    assert "person" in entity_types
    assert "title" in entity_types
    assert "organization" in entity_types
    assert "email" in entity_types

    assert "Beyza Kara" in entity_texts
    assert "Junior Developer" in entity_texts
    assert "snapAddy GmbH" in entity_texts
    assert "beyza@snapaddy.com" in entity_texts


def test_extract_uses_mocked_model_response():
    extractor = LlmExtractor(model_name="test-model")

    def fake_call_model(prompt: str) -> str:
        return """
        {
            "name": "Beyza Kara",
            "title": "Junior Developer",
            "company": "snapAddy GmbH",
            "email": "beyza@snapaddy.com",
            "phone": null,
            "address": null
        }
        """

    extractor._call_model = fake_call_model  # type: ignore[method-assign]

    entities = extractor.extract(
        "Hi, I am Beyza Kara, Junior Developer at snapAddy GmbH. Email: beyza@snapaddy.com"
    )

    entity_types = [entity.entity_type for entity in entities]
    entity_texts = [entity.entity_text for entity in entities]

    assert "person" in entity_types
    assert "title" in entity_types
    assert "organization" in entity_types
    assert "email" in entity_types

    assert "Beyza Kara" in entity_texts
    assert "Junior Developer" in entity_texts
    assert "snapAddy GmbH" in entity_texts
    assert "beyza@snapaddy.com" in entity_texts