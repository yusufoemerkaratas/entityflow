import { type ChangeEvent, useEffect, useMemo, useRef, useState } from "react"

import { inspectVisionImage, patchVisionDetectionReview } from "../api/client"
import type {
  VisionDetectionWithId,
  VisionInspectionResponse,
  VisionReviewStatus,
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

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`
}

function formatPixels(value: number): string {
  return value.toLocaleString()
}

export function VisionPage() {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [inspection, setInspection] = useState<VisionInspectionResponse | null>(null)
  const [detections, setDetections] = useState<VisionDetectionWithId[]>([])
  const [selectedDetectionId, setSelectedDetectionId] = useState<number | null>(null)
  const [pendingReviewIds, setPendingReviewIds] = useState<Set<number>>(
    () => new Set(),
  )
  const [loading, setLoading] = useState(false)
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

  const activeDetection = useMemo(
    () =>
      detections.find((detection) => detection.id === selectedDetectionId) ??
      detections[0] ??
      null,
    [detections, selectedDetectionId],
  )

  const summaryCards = useMemo(() => {
    const pending = detections.filter(
      (detection) => detection.review_status === "pending",
    ).length
    const accepted = detections.filter(
      (detection) => detection.review_status === "accepted",
    ).length
    const rejected = detections.filter(
      (detection) => detection.review_status === "rejected",
    ).length

    return [
      { label: "Pending", count: pending, className: "vision-stat-pending" },
      { label: "Accepted", count: accepted, className: "vision-stat-accepted" },
      { label: "Rejected", count: rejected, className: "vision-stat-rejected" },
    ]
  }, [detections])

  function resetInspectionState() {
    setInspection(null)
    setDetections([])
    setSelectedDetectionId(null)
    setPendingReviewIds(new Set())
    setStatusMessage(null)
    setError(null)
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setError(null)
    setStatusMessage(null)

    const nextFile = event.target.files?.[0]
    if (!nextFile) return

    if (!ACCEPTED_IMAGE_TYPES.includes(nextFile.type)) {
      setFile(null)
      resetInspectionState()
      setError("Please choose a JPG, PNG, WEBP, GIF, BMP, or TIFF image.")
      if (fileInputRef.current) fileInputRef.current.value = ""
      return
    }

    setFile(nextFile)
    resetInspectionState()
  }

  async function handleInspect() {
    if (!file || loading) return

    setLoading(true)
    setError(null)
    setStatusMessage(null)

    try {
      const response = await inspectVisionImage(file)
      const nextDetections = response.detections

      setInspection(response)
      setDetections(nextDetections)
      setSelectedDetectionId(nextDetections[0]?.id ?? null)

      if (nextDetections.length === 0) {
        setStatusMessage("No visual detections were found in this image.")
      } else {
        setStatusMessage(
          `Found ${nextDetections.length} detection${
            nextDetections.length === 1 ? "" : "s"
          }.`,
        )
      }
    } catch (inspectionError) {
      setError(
        inspectionError instanceof Error
          ? inspectionError.message
          : "Visual inspection failed.",
      )
    } finally {
      setLoading(false)
    }
  }

  async function updateDetectionStatus(
    detectionId: number,
    reviewStatus: VisionReviewStatus,
  ) {
    const previousDetections = detections

    setPendingReviewIds((current) => new Set(current).add(detectionId))
    setSelectedDetectionId(detectionId)
    setError(null)

    setDetections((current) =>
      current.map((detection) =>
        detection.id === detectionId
          ? { ...detection, review_status: reviewStatus }
          : detection,
      ),
    )

    try {
      const updatedDetection = await patchVisionDetectionReview(
        detectionId,
        reviewStatus,
      )

      setDetections((current) =>
        current.map((detection) =>
          detection.id === detectionId ? updatedDetection : detection,
        ),
      )
      setStatusMessage(`Saved detection as ${updatedDetection.review_status}.`)
    } catch (reviewError) {
      setDetections(previousDetections)
      setStatusMessage(null)
      setError(
        reviewError instanceof Error
          ? reviewError.message
          : "Failed to save detection review.",
      )
    } finally {
      setPendingReviewIds((current) => {
        const next = new Set(current)
        next.delete(detectionId)
        return next
      })
    }
  }

  function selectDetection(detectionId: number) {
    setSelectedDetectionId(detectionId)
  }

  function isReviewingDetection(detectionId: number): boolean {
    return pendingReviewIds.has(detectionId)
  }

  const imageWidth = inspection?.image_width ?? 1
  const imageHeight = inspection?.image_height ?? 1

  return (
    <section className="page-card vision-page">
      <div className="page-header">
        <p className="eyebrow">Computer vision</p>
        <h2>Visual inspection workspace</h2>
        <p>
          Upload an image, run inspection, and review the detected regions
          directly on top of the preview.
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

        <div className="vision-toolbar-actions">
          <button
            type="button"
            className="vision-primary-button"
            onClick={handleInspect}
            disabled={!file || loading}
          >
            {loading ? "Inspecting…" : "Run visual inspection"}
          </button>

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

      <div className="vision-summary-grid">
        <article className="vision-summary-card">
          <span>Image size</span>
          <strong>
            {inspection
              ? `${inspection.image_width} × ${inspection.image_height}`
              : "Waiting for inspection"}
          </strong>
        </article>

        <article className="vision-summary-card">
          <span>Detections</span>
          <strong>{detections.length}</strong>
        </article>

        {summaryCards.map((summary) => (
          <article
            key={summary.label}
            className={`vision-summary-card ${summary.className}`}
          >
            <span>{summary.label}</span>
            <strong>{summary.count}</strong>
          </article>
        ))}
      </div>

      <div className="vision-layout">
        <section className="vision-preview-panel">
          <header className="vision-panel-header">
            <div>
              <p className="eyebrow">Image preview</p>
              <h3>{inspection?.filename ?? file?.name ?? "No image loaded"}</h3>
            </div>

            <span className="vision-panel-chip">
              {inspection ? `${detections.length} detections` : "Awaiting upload"}
            </span>
          </header>

          {previewUrl ? (
            <div className="vision-stage">
              <img
                className="vision-image"
                src={previewUrl}
                alt={file?.name ?? "Uploaded preview"}
              />

              {inspection && (
                <div className="vision-overlay">
                  {detections.map((detection) => {
                    const isActive = detection.id === activeDetection?.id
                    const left = (detection.bbox.x / imageWidth) * 100
                    const top = (detection.bbox.y / imageHeight) * 100
                    const width = (detection.bbox.width / imageWidth) * 100
                    const height = (detection.bbox.height / imageHeight) * 100

                    return (
                      <button
                        key={detection.id}
                        type="button"
                        className={`vision-box ${
                          isActive ? "vision-box-active" : ""
                        } vision-status-${detection.review_status}`}
                        style={{
                          left: `${left}%`,
                          top: `${top}%`,
                          width: `${width}%`,
                          height: `${height}%`,
                        }}
                        onClick={() => selectDetection(detection.id)}
                        aria-label={`${detection.label}, ${detection.review_status}`}
                      >
                        <span className="vision-box-label">
                          {detection.label}
                        </span>
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          ) : (
            <div className="vision-empty-state">
              <span className="vision-empty-icon">🪟</span>
              <h3>No image selected</h3>
              <p>
                Pick an image on the left to preview it here and draw the visual
                detections after inspection.
              </p>
            </div>
          )}
        </section>

        <aside className="vision-review-panel">
          <header className="vision-panel-header">
            <div>
              <p className="eyebrow">Detection review</p>
              <h3>Results and review state</h3>
            </div>
            <span className="vision-panel-chip vision-panel-chip-backend">
              Saved to backend
            </span>
          </header>

          {activeDetection ? (
            <div className="vision-active-card">
              <div className="vision-active-heading">
                <div>
                  <p className="vision-active-label">Selected detection</p>
                  <h4>{activeDetection.label}</h4>
                </div>

                <span className={`vision-status-pill vision-status-${activeDetection.review_status}`}>
                  {activeDetection.review_status}
                </span>
              </div>

              <dl className="vision-details-grid">
                <div>
                  <dt>Confidence</dt>
                  <dd>{formatPercent(activeDetection.confidence)}</dd>
                </div>
                <div>
                  <dt>Coordinates</dt>
                  <dd>
                    {activeDetection.bbox.x}, {activeDetection.bbox.y}
                  </dd>
                </div>
                <div>
                  <dt>Size</dt>
                  <dd>
                    {activeDetection.bbox.width} × {activeDetection.bbox.height}
                  </dd>
                </div>
                <div>
                  <dt>Box area</dt>
                  <dd>
                    {(activeDetection.bbox.width * activeDetection.bbox.height).toLocaleString()}
                  </dd>
                </div>
              </dl>

              <div className="vision-review-actions">
                <button
                  type="button"
                  className="vision-action-button vision-action-accept"
                  onClick={() => updateDetectionStatus(activeDetection.id, "accepted")}
                  disabled={isReviewingDetection(activeDetection.id)}
                >
                  Approve
                </button>
                <button
                  type="button"
                  className="vision-action-button vision-action-reject"
                  onClick={() => updateDetectionStatus(activeDetection.id, "rejected")}
                  disabled={isReviewingDetection(activeDetection.id)}
                >
                  Reject
                </button>
              </div>
            </div>
          ) : (
            <div className="vision-empty-table">
              <h3>No detections yet</h3>
              <p>
                Run inspection to populate the review table and bounding boxes.
              </p>
            </div>
          )}

          <div className="vision-table-wrap">
            <table className="vision-table">
              <thead>
                <tr>
                  <th>Label</th>
                  <th>Confidence</th>
                  <th>Box</th>
                  <th>Status</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {detections.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="vision-table-empty">
                      Detected regions will appear here.
                    </td>
                  </tr>
                ) : (
                  detections.map((detection) => {
                    const isActive = detection.id === activeDetection?.id

                    return (
                      <tr
                        key={detection.id}
                        className={isActive ? "vision-table-row-active" : ""}
                        onClick={() => selectDetection(detection.id)}
                      >
                        <td>
                          <strong>{detection.label}</strong>
                        </td>
                        <td>{formatPercent(detection.confidence)}</td>
                        <td>
                          {detection.bbox.x}, {detection.bbox.y}
                        </td>
                        <td>
                          <span
                            className={`vision-status-pill vision-status-${detection.review_status}`}
                          >
                            {detection.review_status}
                          </span>
                        </td>
                        <td>
                          <div className="vision-row-actions">
                            <button
                              type="button"
                              className="vision-mini-button"
                              onClick={(event) => {
                                event.stopPropagation()
                                updateDetectionStatus(detection.id, "accepted")
                              }}
                              disabled={isReviewingDetection(detection.id)}
                            >
                              Approve
                            </button>
                            <button
                              type="button"
                              className="vision-mini-button vision-mini-button-danger"
                              onClick={(event) => {
                                event.stopPropagation()
                                updateDetectionStatus(detection.id, "rejected")
                              }}
                              disabled={isReviewingDetection(detection.id)}
                            >
                              Reject
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </aside>
      </div>
    </section>
  )
}