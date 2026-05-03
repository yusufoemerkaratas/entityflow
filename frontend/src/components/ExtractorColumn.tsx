import type { ExtractionMeta, ExtractorName, ReviewedEntity } from "../types"

import { EntityCard } from "./EntityCard"

type ExtractorColumnProps = {
  extractorName: ExtractorName
  title: string
  meta: ExtractionMeta | null
  onHover: (entity: ReviewedEntity | null) => void
}

export function ExtractorColumn({
  extractorName,
  title,
  meta,
  onHover,
}: ExtractorColumnProps) {
  const entityCount = meta?.entity_count ?? 0
  const entities = meta?.entities ?? []

  let emptyMessage = ""
  if (!meta) {
    emptyMessage = "No results yet"
  } else if (entityCount === 0) {
    emptyMessage = "No entities found"
  }

  return (
    <section className="extractor-column" data-extractor={extractorName}>
      <header className="extractor-header">
        <div>
          <h3>{title}</h3>
          <p className="extractor-version">
            {meta ? `v${meta.extractor_version}` : "Not run"}
          </p>
        </div>
        <span className="extractor-count">{entityCount}</span>
      </header>

      {emptyMessage ? (
        <div className="extractor-empty">{emptyMessage}</div>
      ) : (
        <div className="entity-list">
          {entities.map((entity, index) => (
            <EntityCard
              key={`${extractorName}-${entity.entity_type}-${index}`}
              entity={entity}
              onHover={onHover}
            />
          ))}
        </div>
      )}
    </section>
  )
}
