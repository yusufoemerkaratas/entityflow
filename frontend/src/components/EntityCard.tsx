import type { ReviewedEntity } from "../types"

type EntityCardProps = {
  entity: ReviewedEntity
  onHover: (entity: ReviewedEntity | null) => void
}

const ENTITY_TYPE_CLASSES: Record<string, string> = {
  email: "entity-type-email",
  phone: "entity-type-phone",
  url: "entity-type-url",
  person: "entity-type-person",
  organization: "entity-type-organization",
  location: "entity-type-location",
  title: "entity-type-title",
  address: "entity-type-address",
}

function entityTypeClass(entityType: string): string {
  const key = entityType.toLowerCase()
  return ENTITY_TYPE_CLASSES[key] ?? "entity-type-default"
}

function formatConfidence(confidence: number | null): string {
  if (typeof confidence !== "number" || Number.isNaN(confidence)) {
    return "-"
  }

  return `${Math.round(confidence * 100)}%`
}

function formatSpan(entity: ReviewedEntity): string {
  const start = entity.span_start
  const end = entity.span_end

  if (
    typeof start === "number" &&
    typeof end === "number" &&
    Number.isFinite(start) &&
    Number.isFinite(end) &&
    start >= 0 &&
    end > start
  ) {
    return `${start}-${end}`
  }

  return "n/a"
}

export function EntityCard({ entity, onHover }: EntityCardProps) {
  return (
    <article
      className="entity-card"
      onMouseEnter={() => onHover(entity)}
      onMouseLeave={() => onHover(null)}
      onFocus={() => onHover(entity)}
      onBlur={() => onHover(null)}
      tabIndex={0}
    >
      <div className="entity-card-header">
        <span className={`entity-type-badge ${entityTypeClass(entity.entity_type)}`}>
          {entity.entity_type}
        </span>
        <span className="entity-span">Span: {formatSpan(entity)}</span>
      </div>
      <p className="entity-text">{entity.entity_text}</p>
      <div className="entity-card-footer">
        <span>Confidence</span>
        <strong>{formatConfidence(entity.confidence)}</strong>
      </div>
    </article>
  )
}
