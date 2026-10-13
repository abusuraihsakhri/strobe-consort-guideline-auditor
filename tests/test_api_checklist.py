"""FastAPI integration smoke tests."""
from fastapi.testclient import TestClient

from agents.api import app
from guideline_audit import blank_review

client = TestClient(app)


def test_home_page_and_static_catalogue():
    home = client.get("/")
    assert home.status_code == 200
    assert "Reporting Checklist Auditor" in home.text
    data = client.get("/checklists.json")
    assert data.status_code == 200
    assert len(data.json()["consort"]["items"]) == 30


def test_api_catalogue():
    result = client.get("/api/checklists")
    assert result.status_code == 200
    assert len(result.json()["strobe"]["items"]) == 22


def test_checklist_summary_api():
    review = blank_review("strobe")
    review["items"][0]["status"] = "reported"
    response = client.post("/api/checklist/summary", json=review)
    assert response.status_code == 200
    assert response.json()["counts"]["reported"] == 1


def test_invalid_review_returns_validation_error():
    review = blank_review("strobe")
    review["items"][0]["status"] = "unrecognized"
    response = client.post("/api/checklist/summary", json=review)
    assert response.status_code == 422


def test_existing_legacy_health():
    response = client.get("/health")
    assert response.status_code == 200


def test_logs_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_AUDIT_LOG_ENDPOINT", raising=False)
    response = client.get("/api/audit/logs")
    assert response.status_code == 403


def test_reject_phi_without_500():
    response = client.post("/api/audit", json={
        "task_id": "MRN-12345678",
        "target_identifier": "KEY-001",
        "primary_metric": 1.0,
    })
    assert response.status_code == 422


def test_mock_chat_does_not_claim_scientific_verification():
    response = client.post("/api/chat", json={"query": "Please assess STROBE checklist."})
    assert response.status_code == 200
    assert "No external language model" in response.json()["response"]
