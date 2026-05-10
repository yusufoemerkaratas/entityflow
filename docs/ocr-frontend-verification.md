# OCR Frontend Verification

Manual verification for Sprint 5 frontend OCR upload workflow.

## Scope

- Open the Vision page and upload an image.
- Run OCR from the main action button.
- Confirm extracted OCR text, loading, success, empty, and error states are visible.
- Open the Upload page and switch to Image OCR.
- Confirm the same OCR workflow is available from the unified upload workspace.
- Run OCR + regex + spaCy and confirm entity cards render with search and type filters.
- Confirm the page remains usable on desktop and laptop-sized viewports.

## Type Coverage

The frontend uses TypeScript response types for OCR-only and OCR-to-entity pipeline responses:

- `VisionOcrResponse`
- `VisionOcrExtractionResponse`
- `VisionOcrExtractedEntity`

Build verification:

```bash
npm --prefix frontend run build
```

