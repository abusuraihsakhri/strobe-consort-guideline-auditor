"""
Focused tests for security hardening and reliability improvements.
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import tempfile
import csv
from strobe_consort import calculate_metrics, process_batch
from agents.base import AuditTrail, PHIGuard, SecurityException


class TestCalculateMetrics:
    def test_basic_scoring(self):
        res = calculate_metrics(v1=10.0, v2=5.0, v3=2.0)
        # score = 10.0 + 5.0/2 + 2.0/3 = 10 + 2.5 + 0.67 = 13.17
        assert res["score"] == 13.17
        assert res["classification"] == "Moderate / Intermediate"
        assert res["inputs_evaluated"] == 3

    def test_empty_input(self):
        res = calculate_metrics()
        assert res["score"] == 1.0  # Default when no numeric values
        assert res["inputs_evaluated"] == 0

    def test_string_values_ignored(self):
        res = calculate_metrics(v1=10.0, name="test")
        assert res["inputs_evaluated"] == 2
        assert res["score"] == 10.0

    def test_none_values_filtered(self):
        res = calculate_metrics(v1=10.0, v2=None, v3=5.0)
        assert res["inputs_evaluated"] == 2

    def test_classification_tiers(self):
        low = calculate_metrics(v1=5.0)
        assert low["classification"] == "Low / Standard"

        moderate = calculate_metrics(v1=15.0)
        assert moderate["classification"] == "Moderate / Intermediate"

        high = calculate_metrics(v1=30.0)
        assert high["classification"] == "High / Severe"


class TestProcessBatch:
    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            process_batch("nonexistent_file.csv", "output.csv")

    def test_empty_csv_raises(self, tmp_path):
        csv_in = tmp_path / "empty.csv"
        csv_in.write_text("", encoding="utf-8")
        with pytest.raises(ValueError, match="no headers"):
            process_batch(str(csv_in), str(tmp_path / "out.csv"))

    def test_batch_output_structure(self, tmp_path):
        csv_in = tmp_path / "in.csv"
        csv_out = tmp_path / "out.csv"
        csv_in.write_text("ID,v1,v2\nA,10.0,5.0\nB,20.0,8.0\n", encoding="utf-8")

        process_batch(str(csv_in), str(csv_out))

        with open(csv_out, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert "score" in rows[0]
        assert "classification" in rows[0]
        assert "clinical_recommendation" in rows[0]
        assert rows[0]["ID"] == "A"
        assert rows[1]["ID"] == "B"

    def test_output_directory_created(self, tmp_path):
        csv_in = tmp_path / "in.csv"
        csv_out = tmp_path / "subdir" / "nested" / "out.csv"
        csv_in.write_text("ID,v1\nA,10.0\n", encoding="utf-8")

        process_batch(str(csv_in), str(csv_out))

        assert csv_out.exists()


class TestAuditTrailSecurity:
    def test_custom_secret_key(self):
        trail = AuditTrail(secret_key="test-key-123")
        entry = trail.log("actor", "tier", "event", {"data": "value"})
        assert "current_hash" in entry
        assert entry["prev_hash"] == "GENESIS_BLOCK_0000000000000000"

    def test_integrity_verification(self):
        trail = AuditTrail(secret_key="integrity-test-key")
        trail.log("a", "t", "e1", {"x": 1})
        trail.log("a", "t", "e2", {"x": 2})
        trail.log("a", "t", "e3", {"x": 3})
        assert trail.verify_integrity() is True

    def test_integrity_tamper_detection(self):
        trail = AuditTrail(secret_key="tamper-test-key")
        trail.log("a", "t", "e1", {"x": 1})
        trail.log("a", "t", "e2", {"x": 2})
        # Tamper with the chain
        trail.logs[0]["current_hash"] = "TAMPERED_HASH"
        assert trail.verify_integrity() is False

    def test_phi_blocked_in_audit_log(self):
        trail = AuditTrail(secret_key="phi-test-key")
        with pytest.raises(SecurityException):
            trail.log("actor", "tier", "event", {"data": "Patient MRN-12345678"})

    def test_get_trail_returns_logs(self):
        trail = AuditTrail(secret_key="get-trail-key")
        trail.log("a", "t", "e1", {"x": 1})
        assert len(trail.get_trail()) == 1


class TestPHIGuard:
    def test_mrn_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("MRN-12345678")

    def test_ssn_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("SSN: 123-45-6789")

    def test_phone_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call 555-123-4567")

    def test_email_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email: patient@example.com")

    def test_clean_text_passes(self):
        PHIGuard.assert_no_phi("Specimen KEY-001 optimal results")
        PHIGuard.assert_no_phi("Analytical assay completed")

    def test_redact_phi(self):
        redacted = PHIGuard.redact_phi("Patient MRN-12345678 and SSN 123-45-6789")
        assert "MRN" not in redacted or "12345678" not in redacted
        assert "[REDACTED_IDENTIFIER]" in redacted

    def test_empty_text_safe(self):
        PHIGuard.assert_no_phi("")
        PHIGuard.assert_no_phi(None)
