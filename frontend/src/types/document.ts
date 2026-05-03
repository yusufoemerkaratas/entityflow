export type DocumentCreateRequest = {
  text: string
  source_type?: string
}

export type DocumentResponse = {
  id: number
  char_count: number
  content_hash: string
  is_duplicate: boolean
  uploaded_at: string
}

export type DocumentDetail = {
  id: number
  raw_text: string
  source_type: string
  char_count: number
  uploaded_at: string
}