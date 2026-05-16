from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_documents: int
    total_entities: int
    reviewed_entities: int
    extractor_count: int


class DashboardFinding(BaseModel):
    document_id: int
    document_label: str
    source_type: str
    entity_type: str
    entity_text: str
    extractor_name: str
    severity: str
    risk_score: int
    detected_at: str
    review_status: str


class DashboardSeverityCount(BaseModel):
    severity: str
    count: int


class DashboardTimePoint(BaseModel):
    label: str
    count: int


class DashboardSourceCount(BaseModel):
    source_type: str
    count: int


class DashboardSummaryResponse(BaseModel):
    stats: DashboardStats
    critical_findings: list[DashboardFinding]
    recent_findings: list[DashboardFinding]
    severity_counts: list[DashboardSeverityCount]
    findings_over_time: list[DashboardTimePoint]
    source_counts: list[DashboardSourceCount]
