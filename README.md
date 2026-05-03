# EntityFlow

**NLP-based entity extraction pipeline** — converts unstructured text into structured entities using a multi-layer approach: regex baseline → spaCy NER → LLM fallback.

Built as a portfolio project targeting NLP/data extraction roles (snapAddy, Heidelberg area).

---

## What it does

Upload any unstructured text → EntityFlow runs it through three extraction layers → results are compared side by side → human reviewer confirms or rejects entities.

**Extracted entity types:** Person · Organization · Location · Email · Phone · URL

---

## Extraction Layers

| Extractor | Approach | Precision | Recall | Notes |
|---|---|---|---|---|
| **RegexExtractor** | Pattern matching | ~1.00 | ~0.60 | Fast, deterministic. Strong for email/phone/URL, rigid for variations. |
| **SpaCyExtractor** | Classical NER (en_core_web_sm) | ~0.80 | ~0.75 | Good general coverage for PERSON and ORG. |
| **LlmExtractor** | LLM API with structured prompt | ~0.90 | ~0.95 | Best recall for complex titles and company names. |

> Metrics measured against a static golden set of 10 manually verified samples.  
> Run `python scripts/evaluate.py` to see live metrics on your local `data/samples.json`.

---

## Tech Stack

| Area | Technologies |
|---|---|
| **Backend** | Python · FastAPI · SQLAlchemy · Alembic |
| **NLP** | spaCy · Regex · LLM API (OpenAI-compatible) |
| **Database** | PostgreSQL (with JSONB) |
| **Frontend** | React · TypeScript · Vite |
| **DevOps** | Docker · Docker Compose · GitHub Actions CI |
| **Testing** | pytest · httpx |

---

## Architecture

```
Text Input
    ↓
POST /documents          — upload text, SHA-256 deduplication
    ↓
POST /documents/{id}/extract?extractor=regex|spacy|llm
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
| `POST` | `/documents/{id}/extract` | Run extractor (`?extractor=regex\|spacy\|llm`) |
| `GET` | `/documents/{id}/extractions` | All extractor results in one response |
| `PATCH` | `/entities/{id}/review` | Accept or reject an entity |
| `GET` | `/health` | DB-aware health check |

Full docs at `http://localhost:8000/docs` (Swagger UI).

---

## Quick Start

```bash
git clone https://github.com/yusufoemerkaratas/entityflow.git
cd entityflow
cp .env.example .env      # fill in DB credentials and API key
docker compose up --build
```

App runs at `http://localhost:5173` · API at `http://localhost:8000/docs`

---

## Project Structure

```
entityflow/
├── app/
│   ├── api/          # FastAPI routes
│   ├── db/           # SQLAlchemy models, schema, migrations
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
