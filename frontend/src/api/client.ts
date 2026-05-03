import type {
  ComparisonResponse,
  DocumentDetail,
  DocumentCreateRequest,
  DocumentResponse,
  ExtractionRunResponse,
  ExtractorName,
  HealthResponse,
  ReviewedEntity,
} from "../types"

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"

async function requestJson<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const message = await readErrorMessage(response)
    throw new Error(message)
  }

  return response.json() as Promise<T>
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const data = await response.json()

    if (typeof data.detail === "string") {
      return data.detail
    }

    if (Array.isArray(data.detail)) {
      return data.detail
        .map((err: { loc?: string[]; msg?: string }) => {
          const field = err.loc?.slice(-1)[0] ?? "field"
          return `${field}: ${err.msg ?? "invalid"}`
        })
        .join(" · ")
    }

    return `Request failed with status ${response.status}`
  } catch {
    return `Request failed with status ${response.status}`
  }
}

export function getHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/health")
}

export function createDocument(
  text: string,
  sourceType = "manual",
): Promise<DocumentResponse> {
  const payload: DocumentCreateRequest = {
    text,
    source_type: sourceType,
  }

  return requestJson<DocumentResponse>("/documents", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function runExtraction(
  documentId: number,
  extractor: ExtractorName,
): Promise<ExtractionRunResponse> {
  const params = new URLSearchParams({
    extractor,
  })

  return requestJson<ExtractionRunResponse>(
    `/documents/${documentId}/extract?${params.toString()}`,
    {
      method: "POST",
    },
  )
}

export function getDocumentExtractions(
  documentId: number,
): Promise<ComparisonResponse> {
  return requestJson<ComparisonResponse>(`/documents/${documentId}/extractions`)
}

export function getDocument(documentId: number): Promise<DocumentDetail> {
  return requestJson<DocumentDetail>(`/documents/${documentId}`)
}

export function patchEntityReview(
  entityId: number,
  reviewStatus: "approved" | "rejected",
): Promise<ReviewedEntity> {
  return requestJson<ReviewedEntity>(`/entities/${entityId}/review`, {
    method: "PATCH",
    body: JSON.stringify({ review_status: reviewStatus }),
  })
}