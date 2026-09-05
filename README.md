# Strobe Consort Guideline Auditor

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Reference Guidelines & Standards:** STROBE, CONSORT, CAP, CLSI, ISO Standards

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## What It Does

STROBE & CONSORT Statement Compliance Auditor for clinical trial manuscripts. Evaluates observational and randomized clinical trial manuscripts for essential checklist compliance using a multi-agent consensus architecture.

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## Key Features

- **Single & Batch Evaluation**: Process individual cases or bulk CSV datasets
- **Multi-Agent Consensus**: Three specialized workers (QC Invariant, Safety Escalation, Protocol Conformance) evaluate each task
- **Zero-PHI Outbound Guard**: Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
- **Tamper-Evident HMAC-SHA256 Audit Trail**: Chained, cryptographically signed logs for every evaluation
- **FastAPI REST API**: OpenAPI 3.1 REST endpoints with `/health` and `/metrics`
- **Prometheus Telemetry**: Operational metrics exporter
- **Active Learning Bayesian Calibration**: Dynamic worker reliability weight tracking

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/strobe-consort-guideline-auditor.git
cd strobe-consort-guideline-auditor

# Install dependencies
pip install -r requirements.txt
```

---

## CLI Usage

### 1. Single Case Evaluation
```bash
python strobe_consort.py single --v1 10.0 --v2 5.0 --v3 2.0
```

### 2. Batch CSV Processing
```bash
python strobe_consort.py batch -i sample.csv -o results.csv
```

### 3. Enterprise CLI (with multi-agent consensus)
```bash
# Audit a single task
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Batch process
python cli.py batch -i sample.csv -o results.csv

# Verify audit trail integrity
python cli.py verify-audit

# Launch REST API server
python cli.py serve --host 127.0.0.1 --port 8000
```

---

## REST API Endpoints

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/health` | GET | Service health check |
| `/metrics` | GET | Operational metrics |
| `/api/audit` | POST | Submit task for evaluation |
| `/api/chat` | POST | Query supervisory chat |
| `/api/audit/logs` | GET | Retrieve audit trail |

---

## Input Data Schema

### CSV Batch Input
| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Patient identifier | Required |
| `v1` | Primary measurement | Required |
| `v2` | Secondary measurement | Required |
| `v3` | Tertiary measurement | Optional |

### API Audit Payload
```json
{
  "task_id": "TASK-2026-001",
  "target_identifier": "KEY-TARGET-01",
  "primary_metric": 28.5,
  "secondary_metric": 14.2,
  "status_descriptor": "NOMINAL",
  "is_critical_flag": false
}
```

---

## Security

- **PHI Protection**: All outbound data is scanned for PHI (MRN, SSN, phone, email, DOB) before logging or transmission
- **Audit Integrity**: HMAC-SHA256 chained audit trail with tamper detection
- **Configurable Secret Key**: Set `AUDIT_SECRET_KEY` environment variable for persistent audit integrity

```bash
export AUDIT_SECRET_KEY="your-secure-key-here"
```

---

## Testing

```bash
# Run all tests
pytest -v

# Run specific test modules
python -m pytest test_strobe_consort.py -v
python -m pytest tests/ -v

# Run simulation benchmark
python simulator.py 1000
```

---

## Container Deployment

```bash
docker build -t strobe-consort-guideline-auditor .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-key strobe-consort-guideline-auditor
```

---

## Project Structure

```
strobe-consort-guideline-auditor/
├── strobe_consort.py          # Core scoring algorithm & batch processor
├── cli.py                     # Enterprise CLI interface
├── simulator.py               # High-throughput simulation
├── enrichment.py              # Enrichment feature engines
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container configuration
├── sample.csv                 # Example input data
├── agents/
│   ├── __init__.py
│   ├── base.py                # Security, PHI guard, audit trail
│   ├── models.py              # Pydantic data models
│   ├── supervisor.py          # Multi-agent orchestrator
│   ├── workers.py             # Specialized evaluation workers
│   ├── api.py                 # FastAPI REST endpoints
│   ├── llm_factory.py         # LLM client factory
│   ├── metrics.py             # Prometheus metrics collector
│   ├── learning.py            # Bayesian calibration engine
│   └── streamer.py            # WebSocket telemetry
├── tests/
│   ├── test_enrichment.py
│   ├── test_strobe_consort_guideline_auditor.py
│   └── test_security_and_reliability.py
└── web/
    └── index.html
```
