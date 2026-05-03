import { Link, useParams } from "react-router-dom"

export function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>()

  return (
    <section className="page-card">
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