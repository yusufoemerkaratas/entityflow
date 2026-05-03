import { useState } from "react"
import { Link, useLocation, useParams } from "react-router-dom"

export function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const location = useLocation()
  const isDuplicate = (location.state as { isDuplicate?: boolean } | null)
    ?.isDuplicate

  const [showDuplicateInfo, setShowDuplicateInfo] = useState(isDuplicate ?? false)

  return (
    <section className="page-card">
      {showDuplicateInfo && (
        <div className="status-card" style={{ borderColor: "var(--accent)", background: "var(--accent-bg)" }}>
          <div className="status-indicator status-online" />
          <div style={{ flex: 1 }}>
            <h3>Duplicate document detected</h3>
            <p>
              This text was already uploaded. You have been redirected to the
              existing document.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setShowDuplicateInfo(false)}
            style={{
              background: "none",
              border: "none",
              color: "var(--text)",
              cursor: "pointer",
              fontSize: "1.2rem",
              padding: "0.25rem",
            }}
            aria-label="Dismiss"
          >
            ✕
          </button>
        </div>
      )}

      <div className="page-header">
        <p className="eyebrow">Document detail</p>
        <h2>Document #{id}</h2>
        <p>
          This route is ready for the later document detail, extraction results,
          and review UI.
        </p>
      </div>

      <div className="info-panel">
        <h3>Route parameter</h3>
        <p>
          The document id comes from the URL segment{" "}
          <code>/documents/:id</code>.
        </p>
        <p>
          Current route value: <strong>{id}</strong>
        </p>
      </div>

      <Link className="button-link secondary" to="/">
        Back to home
      </Link>
    </section>
  )
}