# EntityFlow

**OCR-first multimodal entity extraction workspace** for turning messy text and image uploads into structured, reviewable entities.

EntityFlow is built as a portfolio-grade full-stack AI project: FastAPI + PostgreSQL on the backend, React + TypeScript on the frontend, deterministic extractors for reliability, optional LLM extraction for recall, and OCR-powered Computer Vision input for image-to-entity workflows.

The core product idea is simple:

```text
text or image -> normalized document -> regex / spaCy / LLM extraction -> human review
```

---

## Why It Matters

Many real documents do not start as clean text. They arrive as screenshots, scans, labels, flyers, business cards, or photos. EntityFlow demonstrates how a multimodal review system can accept both typed text and image input, normalize them into one document model, run multiple extraction strategies, and let a reviewer validate the result.

This is not a toy OCR page bolted onto an NLP app. The OCR output is connected to the same `documents`, `extractions`, and `entities` pipeline used by text uploads.

---

## Current Capabilities

- Upload text manually, from `.txt` / `.md` files, or from images through OCR.
- Extract entities with three complementary strategies: regex, German spaCy NER, and an optional LLM extractor.
- Convert image text into `source_type=image_ocr` documents and run the same extractor pipeline on OCR-derived text.
- Compare extractor outputs side by side for the same document.
- Review entities with `pending`, `approved`, and `rejected` states persisted in PostgreSQL.
- Detect duplicate documents through SHA-256 content hashes.
- Run the full stack with Docker Compose: PostgreSQL, FastAPI, and the React frontend.
- Use a terminal-inspired frontend theme designed to make the OCR workflow feel like a focused engineering tool.
- Validate backend behavior with pytest and frontend type safety with TypeScript builds.

**Extracted entity types:** person, organization, location, title, address, email, phone, url.

---

## Main Workflows

### 1. Text-to-Entity Extraction

1. Create a document from pasted text or an uploaded text file.
2. Run one or more extractors: `regex`, `spacy_de`, or `llm_mini`.
3. Compare extraction results across extractor families.
4. Approve or reject entities in the review UI.

### 2. Image-to-Entity Extraction

1. Upload an image in the OCR workspace.
2. The backend validates and decodes the image.
3. OpenCV preprocessing prepares the image for OCR.
4. Tesseract extracts raw text.
5. The backend normalizes the OCR text and returns OCR metadata.
6. The OCR text can be stored as a document with `source_type=image_ocr`.
7. Regex and spaCy can run immediately on the OCR-derived document.
8. Extracted entities are displayed with search and type filters.

### 3. Human-in-the-Loop Review

Reviewer decisions are stored on the entity rows, so extraction is not treated as a final answer. The UI supports correction-oriented workflows where a human can inspect raw text, hover extracted spans, and approve or reject candidates.

---

## Architecture

```mermaid
flowchart TD
    textInput["Paste text or upload .txt/.md"] --> createDocument["POST /documents"]
    createDocument --> documents[("documents")]
    documents --> runExtraction["POST /documents/:id/extract"]
    runExtraction --> extractors["Regex / spaCy / LLM extractors"]
    extractors --> extractions[("extractions")]
    extractions --> entities[("entities")]
    entities --> reviewUi["Entity comparison and review UI"]
    reviewUi --> reviewEntity["PATCH /entities/:id/review"]
    reviewEntity --> entities

    imageInput["Upload image"] --> ocrEndpoint["POST /vision/ocr"]
    ocrEndpoint --> preprocess["OpenCV OCR preprocessing"]
    preprocess --> tesseract["Tesseract OCR"]
    tesseract --> ocrText["Normalized OCR text"]
    ocrText --> ocrExtract["POST /vision/ocr/extract"]
    ocrExtract --> imageDocument["Create or reuse image_ocr document"]
    imageDocument --> documents
    imageDocument --> extractors
```

**OCR-first note:** `POST /vision/inspect` is kept as a deprecated compatibility route, but it now returns the OCR-first response shape. The main Sprint 5 value proposition no longer depends on contour-based region detection.

---

## Data Model

```text
documents
  id, raw_text, source_type, content_hash, char_count, uploaded_at

extractions
  id, document_id, extractor_name, extractor_version, processing_ms, created_at

entities
  id, extraction_id, entity_type, entity_text, normalized_value,
  confidence, span_start, span_end, review_status

vision_inspections / vision_detections
  Legacy compatibility tables from the earlier visual-inspection prototype.
  The current workflow is OCR-first and uses documents/extractions/entities.
```

---

## Extractor Strategy

| Extractor | Role | Strength | Tradeoff |
|---|---|---|---|
| `RegexExtractor` | Deterministic patterns | High precision for email, phone, URL | Limited semantic understanding |
| `SpacyExtractor` | Classical NER | Good for person, organization, location | Model-dependent and language-sensitive |
| `LlmExtractor` | Structured LLM extraction | Better recall for noisy or complex text | Requires API configuration and network access |
| OCR + extractors | Image-to-entity bridge | Turns screenshots/photos into normal documents | OCR quality depends on image clarity |

Evaluation is intentionally small and reproducible. Metrics are calculated against `data/samples.json`:

```bash
python scripts/evaluate.py
```

The table values in docs should be read as a local benchmark for the included sample set, not as a production accuracy claim.

---

## Tech Stack

| Area | Technologies |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy |
| OCR / Vision | OpenCV, Tesseract OCR |
| NLP | Regex, spaCy `de_core_news_sm`, optional LLM API |
| Database | PostgreSQL |
| Frontend | React, TypeScript, Vite |
| DevOps | Docker, Docker Compose, GitHub Actions CI |
| Testing | pytest, FastAPI TestClient, TypeScript build |

---

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | DB-aware health check |
| `POST` | `/documents` | Create or reuse a text document |
| `GET` | `/documents/{id}` | Fetch raw document text and metadata |
| `POST` | `/documents/{id}/extract?extractor=...` | Run `regex`, `spacy_de`, or `llm_mini` |
| `GET` | `/documents/{id}/extractions` | Compare extractor outputs for one document |
| `PATCH` | `/entities/{id}/review` | Persist `approved` or `rejected` review state |
| `POST` | `/vision/ocr` | Extract readable text from an uploaded image |
| `POST` | `/vision/ocr/extract?extractors=regex,spacy_de` | OCR image, create/reuse document, run extractors |
| `POST` | `/vision/inspect` | Deprecated compatibility alias for OCR-first extraction |

Full Swagger docs are available at:

```text
http://localhost:8000/docs
```

---

## Example Requests

### OCR only

```bash
curl -X POST "http://localhost:8000/vision/ocr" \
  -F "file=@docs/demo-images/sample-product.png"
```

Example response:

```json
{
  "filename": "sample-product.png",
  "image_width": 400,
  "image_height": 300,
  "extracted_text": "Alice Example\nalice@example.com",
  "raw_text": "Alice Example\n\nalice@example.com\n",
  "char_count": 31,
  "is_empty": false,
  "engine": "tesseract"
}
```

### OCR plus entity extraction

```bash
curl -X POST "http://localhost:8000/vision/ocr/extract?extractors=regex,spacy_de" \
  -F "file=@docs/demo-images/sample-product.png"
```

This creates or reuses an `image_ocr` document, runs the selected extractors, and returns grouped entity results.

### Review an entity

```bash
curl -X PATCH "http://localhost:8000/entities/41/review" \
  -H "Content-Type: application/json" \
  -d '{"review_status":"approved"}'
```

---

## Quick Start

```bash
git clone https://github.com/yusufoemerkaratas/entityflow.git
cd entityflow
cp .env.example .env
docker compose up --build
```

Open:

```text
Frontend: http://localhost:5173
API docs: http://localhost:8000/docs
```

The Docker API image installs `tesseract-ocr`, so OCR works inside the container without requiring a local host installation.

---

## Local Development

### Backend

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg2://entityflow:entityflow@localhost:5434/entityflow
uvicorn app.api.main:app --reload
```

For OCR outside Docker, install Tesseract on your machine and make sure `tesseract` is available in `PATH`.

### Frontend

```bash
cd frontend
npm install
export VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

---

## Testing

Backend OCR and extraction tests:

```bash
venv/bin/pytest tests/test_ocr_service.py tests/test_vision_ocr_api.py tests/test_vision_ocr_extraction_api.py tests/test_vision_api.py -q
```

Full backend test suite:

```bash
venv/bin/pytest -q
```

Frontend build/type check:

```bash
npm --prefix frontend run build
```

Manual OCR frontend verification notes are documented in:

```text
docs/ocr-frontend-verification.md
```

---

## Screenshots

### Text Extraction

![Upload Page](docs/screenshots/upload_page.png)

![Extractor Comparison View](docs/screenshots/comparison_view.png)

![Entity Review](docs/screenshots/entity_review.png)

### OCR / Vision Workflow

![Vision Upload](docs/screenshots/vision-upload.png)

![Vision Result](docs/screenshots/vision-result.png)

---

## Project Structure

```text
entityflow/
├── app/
│   ├── api/          # FastAPI routes for documents, extraction, review, OCR
│   ├── db/           # SQLAlchemy engine and PostgreSQL schema
│   ├── extractors/   # Regex, spaCy, and LLM extractor implementations
│   ├── services/     # Shared extraction pipeline orchestration
│   ├── vision/       # OCR service and OpenCV preprocessing utilities
│   └── schemas/      # Pydantic request/response models
├── frontend/         # React + TypeScript frontend
├── tests/            # pytest unit and integration tests
├── data/             # Golden sample set for local extractor evaluation
├── docs/             # Demo scripts, architecture notes, screenshots
└── scripts/          # Evaluation utilities
```

---

## Configuration

Required:

- `DATABASE_URL`

Optional LLM extraction:

- `LLM_API_KEY` or `OPENAI_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL_NAME`

Optional OCR overrides:

- `TESSERACT_CMD`
- `TESSERACT_LANG`

---

## What This Project Demonstrates

- Full-stack product thinking around an end-to-end AI workflow.
- Clean API design with typed request/response schemas.
- OCR integration that feeds the same data model as normal text input.
- Multiple extraction strategies with different precision/recall tradeoffs.
- Human review and persistence instead of one-shot extraction.
- Practical Dockerized development with PostgreSQL, Tesseract, FastAPI, and React.
- Testable backend services and typed frontend integration.

---

## Future Work

- OCR confidence scoring and line-level metadata.
- Better OCR preprocessing presets for scanned documents versus photos.
- Dataset-based OCR evaluation.
- Optional EasyOCR or transformer-based OCR adapter.
- LLM-assisted correction of noisy OCR text.
- Export reviewed entities as CSV or JSON.

---

## Author

**Yusuf Ömer Karataş** — Informatik @ THWS Würzburg  
[LinkedIn](https://www.linkedin.com/in/yusuf-ömer-karatas-330952219) · [yusufoemer.karatas@study.thws.de](mailto:yusufoemer.karatas@study.thws.de)
