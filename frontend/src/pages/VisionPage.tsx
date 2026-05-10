import { type ChangeEvent, useEffect, useRef, useState } from "react"

import { extractVisionText, extractVisionTextAndRunPipeline } from "../api/client"
import type {
  VisionOcrExtractionResponse,
  VisionOcrResponse,
} from "../types"

import "./VisionPage.css"

const ACCEPTED_IMAGE_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/gif",
  "image/bmp",
  "image/tiff",
]

function formatPixels(value: number): string {
  return value.toLocaleString()
}

type VisionPageProps = {
  embedded?: boolean
}

export function VisionPage({ embedded = false }: VisionPageProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const cameraInputRef = useRef<HTMLInputElement>(null)

  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [ocrResult, setOcrResult] = useState<VisionOcrResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [pipelineLoading, setPipelineLoading] = useState(false)
  const [pipelineResult, setPipelineResult] =
    useState<VisionOcrExtractionResponse | null>(null)
  const [entityFilter, setEntityFilter] = useState("all")
  const [entitySearch, setEntitySearch] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null)
      return undefined
    }

    const nextUrl = URL.createObjectURL(file)
    setPreviewUrl(nextUrl)

    return () => {
      URL.revokeObjectURL(nextUrl)
    }
  }, [file])

  function resetOcrState() {
    setOcrResult(null)
    setPipelineResult(null)
    setStatusMessage(null)
    setError(null)
  }

  function selectImage(nextFile: File) {
    if (!ACCEPTED_IMAGE_TYPES.includes(nextFile.type)) {
      setFile(null)
      resetOcrState()
      setError("Please choose a JPG, PNG, WEBP, GIF, BMP, or TIFF image.")
      if (fileInputRef.current) fileInputRef.current.value = ""
      if (cameraInputRef.current) cameraInputRef.current.value = ""
      return
    }

    setFile(nextFile)
    resetOcrState()
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setError(null)
    setStatusMessage(null)

    const nextFile = event.target.files?.[0]
    if (!nextFile) return

    selectImage(nextFile)
  }

  async function handleExtract() {
    if (!file || loading) return

    setLoading(true)
    setError(null)
    setStatusMessage(null)

    try {
      const response = await extractVisionText(file)
      setOcrResult(response)

      if (response.is_empty) {
        setStatusMessage("OCR completed, but no readable text was found.")
      } else {
        setStatusMessage(
          `OCR extracted ${response.char_count.toLocaleString()} characters.`,
        )
      }
    } catch (ocrError) {
      setError(
        ocrError instanceof Error ? ocrError.message : "OCR extraction failed.",
      )
    } finally {
      setLoading(false)
    }
  }

  async function handleRunPipeline(extractors: string) {
    if (!file || pipelineLoading) return

    setPipelineLoading(true)
    setError(null)
    setStatusMessage(null)

    try {
      const response = await extractVisionTextAndRunPipeline(file, extractors)
      setOcrResult(response.ocr)
      setPipelineResult(response)
      setStatusMessage(
        `Pipeline completed on document #${response.document_id} (${response.source_type}).`,
      )
    } catch (pipelineError) {
      setError(
        pipelineError instanceof Error
          ? pipelineError.message
          : "OCR pipeline execution failed.",
      )
    } finally {
      setPipelineLoading(false)
    }
  }

  const allEntities = pipelineResult
    ? Object.entries(pipelineResult.results).flatMap(([extractorName, entities]) =>
        entities.map((entity) => ({ ...entity, extractorName })),
      )
    : []
  const entityTypes = Array.from(new Set(allEntities.map((entity) => entity.entity_type)))
  const filteredEntities = allEntities.filter((entity) => {
    const matchesType = entityFilter === "all" || entity.entity_type === entityFilter
    const query = entitySearch.trim().toLowerCase()
    const matchesSearch =
      query === "" ||
      entity.entity_text.toLowerCase().includes(query) ||
      entity.entity_type.toLowerCase().includes(query) ||
      entity.extractorName.toLowerCase().includes(query)

    return matchesType && matchesSearch
  })

  const content = (
    <>
      <div className="page-header">
        <p className="eyebrow">Computer vision</p>
        <h2>OCR extraction workspace</h2>
        <p>
          Upload an image, run OCR, and inspect the extracted text before
          sending it into the entity extraction workflow.
        </p>
      </div>

      <div className="vision-toolbar">
        <label className="vision-upload-card" htmlFor="vision-file-input">
          <span className="vision-upload-icon">🖼️</span>
          <span className="vision-upload-copy">
            <strong>Choose an image</strong>
            <span>JPG, PNG, WEBP, GIF, BMP, or TIFF</span>
          </span>
        </label>

        <input
          ref={fileInputRef}
          id="vision-file-input"
          type="file"
          accept={ACCEPTED_IMAGE_TYPES.join(",")}
          className="vision-file-input"
          onChange={handleFileChange}
          disabled={loading}
        />
        <input
          ref={cameraInputRef}
          id="vision-camera-input"
          type="file"
          accept="image/*"
          capture="environment"
          className="vision-file-input"
          onChange={handleFileChange}
          disabled={loading || pipelineLoading}
        />

        <div className="vision-toolbar-actions">
          <button
            type="button"
            className="vision-primary-button"
            onClick={handleExtract}
            disabled={!file || loading || pipelineLoading}
          >
            {loading ? "Running OCR…" : "Extract text from image"}
          </button>
          <button
            type="button"
            className="vision-primary-button"
            onClick={() => handleRunPipeline("regex,spacy_de")}
            disabled={!file || loading || pipelineLoading}
          >
            {pipelineLoading ? "Running pipeline…" : "Run OCR + regex + spaCy"}
          </button>
          <label className="vision-secondary-button" htmlFor="vision-camera-input">
            Take photo
          </label>

          <div className="vision-file-meta">
            <strong>{file?.name ?? "No file selected"}</strong>
            <span>
              {file
                ? `${formatPixels(file.size)} bytes`
                : "Select an image to begin."}
            </span>
          </div>
        </div>
      </div>

      {error && (
        <div className="upload-error-banner" role="alert">
          <span className="upload-error-icon">⚠️</span>
          <div>{error}</div>
        </div>
      )}

      {statusMessage && !error && (
        <div className="upload-info-banner" role="status">
          <span className="upload-info-icon">ℹ️</span>
          <div>{statusMessage}</div>
        </div>
      )}

      <div className="vision-layout">
        <section className="vision-preview-panel">
          <header className="vision-panel-header">
            <div>
              <p className="eyebrow">Image preview</p>
              <h3>{ocrResult?.filename ?? file?.name ?? "No image loaded"}</h3>
            </div>

            <span className="vision-panel-chip">
              {ocrResult ? `${ocrResult.char_count} chars` : "Awaiting upload"}
            </span>
          </header>

          {previewUrl ? (
            <div className="vision-stage">
              <img
                className="vision-image"
                src={previewUrl}
                alt={file?.name ?? "Uploaded preview"}
              />
            </div>
          ) : (
            <div className="vision-empty-state">
              <span className="vision-empty-icon">🪟</span>
              <h3>No image selected</h3>
              <p>
                Pick an image on the left to preview it here before running OCR.
              </p>
            </div>
          )}
        </section>

        <aside className="vision-result-panel">
          <header className="vision-panel-header">
            <div>
              <p className="eyebrow">OCR result</p>
              <h3>Extracted text</h3>
            </div>

            <span className="vision-panel-chip vision-panel-chip-backend">
              Ready for NLP
            </span>
          </header>

          {ocrResult ? (
            <div className="vision-ocr-stack">
              <section className="vision-ocr-card">
                <div className="vision-ocr-card-header">
                  <div>
                    <p className="vision-ocr-label">Normalized OCR text</p>
                    <h4>
                      {ocrResult.is_empty ? "No readable text found" : "OCR output"}
                    </h4>
                  </div>

                  <span className="vision-ocr-engine">{ocrResult.engine}</span>
                </div>

                {ocrResult.is_empty ? (
                  <div className="vision-empty-table">
                    <h3>No text extracted</h3>
                    <p>
                      Try a higher-contrast image with clearer printed text,
                      such as an email signature, label, or document crop.
                    </p>
                  </div>
                ) : (
                  <pre className="vision-ocr-text">{ocrResult.extracted_text}</pre>
                )}
              </section>

              <section className="vision-ocr-card">
                <p className="vision-ocr-label">Raw OCR text</p>
                <pre className="vision-ocr-text vision-ocr-text-raw">
                  {ocrResult.raw_text || "No raw OCR output."}
                </pre>
              </section>

              <section className="vision-ocr-note">
                <h4>Next step</h4>
                <p>
                  This OCR output will be the input for the existing entity
                  extraction pipeline.
                </p>
              </section>

              {pipelineResult && (
                <section className="vision-ocr-card">
                  <div className="vision-ocr-card-header">
                    <div>
                      <p className="vision-ocr-label">Entity extraction result</p>
                      <h4>Document #{pipelineResult.document_id}</h4>
                    </div>
                    <span className="vision-panel-chip">
                      {filteredEntities.length} visible
                    </span>
                  </div>

                  <div className="vision-filter-bar">
                    <input
                      className="vision-filter-input"
                      type="search"
                      value={entitySearch}
                      onChange={(event) => setEntitySearch(event.target.value)}
                      placeholder="Search entity text, type, extractor"
                    />
                    <div className="vision-filter-chips" aria-label="Entity filters">
                      <button
                        type="button"
                        className={entityFilter === "all" ? "vision-filter-chip-active" : ""}
                        onClick={() => setEntityFilter("all")}
                      >
                        All
                      </button>
                      {entityTypes.map((type) => (
                        <button
                          key={type}
                          type="button"
                          className={entityFilter === type ? "vision-filter-chip-active" : ""}
                          onClick={() => setEntityFilter(type)}
                        >
                          {type}
                        </button>
                      ))}
                    </div>
                  </div>

                  {filteredEntities.length === 0 ? (
                    <p className="vision-ocr-text">No entities match the current filters.</p>
                  ) : (
                    <div className="vision-entity-grid">
                      {filteredEntities.map((entity, index) => (
                        <article
                          className="vision-entity-card"
                          key={`${entity.extractorName}-${entity.entity_text}-${index}`}
                        >
                          <span>{entity.entity_type}</span>
                          <strong>{entity.entity_text}</strong>
                          <small>{entity.extractorName}</small>
                        </article>
                      ))}
                    </div>
                  )}
                </section>
              )}
            </div>
          ) : (
            <div className="vision-empty-table">
              <h3>No OCR result yet</h3>
              <p>
                Run OCR to populate the extracted text panel and prepare the
                image content for downstream entity extraction.
              </p>
            </div>
          )}
        </aside>
      </div>
    </>
  )

  if (embedded) {
    return <div className="vision-page vision-page-embedded">{content}</div>
  }

  return (
    <section className="page-card vision-page">
      {content}
    </section>
  )
}
