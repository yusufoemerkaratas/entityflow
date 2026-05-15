export type DashboardStats = {
  total_documents: number
  total_entities: number
  reviewed_entities: number
  extractor_count: number
}

export type DashboardFinding = {
  document_id: number
  document_label: string
  source_type: string
  entity_type: string
  entity_text: string
  extractor_name: string
  severity: "Critical" | "High" | "Medium" | "Low"
  risk_score: number
  detected_at: string
  review_status: "pending" | "approved" | "rejected"
}

export type DashboardSeverityCount = {
  severity: "Critical" | "High" | "Medium" | "Low"
  count: number
}

export type DashboardTimePoint = {
  label: string
  count: number
}

export type DashboardSourceCount = {
  source_type: string
  count: number
}

export type DashboardSummaryResponse = {
  stats: DashboardStats
  critical_findings: DashboardFinding[]
  recent_findings: DashboardFinding[]
  severity_counts: DashboardSeverityCount[]
  findings_over_time: DashboardTimePoint[]
  source_counts: DashboardSourceCount[]
}