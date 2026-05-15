from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.dashboard import (
    DashboardFinding,
    DashboardSeverityCount,
    DashboardSourceCount,
    DashboardStats,
    DashboardSummaryResponse,
    DashboardTimePoint,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


FINDING_SELECT = """
    SELECT
        d.id AS document_id,
        d.source_type,
        e.entity_type,
        e.entity_text,
        e.review_status,
        x.extractor_name,
        x.created_at,
        CASE
            WHEN COALESCE(e.confidence, 0.5) >= 0.90 THEN 'Critical'
            WHEN COALESCE(e.confidence, 0.5) >= 0.70 THEN 'High'
            WHEN COALESCE(e.confidence, 0.5) >= 0.40 THEN 'Medium'
            ELSE 'Low'
        END AS severity,
        ROUND((COALESCE(e.confidence, 0.5)::numeric * 100))::int AS risk_score
    FROM entities e
    JOIN extractions x ON x.id = e.extraction_id
    JOIN documents d ON d.id = x.document_id
"""


def _document_label(document_id: int, source_type: str) -> str:
    label = source_type.replace("_", " ").title()
    return f"{label} #{document_id}"


def _finding_from_row(row) -> DashboardFinding:
    return DashboardFinding(
        document_id=row["document_id"],
        document_label=_document_label(row["document_id"], row["source_type"]),
        source_type=row["source_type"],
        entity_type=row["entity_type"],
        entity_text=row["entity_text"],
        extractor_name=row["extractor_name"],
        severity=row["severity"],
        risk_score=row["risk_score"],
        detected_at=row["created_at"].isoformat(),
        review_status=row["review_status"],
    )


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummaryResponse:
    stats_row = db.execute(
        text(
            """
            SELECT
                (SELECT COUNT(*) FROM documents) AS total_documents,
                (SELECT COUNT(*) FROM entities) AS total_entities,
                (
                    SELECT COUNT(*)
                    FROM entities
                    WHERE review_status IN ('approved', 'rejected')
                ) AS reviewed_entities,
                (SELECT COUNT(DISTINCT extractor_name) FROM extractions) AS extractor_count
            """
        )
    ).mappings().one()

    recent_rows = db.execute(
        text(
            f"""
            {FINDING_SELECT}
            ORDER BY x.created_at DESC, e.id DESC
            LIMIT 5
            """
        )
    ).mappings().all()

    critical_rows = db.execute(
        text(
            f"""
            {FINDING_SELECT}
            WHERE COALESCE(e.confidence, 0.5) >= 0.70
            ORDER BY risk_score DESC, x.created_at DESC, e.id DESC
            LIMIT 3
            """
        )
    ).mappings().all()

    severity_rows = db.execute(
        text(
            """
            SELECT severity, COUNT(*) AS count
            FROM (
                SELECT
                    CASE
                        WHEN COALESCE(confidence, 0.5) >= 0.90 THEN 'Critical'
                        WHEN COALESCE(confidence, 0.5) >= 0.70 THEN 'High'
                        WHEN COALESCE(confidence, 0.5) >= 0.40 THEN 'Medium'
                        ELSE 'Low'
                    END AS severity
                FROM entities
            ) severity_table
            GROUP BY severity
            """
        )
    ).mappings().all()

    source_rows = db.execute(
        text(
            """
            SELECT source_type, COUNT(*) AS count
            FROM documents
            GROUP BY source_type
            ORDER BY count DESC, source_type ASC
            LIMIT 5
            """
        )
    ).mappings().all()

    time_rows = db.execute(
        text(
            """
            SELECT DATE(x.created_at) AS day, COUNT(e.id) AS count
            FROM extractions x
            LEFT JOIN entities e ON e.extraction_id = x.id
            WHERE x.created_at >= CURRENT_DATE - INTERVAL '6 days'
            GROUP BY DATE(x.created_at)
            ORDER BY day ASC
            """
        )
    ).mappings().all()
    counts_by_day = {row["day"]: row["count"] for row in time_rows}
    today = date.today()
    findings_over_time = [
        DashboardTimePoint(
            label=(today - timedelta(days=offset)).strftime("%b %-d"),
            count=counts_by_day.get(today - timedelta(days=offset), 0),
        )
        for offset in range(6, -1, -1)
    ]

    return DashboardSummaryResponse(
        stats=DashboardStats(
            total_documents=stats_row["total_documents"],
            total_entities=stats_row["total_entities"],
            reviewed_entities=stats_row["reviewed_entities"],
            extractor_count=stats_row["extractor_count"],
        ),
        critical_findings=[_finding_from_row(row) for row in critical_rows],
        recent_findings=[_finding_from_row(row) for row in recent_rows],
        severity_counts=[
            DashboardSeverityCount(severity=row["severity"], count=row["count"])
            for row in severity_rows
        ],
        findings_over_time=findings_over_time,
        source_counts=[
            DashboardSourceCount(source_type=row["source_type"], count=row["count"])
            for row in source_rows
        ],
    )
