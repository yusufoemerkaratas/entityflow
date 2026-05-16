from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_dashboard_summary_returns_expected_shape():
    response = client.get("/dashboard/summary")

    assert response.status_code == 200

    data = response.json()
    assert set(data.keys()) == {
        "stats",
        "critical_findings",
        "recent_findings",
        "severity_counts",
        "findings_over_time",
        "source_counts",
    }

    stats = data["stats"]
    assert set(stats.keys()) == {
        "total_documents",
        "total_entities",
        "reviewed_entities",
        "extractor_count",
    }

    assert isinstance(data["critical_findings"], list)
    assert isinstance(data["recent_findings"], list)
    assert isinstance(data["severity_counts"], list)
    assert isinstance(data["findings_over_time"], list)
    assert isinstance(data["source_counts"], list)
