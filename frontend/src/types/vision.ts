export type VisionReviewStatus = "pending" | "accepted" | "rejected"

export type VisionBoundingBox = {
  x: number
  y: number
  width: number
  height: number
}

export type VisionDetection = {
  label: string
  confidence: number
  bbox: VisionBoundingBox
  review_status: VisionReviewStatus
}

export type VisionDetectionWithId = VisionDetection & {
  id: number
}

export type VisionInspectionResponse = {
  inspection_id: number
  filename: string
  image_width: number
  image_height: number
  detections: VisionDetectionWithId[]
}

export type VisionOcrResponse = {
  filename: string
  image_width: number
  image_height: number
  extracted_text: string
  raw_text: string
  char_count: number
  is_empty: boolean
  engine: string
}

export type VisionOcrExtractedEntity = {
  entity_type: string
  entity_text: string
  span_start: number | null
  span_end: number | null
  confidence: number | null
}

export type VisionOcrExtractionRun = {
  extractor_name: string
  extraction_id: number
  entity_count: number
}

export type VisionOcrExtractionResponse = {
  document_id: number
  source_type: string
  is_duplicate_document: boolean
  ocr: VisionOcrResponse
  runs: VisionOcrExtractionRun[]
  results: Record<string, VisionOcrExtractedEntity[]>
}
