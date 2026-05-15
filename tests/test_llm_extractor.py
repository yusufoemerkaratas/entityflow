from app.extractors.llm_extractor import LlmExtractor
from app.schemas.llm_extraction import LlmExtractionResult


def test_build_prompt_contains_expected_fields():
    extractor = LlmExtractor(model_name="test-model")
    text = "Hi, I am Beyza Kara from snapAddy."

    prompt = extractor._build_prompt(text)

    assert "name" in prompt
    assert "title" in prompt
    assert "company" in prompt
    assert "location" in prompt
    assert "country" in prompt
    assert "email" in prompt
    assert "phone" in prompt
    assert "domain" in prompt
    assert "url" in prompt
    assert "ip_like" in prompt
    assert "address" in prompt
    assert text in prompt


def test_parse_response_handles_plain_json():
    extractor = LlmExtractor(model_name="test-model")
    raw_response = """
    {
        "name": ["Beyza Kara"],
        "title": ["Junior Developer"],
        "company": ["snapAddy GmbH"],
        "location": ["Berlin"],
        "country": ["Germany"],
        "email": ["beyza@snapaddy.example"],
        "phone": [],
        "domain": ["snapaddy.example"],
        "url": ["https://snapaddy.example"],
        "ip_like": [],
        "address": []
    }
    """

    result = extractor._parse_response(raw_response)

    assert isinstance(result, LlmExtractionResult)
    assert result.name == ["Beyza Kara"]
    assert result.title == ["Junior Developer"]
    assert result.company == ["snapAddy GmbH"]
    assert result.location == ["Berlin"]
    assert result.country == ["Germany"]
    assert result.email == ["beyza@snapaddy.example"]
    assert result.domain == ["snapaddy.example"]
    assert result.url == ["https://snapaddy.example"]
    assert result.phone == []
    assert result.address == []


def test_parse_response_handles_markdown_code_fence():
    extractor = LlmExtractor(model_name="test-model")
    raw_response = """```json
    {
        "name": "Beyza Kara",
        "title": "Junior Developer",
        "company": "snapAddy GmbH",
        "location": null,
        "email": "beyza@snapaddy.com",
        "phone": null,
        "url": null,
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
        company=["snapAddy GmbH", "TechNova GmbH"],
        location="Würzburg",
        country=["Germany"],
        email=["beyza@snapaddy.example", "admin@technova.example"],
        phone=None,
        domain=["snapaddy.example", "technova.example"],
        url="https://snapaddy.example",
        ip_like=["192.0.2.10"],
        address=None,
    )

    entities = extractor._to_entities(result)

    entity_types = [entity.entity_type for entity in entities]
    entity_texts = [entity.entity_text for entity in entities]

    assert "person" in entity_types
    assert "title" in entity_types
    assert "organization" in entity_types
    assert "location" in entity_types
    assert "email" in entity_types
    assert "url" in entity_types
    assert "ip_like" in entity_types

    assert "Beyza Kara" in entity_texts
    assert "Junior Developer" in entity_texts
    assert "snapAddy GmbH" in entity_texts
    assert "TechNova GmbH" in entity_texts
    assert "Würzburg" in entity_texts
    assert "Germany" in entity_texts
    assert "beyza@snapaddy.example" in entity_texts
    assert "admin@technova.example" in entity_texts
    assert "snapaddy.example" in entity_texts
    assert "technova.example" in entity_texts
    assert "https://snapaddy.example" in entity_texts
    assert "192.0.2.10" in entity_texts


def test_extract_uses_mocked_model_response():
    extractor = LlmExtractor(model_name="test-model")

    def fake_call_model(prompt: str) -> str:
        return """
        {
            "name": ["Beyza Kara"],
            "title": ["Junior Developer"],
            "company": ["snapAddy GmbH"],
            "location": ["Würzburg"],
            "country": [],
            "email": ["beyza@snapaddy.example"],
            "phone": [],
            "domain": ["snapaddy.example"],
            "url": ["https://snapaddy.example"],
            "ip_like": [],
            "address": []
        }
        """

    extractor._call_model = fake_call_model  # type: ignore[method-assign]

    entities = extractor.extract(
        "Hi, I am Beyza Kara, Junior Developer at snapAddy GmbH. Email: beyza@snapaddy.example"
    )

    entity_types = [entity.entity_type for entity in entities]
    entity_texts = [entity.entity_text for entity in entities]

    assert "person" in entity_types
    assert "title" in entity_types
    assert "organization" in entity_types
    assert "location" in entity_types
    assert "email" in entity_types
    assert "url" in entity_types

    assert "Beyza Kara" in entity_texts
    assert "Junior Developer" in entity_texts
    assert "snapAddy GmbH" in entity_texts
    assert "Würzburg" in entity_texts
    assert "beyza@snapaddy.example" in entity_texts
    assert "snapaddy.example" in entity_texts
    assert "https://snapaddy.example" in entity_texts


def test_to_entities_handles_mock_contact_lists():
    extractor = LlmExtractor(model_name="test-model")
    result = LlmExtractionResult(
        name=["Lukas Weber", "Anna Schneider"],
        company=["TechNova GmbH", "CloudBridge SE"],
        email=["admin@technova.example", "security@cloudbridge.example"],
        phone=["+49 151 00000001", "+49 152 00000002"],
        domain=["technova.example", "cloudbridge.example"],
        country=["Germany", "Sweden"],
    )

    entity_texts = [entity.entity_text for entity in extractor._to_entities(result)]

    assert "Lukas Weber" in entity_texts
    assert "Anna Schneider" in entity_texts
    assert "TechNova GmbH" in entity_texts
    assert "CloudBridge SE" in entity_texts
    assert "admin@technova.example" in entity_texts
    assert "security@cloudbridge.example" in entity_texts
    assert "+49 151 00000001" in entity_texts
    assert "+49 152 00000002" in entity_texts
    assert "technova.example" in entity_texts
    assert "cloudbridge.example" in entity_texts


def test_extract_adds_literal_mock_contact_values_not_returned_by_model():
    extractor = LlmExtractor(model_name="test-model")

    def fake_call_model(prompt: str) -> str:
        return """
        {
            "name": [],
            "title": [],
            "company": [],
            "location": [],
            "country": [],
            "email": [],
            "phone": [],
            "domain": [],
            "url": [],
            "ip_like": [],
            "address": []
        }
        """

    extractor._call_model = fake_call_model  # type: ignore[method-assign]

    entities = extractor.extract(
        "Email admin@technova.example, phone +49 151 00000001, "
        "domain technova.example, host 192.0.2.10."
    )
    entity_texts = [entity.entity_text for entity in entities]

    assert "admin@technova.example" in entity_texts
    assert "+49 151 00000001" in entity_texts
    assert "technova.example" in entity_texts
    assert "192.0.2.10" in entity_texts
