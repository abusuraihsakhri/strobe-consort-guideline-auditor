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
