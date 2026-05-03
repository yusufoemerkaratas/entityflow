import type { ExtractedEntity } from "../types"

type HighlightRange = {
  start: number
  end: number
}

type RawTextPanelProps = {
  rawText: string
  hoveredEntity: ExtractedEntity | null
  sourceType: string
  charCount: number
}

function isValidSpan(
  rawText: string,
  start: number | null,
  end: number | null,
): start is number {
  return (
    typeof start === "number" &&
    Number.isFinite(start) &&
    typeof end === "number" &&
    Number.isFinite(end) &&
    start >= 0 &&
    end > start &&
    end <= rawText.length
  )
}

function getHighlightRange(
  rawText: string,
  entity: ExtractedEntity | null,
): HighlightRange | null {
  if (!entity) return null

  if (isValidSpan(rawText, entity.span_start, entity.span_end)) {
    return {
      start: entity.span_start,
      end: entity.span_end as number,
    }
  }

  const text = entity.entity_text?.trim()
  if (!text) return null

  const haystack = rawText.toLowerCase()
  const needle = text.toLowerCase()
  const index = haystack.indexOf(needle)

  if (index === -1) return null

  return {
    start: index,
    end: index + text.length,
  }
}

export function RawTextPanel({
  rawText,
  hoveredEntity,
  sourceType,
  charCount,
}: RawTextPanelProps) {
  const highlightRange = getHighlightRange(rawText, hoveredEntity)

  const content = highlightRange ? (
    <>
      {rawText.slice(0, highlightRange.start)}
      <mark className="raw-text-highlight">
        {rawText.slice(highlightRange.start, highlightRange.end)}
      </mark>
      {rawText.slice(highlightRange.end)}
    </>
  ) : (
    rawText
  )

  return (
    <section className="raw-text-panel">
      <div className="raw-text-header">
        <div>
          <p className="eyebrow">Raw text</p>
          <h3>Document source</h3>
        </div>
        <div className="raw-text-meta">
          <span className="raw-text-pill">Source: {sourceType}</span>
          <span className="raw-text-pill">{charCount.toLocaleString()} chars</span>
        </div>
      </div>
      <div className="raw-text-body" aria-live="polite">
        {content}
      </div>
    </section>
  )
}
