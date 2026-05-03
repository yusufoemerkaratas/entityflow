# EntityFlow

EntityFlow is a full-stack information extraction project that converts unstructured text into structured entities such as person, company, email, phone, and location.

## Tech Stack
- Python
- FastAPI
- PostgreSQL
- React
- Docker

## Project Structure
- `app/` backend source code
- `tests/` test files
- `frontend/` React frontend
- `docs/` documentation
- `data/` sample and evaluation data

## API Endpoints

### GET /documents/{id}/extractions
Returns all extractor results for a document in a single response.
Extractors that have not been run will not appear in the response.
If no extractions exist for the document, `results` returns an empty dict `{}`.

Response structure: `results` is a dict where the key is the extractor name and the value is the entity list for that extractor.


## System Evaluation (Mini Golden Set)

To ensure the reliability of the extraction layer, the system includes a lightweight evaluation script (`scripts/evaluate.py`). It measures the **Precision** and **Recall** of each extractor against a static golden set of 5-10 manually verified text samples.

| Extractor | Precision | Recall | Notes |
| :--- | :---: | :---: | :--- |
| **RegexExtractor** | ~1.00 | ~0.60 | High accuracy for exact patterns (Email, Phone), but rigid and misses variations. |
| **SpacyExtractor** | ~0.80 | ~0.75 | Good general coverage for PERSON and ORG, occasionally captures incorrect spans. |
| **LlmExtractor** | ~0.90 | ~0.95 | Deep contextual understanding. Best recall for complex titles and company names. |

> **Note:** The exact metrics above may vary depending on the local sample set. Run `python scripts/evaluate.py` to see the live metrics based on your current `data/samples.json`.