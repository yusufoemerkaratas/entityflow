# Computer Vision Mode — Local Demo

This guide walks you through the visual inspection feature end-to-end so you can use it as a short portfolio demo during interviews or internship applications.

## Prerequisites

- Docker and Docker Compose installed
- Terminal access from the project root

## Quick Start

### 1. Start the stack

```bash
docker compose up --build
```

Wait for the services to be healthy:
- API should be at `http://localhost:8000/docs` (Swagger UI)
- Frontend should be at `http://localhost:5173`

### 2. Navigate to Vision Mode

Open your browser to:
```
http://localhost:5173/vision
```

You should see:
- **Title**: "Visual inspection workspace"
- **Upload card** on the left with a file picker
- **Inspection button** (disabled until you pick an image)
- **Summary cards** showing Image size, Detections count, Pending/Accepted/Rejected review states
- **Empty preview** on the right (no image loaded yet)
- **Detection review panel** (empty until inspection runs)

### 3. Upload a Demo Image

Click the upload card and select one of the sample images from `docs/demo-images/`:
- `sample-product.png` — A simple product mockup
- `sample-product-variant.png` — An alternative variant

The UI should update to show:
- File name and size below the upload card
- The image preview on the right side

### 4. Run Visual Inspection

Click the **"Run visual inspection"** button.

The backend will:
1. Receive the image via `POST /vision/inspect`
2. Validate the MIME type and decode the uploaded bytes with OpenCV
3. Preprocess it with grayscale conversion, blur, thresholding, and morphology
4. Detect contours and convert them into bounding boxes
5. Calculate heuristic confidence scores for each region
6. Persist the inspection and detections to PostgreSQL
7. Return the results as JSON

The UI will update to show:
- **Detection count** in the summary cards
- **Image preview with bounding boxes** (if detections found)
- **Detection review table** with label, confidence, box coordinates, and status

### 5. Review a Detection

If the inspection found any visual regions (detections):

1. **Select a detection** by clicking on a bounding box in the image or a row in the table
2. The **Detection Review panel** on the right will populate with:
   - Detection label
   - Confidence score (%)
   - Bounding box coordinates (x, y)
   - Bounding box size (width × height)
   - Box area in pixels

3. Click **"Approve"** or **"Reject"** to persist your review
   - The review is saved immediately to the backend via `PATCH /vision/detections/{id}/review`
   - The button will show a brief "Saving..." state
   - The status badge in the table updates to reflect your choice

### 6. Try Another Image

Upload another image (the variant or your own) and repeat steps 4–5 to see how the pipeline handles different visual features.

---

## API Reference

### Inspect an image

```bash
curl -X POST "http://localhost:8000/vision/inspect" \
  -F "file=@docs/demo-images/sample-product.png"
```

**Response:**
```json
{
  "inspection_id": 1,
  "filename": "sample-product.png",
  "image_width": 400,
  "image_height": 300,
  "detections": [
    {
      "id": 10,
      "label": "visual_defect_candidate",
      "confidence": 0.87,
      "bbox": {
        "x": 100,
        "y": 50,
        "width": 200,
        "height": 150
      },
      "review_status": "pending"
    }
  ]
}
```

### Review a detection

```bash
curl -X PATCH "http://localhost:8000/vision/detections/10/review" \
  -H "Content-Type: application/json" \
  -d '{"review_status":"accepted"}'
```

This endpoint returns the updated detection object with the new `review_status`.

---

## Database Schema

Inspections and detections are stored in PostgreSQL:

```sql
-- Inspection run metadata
vision_inspections (
  id, filename, image_width, image_height, created_at
)

-- Individual detected regions
vision_detections (
  id, inspection_id, label, confidence,
  bbox_x, bbox_y, bbox_width, bbox_height,
  review_status, updated_at
)
```

---

## Troubleshooting

**No detections found?**
- The contour-detection pipeline is heuristic-based and works best on images with clear contrast and defined shapes.
- Try images with darker regions, strong edges, or distinct visual features.

**Backend API returns 404?**
- Make sure the API is running: `curl http://localhost:8000/health`
- Check the logs: `docker compose logs api`

**Frontend shows "Cannot reach backend"?**
- Verify both frontend and API are running.
- For local dev, use `VITE_API_BASE_URL=http://localhost:8000 npm --prefix frontend run dev`

---

## Next Steps

After exploring the vision mode:
1. Check the text extraction workflow: `http://localhost:5173/upload`
2. Review the architecture: see `docs/cv-architecture.md`
3. Explore the code: `app/api/vision.py`, `app/vision/inspection.py`
