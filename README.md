# EntityFlow

**NLP-based entity extraction pipeline** — converts unstructured text into structured entities using a multi-layer approach: regex baseline → spaCy NER → LLM fallback.


---

## What it does

Upload any unstructured text → EntityFlow runs it through three extraction layers → results are compared side by side → human reviewer confirms or rejects entities.

The review step is intentionally lightweight: each extracted entity can be approved or rejected from the UI, and the choice is stored as `review_status` in the database. This keeps the workflow human-in-the-loop without turning the app into a full annotation platform.

**Extracted entity types:** Person · Organization · Location · Title · Address · Email · Phone · URL

---

## Extraction Layers

| Extractor | Approach | Precision | Recall | Notes |
|---|---|---|---|---|
| **RegexExtractor** | Pattern matching | ~1.00 | ~0.60 | Fast, deterministic. Strong for email/phone/URL, rigid for variations. |
| **SpaCyExtractor** | Classical NER (de_core_news_sm) | ~0.80 | ~0.75 | Good general coverage for PERSON and ORG. |
| **LlmExtractor** | LLM API with structured prompt | ~0.90 | ~0.95 | Best recall for complex titles and company names. |

> Metrics measured against a static golden set of 10 manually verified samples.  
> Run `python scripts/evaluate.py` to see live metrics on your local `data/samples.json`.

---

## Tech Stack

| Area | Technologies |
|---|---|
| **Backend** | Python · FastAPI · SQLAlchemy |
| **NLP** | spaCy · Regex · LLM API |
| **Database** | PostgreSQL |
| **Frontend** | React · TypeScript · Vite |
| **DevOps** | Docker · Docker Compose |
| **Testing** | pytest · httpx |

---

## Architecture

```
Text Input
    ↓
POST /documents          — upload text, SHA-256 deduplication
    ↓
POST /documents/{id}/extract?extractor=regex|spacy_de|llm_mini
    ↓
GET  /documents/{id}/extractions   — all extractor results in one response
    ↓
Review UI               — human confirms / rejects entities
```

**Database schema:**

```
documents       — raw text, content_hash (UNIQUE), metadata
extractions     — document_id, extractor_name, processing_ms
entities        — extraction_id, entity_type, entity_text, span_start, span_end, confidence, review_status
```

---

## Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/documents` | Upload text, returns id + duplicate flag |
| `POST` | `/documents/{id}/extract` | Run extractor (`?extractor=regex\|spacy_de\|llm_mini`) |
| `GET` | `/documents/{id}/extractions` | All extractor results in one response |
| `PATCH` | `/entities/{id}/review` | Accept or reject an entity |
| `GET` | `/health` | DB-aware health check |

Full docs at `http://localhost:8000/docs` (Swagger UI).

---

## Quick Start

```bash
git clone https://github.com/yusufoemerkaratas/entityflow.git
cd entityflow
cp .env.example .env      
docker compose up --build
```

App runs at `http://localhost:5173` · API at `http://localhost:8000/docs`

---

## Screenshots

Add 1-2 screenshots that show the upload flow and the extraction comparison view.

- Upload page
- Comparison / review page

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

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Configuration

Create a `.env` file based on `.env.example`.

Required for DB:
- `DATABASE_URL`

Optional for LLM extraction:
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL_NAME`

---

## Project Structure

```
entityflow/
├── app/
│   ├── api/          # FastAPI routes
│   ├── db/           # Database connection + schema
│   ├── extractors/   # RegexExtractor, SpaCyExtractor, LlmExtractor
│   └── schemas/      # Pydantic models
├── frontend/         # React + TypeScript UI
├── tests/            # pytest unit + integration tests
├── data/             # Golden set samples for evaluation
├── docs/             # Schema docs, architecture notes
└── scripts/          # evaluate.py, seed scripts
```

---

## Development Workflow

This project follows a GitHub issue → branch → PR workflow.  
Each feature was developed in its own branch and merged via pull request.

Labels used: `setup` · `backend` · `nlp` · `frontend` · `evaluation` · `devops` · `docs`

---

## Author

**Yusuf Ömer Karataş** — Informatik @ THWS Würzburg  
[LinkedIn](https://www.linkedin.com/in/yusuf-ömer-karatas-330952219) · [yusufoemerkaratas@study.thws.de](mailto:yusufoemerkaratas@study.thws.de)
