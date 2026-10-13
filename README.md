# STROBE / CONSORT Reporting Checklist Auditor

Reviewer-led tracking of manuscript reporting items, with a static browser interface and a Python summary API. Supports **STROBE (22 main items)** for cohort, case-control and cross-sectional studies and **CONSORT 2025 (30 main items)** for randomised trials.

The prompts are condensed topic summaries, not the full official wording or subitem checklists. Consult the relevant official guideline and any study-design extension before submission.

## What it does

- Record each numbered reporting item as **Reported**, **Partially reported**, **Not reported**, **Not applicable**, or **Not assessed**.
- Document manuscript section/page references, supporting evidence and reviewer comments.
- View descriptive counts of reviewed, missing and unassessed topics, without claiming a validated quality score.
- Export a review as **JSON** for later editing or **CSV** for spreadsheets; import a prior JSON review of the same guideline/version.
- Use the same guideline catalogue from Python to create a template, validate an export and report its counts.
- Run an optional FastAPI server for the browser app and structured JSON summary endpoint.

All review information entered in the static interface stays in the active browser tab until you export it. There is **no automatic manuscript processing**, external model inference, server upload, or browser persistence. Avoid entering patient-identifiable information.

## Use the application

The static interface is in `web/`. From the repository directory:

```bash
python -m http.server 8080 --directory web
```

Open `http://localhost:8080/`. Pick STROBE or CONSORT 2025, review the numbered prompts, and export JSON before closing or reloading the tab. Importing JSON replaces the current review for the selected guideline, but does not affect the other guideline.

A GitHub Actions workflow is configured to publish `web/` to GitHub Pages after successful tests on `master`. Publication requires Pages to be enabled and the deployment workflow to succeed; the live URL is not claimed until verified.

## Python checklist workflow

Python 3.10 or later is supported for the checklist module; it has no third-party dependencies.

```bash
python guideline_audit.py template --guideline strobe --manuscript "Cohort draft" --output strobe-review.json
python guideline_audit.py summary --input strobe-review.json
python guideline_audit.py template --guideline consort --output consort-review.json
```

The `summary` command validates the item IDs, number of items, guideline version, permitted statuses and text lengths before computing counts. It flags not-applicable decisions without a written rationale. No scientific quality or risk-of-bias inference is performed.

## Optional FastAPI server

```bash
python -m pip install -r requirements.txt
python cli.py serve --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000/`. The relevant API routes are:

| Route | Method | Purpose |
| --- | --- | --- |
| `/` | GET | Browser review interface |
| `/checklists.json` | GET | Condensed item catalogue |
| `/api/checklists` | GET | Catalogue via API |
| `/api/checklist/summary` | POST | Validate and summarize an exported review JSON |
| `/health` | GET | Legacy server health endpoint |

The older `strobe_consort.py` numerical scoring demo, `cli.py audit/batch/chat` commands, and `/api/audit` endpoint remain for backwards compatibility. **They do not evaluate STROBE or CONSORT items and must not be interpreted as clinical recommendations, guideline compliance assessments, or validated methodological scores.** The older agent modules are not connected to the reporting checklist UI.

The in-memory HMAC audit trail belongs to the legacy API. Configure `AUDIT_SECRET_KEY` when deploying the legacy service; otherwise the key is generated per process, so signatures are not durable across restarts. `/api/audit/logs` is disabled unless `ENABLE_AUDIT_LOG_ENDPOINT=1` is explicitly set. Its output is not appropriate for untrusted public deployment.

## Testing

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m pip check
```

GitHub Actions runs the Python tests across Python 3.10–3.13 and validates browser JavaScript syntax. The static browser experience uses ordinary JavaScript; **no Pyodide, server-side Python, or external API** is required for GitHub Pages.

## References and limits

- [STROBE official checklists](https://www.strobe-statement.org/checklists/)
- [CONSORT 2025 statement and publications](https://www.consort-spirit.org/published-statements)
- [CONSORT 2025 reporting guideline (Hopewell et al.)](https://doi.org/10.1371/journal.pmed.1004587)

Reporting completeness is distinct from internal validity, risk of bias, and study quality. Checklists and their extensions should be applied with human methodological judgment. PHI pattern screening in the older API is **heuristic and not a comprehensive de-identification or HIPAA compliance guarantee**. Do not send confidential manuscript or patient data to a publicly exposed instance.

## License

MIT; see [LICENSE](LICENSE).
