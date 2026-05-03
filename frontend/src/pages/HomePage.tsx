import { Link } from "react-router-dom"
import { BackendStatus } from "../components/BackendStatus"

export function HomePage() {
  return (
    <section className="page-card">
      <div className="page-header">
        <p className="eyebrow">Frontend foundation</p>
        <h2>EntityFlow dashboard foundation</h2>
        <p>
          This screen is the starting point for the later upload, extraction,
          comparison, and review workflows.
        </p>
      </div>

   <BackendStatus />

      <div className="feature-grid">
        <article className="feature-card">
          <h3>Documents</h3>
          <p>
            Later, users will create or upload documents from this area and send
            them to the backend.
          </p>
        </article>

        <article className="feature-card">
          <h3>Extractors</h3>
          <p>
            Regex, spaCy, and mini LLM extractors will be triggered from the
            frontend through the API client.
          </p>
        </article>

        <article className="feature-card">
          <h3>Review</h3>
          <p>
            Extracted entities will eventually be compared and reviewed in a
            human-in-the-loop workflow.
          </p>
        </article>
      </div>

      <Link className="button-link" to="/documents/1">
        Open sample document route
      </Link>
    </section>
  )
}