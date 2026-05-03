export type ExtractorName = "regex" | "spacy_de" | "llm_mini"

export type ExtractedEntity = {
  entity_type: string
  entity_text: string
  span_start: number | null
  span_end: number | null
  confidence: number | null
}

export type ReviewedEntity = ExtractedEntity & {
  review_status: string
}

export type ExtractionRunResponse = {
  document_id: number
  extraction_id: number
  extractor_name: string
  extractor_version: string
  entity_count: number
  entities: ExtractedEntity[]
}

export type ExtractionMeta = {
  extraction_id: number
  extractor_version: string
  entity_count: number
  entities: ReviewedEntity[]
}

export type ComparisonResponse = {
  document_id: number
  results: Record<string, ExtractionMeta>
}