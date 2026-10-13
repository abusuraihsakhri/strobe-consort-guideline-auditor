"""Regression coverage for the actual reporting-guideline workflow."""
import copy
import json
from pathlib import Path

import pytest

from guideline_audit import blank_review, load_catalogue, summarize_review
from agents.base import AuditTrail


def test_catalogue_has_latest_expected_item_counts():
    catalogue = load_catalogue()
    assert len(catalogue["strobe"]["items"]) == 22
    assert len(catalogue["consort"]["items"]) == 30
    assert catalogue["consort"]["version"] == "2025"
    for framework in catalogue.values():
        ids = [item["id"] for item in framework["items"]]
        assert len(ids) == len(set(ids))


@pytest.mark.parametrize("guideline,count", [("strobe", 22), ("consort", 30)])
def test_blank_review_and_summary(guideline, count):
    review = blank_review(guideline, "Manuscript-v2")
    result = summarize_review(review)
    assert result["total_items"] == count
    assert result["assessed_items"] == 0
    assert result["counts"]["unassessed"] == count
    assert "score" not in result
    review["items"][0]["status"] = "reported"
    review["items"][1]["status"] = "partial"
    review["items"][2]["status"] = "missing"
    review["items"][3]["status"] = "na"
    review["items"][3]["notes"] = "Not relevant to design"
    result = summarize_review(review)
    assert result["assessed_items"] == 4
    assert result["applicable_items_reviewed"] == 3
    assert result["counts"]["na"] == 1
    assert result["na_without_rationale"] == []


@pytest.mark.parametrize("mutation", [
    lambda data: data.update(version="2010"),
    lambda data: data.update(format="unknown"),
    lambda data: data.update(guideline="prisma"),
    lambda data: data["items"].append(data["items"][0].copy()),
    lambda data: data["items"][0].update(id="999"),
    lambda data: data["items"][0].update(status="perfect"),
    lambda data: data["items"][0].update(notes="x" * 2001),
    lambda data: data["items"][0].update(location=42),
])
def test_reject_malformed_reviews(mutation):
    review = blank_review("strobe")
    mutation(review)
    with pytest.raises(ValueError):
        summarize_review(review)


def test_na_without_reason_warns_but_does_not_fake_grade():
    review = blank_review("strobe")
    review["items"][0]["status"] = "na"
    summary = summarize_review(review)
    assert summary["na_without_rationale"] == ["1"]
    assert summary["counts"]["na"] == 1


def test_serialized_review_round_trip():
    source = blank_review("consort", "Test manuscript")
    source["items"][-1]["status"] = "reported"
    encoded = json.dumps(source)
    assert summarize_review(json.loads(encoded))["counts"]["reported"] == 1


def test_audit_mac_detects_tail_tamper():
    trail = AuditTrail(secret_key="a-nonsecret-test-key")
    trail.log("tester", "test", "event", {"id": 1})
    assert trail.verify_integrity()
    trail.logs[0]["event_type"] = "edited"
    assert trail.verify_integrity() is False


def test_audit_mac_detects_signature_tamper_and_returns_copy():
    trail = AuditTrail(secret_key="a-nonsecret-test-key")
    trail.log("tester", "test", "event", {"id": 1})
    leaked = trail.get_trail()
    leaked[0]["current_hash"] = "tampered"
    assert trail.verify_integrity()
    trail.logs[0]["current_hash"] = "tampered"
    assert not trail.verify_integrity()


def test_review_assets_present():
    html = (Path(__file__).resolve().parents[1] / "web" / "index.html").read_text(encoding="utf-8")
    assert 'id="guideline"' in html
    assert 'id="jsonExport"' in html
    assert 'id="csvExport"' in html
    assert './checklists.json' in html
    assert "DOSSIER-SIM" not in html
