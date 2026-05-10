# Computer Vision Flow Architecture

This diagram focuses only on the computer vision extension so it is easy to explain during a short portfolio walkthrough.

```mermaid
flowchart TD
    A[Frontend vision page] --> B[User selects image]
    B --> C[POST /vision/inspect]
    C --> D[Validate MIME type]
    D --> E[Decode image bytes with OpenCV]
    E --> F[Preprocess image]
    F --> G[Threshold + morphology]
    G --> H[Contour detection]
    H --> I[Bounding boxes + confidence]
    I --> J[(vision_inspections)]
    I --> K[(vision_detections)]
    K --> L[Render overlay + review table]
    L --> M[PATCH /vision/detections/{id}/review]
    M --> K
```

## Talking Points

- The pipeline is intentionally classical CV, not a trained detector, so the design stays transparent and easy to demo.
- Bounding boxes are stored with review state, which makes the feature human-in-the-loop rather than fire-and-forget automation.
- The same project now demonstrates both NLP extraction and computer vision review inside one multimodal workspace.
