import type {
  ComparisonResponse,
  DocumentDetail,
  DocumentCreateRequest,
  DocumentResponse,
  ExtractionRunResponse,
  ExtractorName,
  HealthResponse,
  ReviewedEntity,
  VisionInspectionResponse,
  VisionDetectionWithId,
  VisionOcrResponse,
  VisionReviewStatus,
} from "../types"

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ""

function buildUrl(path: string) {
  // If an explicit base URL is provided, join it with the path.
  // Otherwise use a relative path so the dev/prod host is inferred.
  if (!API_BASE_URL) return path
  return `${API_BASE_URL.replace(/\/$/, "")}${path}`
}

async function requestJson<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(buildUrl(path), {
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

async function requestFormData<T>(
  path: string,
  formData: FormData,
): Promise<T> {
  const response = await fetch(buildUrl(path), {
    method: "POST",
    body: formData,
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

export function inspectVisionImage(
  file: File,
): Promise<VisionInspectionResponse> {
  const formData = new FormData()
  formData.append("file", file)

  return requestFormData<VisionInspectionResponse>("/vision/inspect", formData)
}

export function extractVisionText(file: File): Promise<VisionOcrResponse> {
  const formData = new FormData()
  formData.append("file", file)

  return requestFormData<VisionOcrResponse>("/vision/ocr", formData)
}

export function patchVisionDetectionReview(
  detectionId: number,
  reviewStatus: VisionReviewStatus,
): Promise<VisionDetectionWithId> {
  return requestJson<VisionDetectionWithId>(
    `/vision/detections/${detectionId}/review`,
    {
      method: "PATCH",
      body: JSON.stringify({ review_status: reviewStatus }),
    },
  )
}
