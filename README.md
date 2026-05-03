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