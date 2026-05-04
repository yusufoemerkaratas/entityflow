import { useEffect, useState } from "react"
import { Link, useLocation, useParams } from "react-router-dom"

import {
  getDocument,
  getDocumentExtractions,
  patchEntityReview,
} from "../api/client"
import { ExtractorColumn } from "../components/ExtractorColumn"
import { RawTextPanel } from "../components/RawTextPanel"
import type {
  ComparisonResponse,
  DocumentDetail,
  ExtractorName,
  ReviewedEntity,
} from "../types"

import "./ResultsView.css"

export function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const location = useLocation()
  const isDuplicate = (location.state as { isDuplicate?: boolean } | null)
    ?.isDuplicate

  const [showDuplicateInfo, setShowDuplicateInfo] = useState(isDuplicate ?? false)
  const [documentDetail, setDocumentDetail] = useState<DocumentDetail | null>(
    null,
  )
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null)
  const [hoveredEntity, setHoveredEntity] = useState<ReviewedEntity | null>(
    null,
  )
  const [reviewError, setReviewError] = useState<string | null>(null)
  const [pendingReviewIds, setPendingReviewIds] = useState<Set<number>>(
    () => new Set(),
  )
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const documentId = Number(id)
  const isValidId = Number.isFinite(documentId) && documentId > 0

  useEffect(() => {
    let isMounted = true

    async function loadDocument() {
      if (!isValidId) {
        setError("Invalid document id.")
        setLoading(false)
        return
      }

      setLoading(true)
      setError(null)
      setReviewError(null)
      setHoveredEntity(null)

      try {
        const [doc, extractionResults] = await Promise.all([
          getDocument(documentId),
          getDocumentExtractions(documentId),
        ])

        if (!isMounted) return

        setDocumentDetail(doc)
        setComparison(extractionResults)
      } catch (err) {
        if (!isMounted) return
        const message =
          err instanceof Error ? err.message : "An unexpected error occurred."
        setError(message)
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    loadDocument()

    return () => {
      isMounted = false
    }
  }, [documentId, isValidId])

  const extractorOrder: ExtractorName[] = ["regex", "spacy_de", "llm_mini"]
  const extractorLabels: Record<ExtractorName, string> = {
    regex: "Regex",
    spacy_de: "spaCy DE",
    llm_mini: "Mini LLM",
  }

  function replaceEntityReviewStatus(
    source: ComparisonResponse,
    entityId: number,
    reviewStatus: "approved" | "rejected",
  ): ComparisonResponse {
    return {
      ...source,
      results: Object.fromEntries(
        Object.entries(source.results).map(([extractorName, meta]) => [
          extractorName,
          {
            ...meta,
            entities: meta.entities.map((entity) =>
              entity.id === entityId
                ? { ...entity, review_status: reviewStatus }
                : entity,
            ),
          },
        ]),
      ),
    }
  }

  async function handleReviewChange(
    entityId: number,
    nextStatus: "approved" | "rejected",
  ) {
    if (!comparison) return

    const previousComparison = comparison
    setReviewError(null)
    setPendingReviewIds((current) => new Set(current).add(entityId))

    const optimisticComparison = replaceEntityReviewStatus(
      comparison,
      entityId,
      nextStatus,
    )

    setComparison(optimisticComparison)
    setHoveredEntity((current) =>
      current?.id === entityId
        ? { ...current, review_status: nextStatus }
        : current,
    )

    try {
      const updatedEntity = await patchEntityReview(entityId, nextStatus)

      setComparison((current) => {
        if (!current) return current

        return {
          ...current,
          results: Object.fromEntries(
            Object.entries(current.results).map(([extractorName, meta]) => [
              extractorName,
              {
                ...meta,
                entities: meta.entities.map((entity) =>
                  entity.id === entityId ? updatedEntity : entity,
                ),
              },
            ]),
          ),
        }
      })

      setHoveredEntity((current) =>
        current?.id === entityId ? updatedEntity : current,
      )
    } catch (err) {
      setComparison(previousComparison)
      setHoveredEntity((current) =>
        current?.id === entityId ? null : current,
      )
      setReviewError(
        err instanceof Error ? err.message : "Failed to update review status.",
      )
    } finally {
      setPendingReviewIds((current) => {
        const next = new Set(current)
        next.delete(entityId)
        return next
      })
    }
  }

  return (
    <section className="page-card">
      {showDuplicateInfo && (
        <div className="status-card status-card-duplicate">
          <div className="status-indicator status-online" />
          <div className="status-card-body">
            <h3>Duplicate document detected</h3>
            <p>
              This text was already uploaded. You have been redirected to the
              existing document.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setShowDuplicateInfo(false)}
            className="status-card-dismiss"
            aria-label="Dismiss"
          >
            ✕
          </button>
        </div>
      )}

      <div className="page-header">
        <p className="eyebrow">Extractor comparison</p>
        <h2>Document #{id}</h2>
        <p>
          Compare extractor outputs side by side and inspect how entities map to
          the original raw text.
        </p>
        {documentDetail && (
          <div className="results-header-meta">
            <span className="results-header-pill">
              Source: {documentDetail.source_type}
            </span>
            <span className="results-header-pill">
              {documentDetail.char_count.toLocaleString()} chars
            </span>
            <span className="results-header-pill">
              Uploaded {new Date(documentDetail.uploaded_at).toLocaleString()}
            </span>
          </div>
        )}
      </div>

      {loading && (
        <div className="results-loading" role="status">
          <span className="results-spinner" />
          <div>Loading document and extraction results...</div>
        </div>
      )}

      {error && !loading && (
        <div className="results-error" role="alert">
          <strong>Unable to load this document.</strong>
          <span>{error}</span>
        </div>
      )}

      {reviewError && !loading && !error && (
        <div className="results-error results-review-error" role="alert">
          <strong>Review update failed.</strong>
          <span>{reviewError}</span>
        </div>
      )}

      {!loading && !error && documentDetail && (
        <>
          <RawTextPanel
            rawText={documentDetail.raw_text}
            hoveredEntity={hoveredEntity}
            sourceType={documentDetail.source_type}
            charCount={documentDetail.char_count}
          />

          <div className="results-grid">
            {extractorOrder.map((extractorName) => (
              <ExtractorColumn
                key={extractorName}
                extractorName={extractorName}
                title={extractorLabels[extractorName]}
                meta={comparison?.results?.[extractorName] ?? null}
                onHover={setHoveredEntity}
                onReviewChange={handleReviewChange}
                isReviewingEntity={(entityId) => pendingReviewIds.has(entityId)}
              />
            ))}
          </div>
        </>
      )}

      <Link className="button-link secondary" to="/">
        Back to home
      </Link>
    </section>
  )
}