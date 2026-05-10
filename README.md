# EntityFlow

**Multimodal entity extraction and computer vision review workspace** — converts unstructured text into structured entities and now includes a computer vision mode for image inspection, bounding-box review, and human-in-the-loop validation.

Built as a portfolio project for NLP, multimodal AI, and computer vision roles.

---

## What it does

EntityFlow now covers two linked workflows:

1. Text extraction: upload unstructured text, run regex + spaCy + LLM extractors, compare the outputs side by side, and review the extracted entities.
2. Computer vision inspection: upload an image, run a lightweight visual inspection pipeline, view detected regions on top of the image, and approve or reject each detection.

The review flow is human-in-the-loop in both modes. Text entities and visual detections can be reviewed from the UI, and the choice is stored as `review_status` in the database.

**Extracted entity types:** Person · Organization · Location · Title · Address · Email · Phone · URL

## Computer Vision Mode

The vision mode is designed as a portfolio-ready showcase for internship applications: it demonstrates image upload, classical computer vision preprocessing, region proposal generation, persistence, and human review in one compact workflow. Instead of claiming full production object detection, it intentionally uses a lightweight OpenCV contour pipeline so the system design stays easy to explain in demos and interviews. This also makes its limits explicit: it works best as a transparent inspection demo on high-contrast images, not as a replacement for a trained detector in complex real-world scenes.

Pipeline overview:

1. The frontend uploads an image to `POST /vision/inspect`.
2. The backend validates MIME type and decodes the bytes into an OpenCV image.
3. Preprocessing converts the image to grayscale, smooths noise, thresholds foreground regions, and cleans the mask with morphology.
4. Contour detection proposes candidate regions, scales the bounding boxes back to original coordinates, and assigns heuristic confidence scores.
5. The inspection run and its detections are persisted in PostgreSQL.
6. The frontend renders the image preview, bounding boxes, summary cards, and a review table.
7. Accept/reject actions call `PATCH /vision/detections/{id}/review` and persist the new review state.

---

## Extraction Layers

| Extractor | Approach | Precision | Recall | Notes |
|---|---|---|---|---|
| **RegexExtractor** | Pattern matching | ~1.00 | ~0.60 | Fast, deterministic. Strong for email/phone/URL, rigid for variations. |
| **SpaCyExtractor** | Classical NER (de_core_news_sm) | ~0.80 | ~0.75 | Good general coverage for PERSON and ORG. |
| **LlmExtractor** | LLM API with structured prompt | ~0.90 | ~0.95 | Best recall for complex titles and company names. |

> Metrics measured against a static golden set of 10 manually verified samples.  
> The evaluation compares extractor outputs against hand-checked reference entities in `data/samples.json`, so the table is intended as a small reproducible benchmark rather than a broad production claim.  
> Run `python scripts/evaluate.py` to see live metrics on your local `data/samples.json`.

---

## Tech Stack

| Area | Technologies |
|---|---|
| **Backend** | Python · FastAPI · SQLAlchemy |
| **NLP** | spaCy · Regex · LLM API |
| **Database** | PostgreSQL |
| **Frontend** | React · TypeScript · Vite |
| **DevOps** | Docker · Docker Compose · GitHub Actions CI |
| **Testing** | pytest · httpx |

---

## Architecture

```mermaid
flowchart TD
    A[Text upload] --> B[POST /documents]
    B --> C[Regex / spaCy / LLM extractors]
    C --> D[GET /documents/{id}/extractions]
    D --> E[Entity review UI]

    F[Image upload] --> G[POST /vision/inspect]
    G --> H[OpenCV contour detection]
    H --> I[(vision_inspections)]
    H --> J[(vision_detections)]
    J --> K[Visual review UI]
    K --> L[PATCH /vision/detections/{id}/review]
    L --> J
```

**Database schema:**

```
documents          — raw text, content_hash (UNIQUE), metadata
extractions        — document_id, extractor_name, processing_ms
entities           — extraction_id, entity_type, entity_text, span_start, span_end, confidence, review_status
vision_inspections — filename, image_width, image_height
vision_detections  — inspection_id, label, confidence, bbox_x, bbox_y, bbox_width, bbox_height, review_status
```

---

## Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/documents` | Upload text, returns id + duplicate flag |
| `POST` | `/documents/{id}/extract` | Run extractor (`?extractor=regex\|spacy_de\|llm_mini`) |
| `GET` | `/documents/{id}/extractions` | All extractor results in one response |
| `PATCH` | `/entities/{id}/review` | Persist a text entity review state |
| `POST` | `/vision/inspect` | Upload an image, persist inspection + detections |
| `PATCH` | `/vision/detections/{id}/review` | Persist a visual detection review state |
| `GET` | `/health` | DB-aware health check |

### Example Vision Request

```bash
curl -X POST "http://localhost:8000/vision/inspect" \
    -F "file=@docs/demo-images/sample-product.png"
```

### Example Detection Review Request

```bash
curl -X PATCH "http://localhost:8000/vision/detections/41/review" \
    -H "Content-Type: application/json" \
    -d '{"review_status":"accepted"}'
```

### Example Vision JSON Response

```json
{
    "inspection_id": 12,
    "filename": "sample-product.png",
    "image_width": 400,
    "image_height": 300,
    "detections": [
        {
            "id": 41,
            "label": "visual_defect_candidate",
            "confidence": 0.95,
            "bbox": { "x": 118, "y": 78, "width": 145, "height": 85 },
            "review_status": "pending"
        }
    ]
}
```

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

### Text Extraction Mode

- **Upload Page**
![Upload Page](docs/screenshots/upload_page.png)

- **Extractor Comparison View**
![Extractor Comparison View](docs/screenshots/comparison_view.png)

- **Entity Review in Action**
![Entity Review](docs/screenshots/entity_review.png)

### Computer Vision Mode

- **Vision Upload**
![Vision Upload](docs/screenshots/vision-upload.png)

- **Vision Inspection Result**
![Vision Result](docs/screenshots/vision-result.png)

## Demo Images

The vision mode demo uses sample images:
- [Sample Product](docs/demo-images/sample-product.png)
- [Sample Product Variant](docs/demo-images/sample-product-variant.png)

## Local Demo

To try the computer vision workflow locally, see [docs/cv-demo-script.md](docs/cv-demo-script.md) for step-by-step instructions.
For a CV-only architecture view, see [docs/cv-architecture.md](docs/cv-architecture.md).

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
export VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

The frontend does not define a Vite proxy in this repository, so setting `VITE_API_BASE_URL` keeps API requests pointed at the FastAPI server during local development.

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
│   ├── vision/       # OpenCV preprocessing + inspection pipeline
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

## Future Work

- OCR support
- YOLO/object detection
- Defect classification model
- Dataset-based evaluation

---

## Author

**Yusuf Ömer Karataş** — Informatik @ THWS Würzburg  
[LinkedIn](https://www.linkedin.com/in/yusuf-ömer-karatas-330952219) · [yusufoemer.karatas@study.thws.de](mailto:yusufoemer.karatas@study.thws.de)
