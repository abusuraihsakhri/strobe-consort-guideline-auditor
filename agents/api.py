"""
FastAPI REST API Server for Strobe Consort Guideline Auditor.
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Any
from guideline_audit import summarize_review, load_catalogue
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Strobe Consort Guideline Auditor API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "strobe-consort-guideline-auditor", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


@app.get("/api/checklists")
def api_checklists():
    """Metadata and condensed review prompts; not the full official checklists."""
    return load_catalogue()


@app.post("/api/checklist/summary")
def api_checklist_summary(review: dict[str, Any]):
    try:
        return summarize_review(review)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# Static assets are served last, after the REST routes above.
app.mount("/", StaticFiles(directory=str(Path(__file__).resolve().parent.parent / "web"), html=True), name="web")
