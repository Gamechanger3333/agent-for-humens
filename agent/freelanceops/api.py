"""FastAPI layer over the FreelanceOps Strands agent.

This is the piece that turns the agent from "a CLI script" into something a
web dashboard (or, for the hackathon demo, ChatGPT/curl/anything) can call.
It does NOT reimplement any logic — every route just calls the same tool
functions the agent itself uses, or hands a free-text request to the agent's
reasoning loop when the request needs multi-step orchestration.

Run locally:
    cd agent
    uvicorn freelanceops.api:app --reload --port 8787

Endpoints:
    POST /api/proposal          {"job_description": "..."}
    GET  /api/followups         ?days=4
    POST /api/followup          {"lead_id": "...", "mark_sent": false}
    POST /api/invoice-reminder  {"client_name": ""}
    POST /api/agent             {"prompt": "check my leads and draft follow-ups"}
    GET  /api/health
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from . import db  # noqa: E402
from .agent import build_agent  # noqa: E402
from .tools import (  # noqa: E402
    check_followups,
    draft_followup,
    draft_proposal,
    invoice_reminder,
)

app = FastAPI(title="FreelanceOps Agent API", version="1.0.0")

# Dashboard runs on a different origin (Vite dev server / deployed frontend),
# so CORS has to be open here. Locked to specific origins via env in prod.
_allowed = os.getenv("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allowed == "*" else _allowed.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProposalRequest(BaseModel):
    job_description: str
    save: bool = True


class FollowupRequest(BaseModel):
    lead_id: str
    mark_sent: bool = False


class InvoiceRequest(BaseModel):
    client_name: str = ""


class AgentRequest(BaseModel):
    prompt: str


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/proposal")
def api_draft_proposal(req: ProposalRequest) -> dict:
    if not req.job_description.strip():
        raise HTTPException(400, "job_description is required")
    text = draft_proposal(req.job_description, save=req.save)
    return {"proposal": text}


@app.get("/api/followups")
def api_check_followups(days: int = 4) -> dict:
    return {"leads": check_followups(days)}


@app.post("/api/followup")
def api_draft_followup(req: FollowupRequest) -> dict:
    text = draft_followup(req.lead_id, mark_sent=req.mark_sent)
    return {"message": text}


@app.post("/api/invoice-reminder")
def api_invoice_reminder(req: InvoiceRequest) -> dict:
    text = invoice_reminder(req.client_name)
    return {"reminder": text}


@app.get("/api/dashboard-summary")
def api_dashboard_summary() -> dict:
    """One call for the dashboard's landing view: stale leads + overdue invoices."""
    leads = check_followups(days=4)
    invoices = db.fetch_overdue_invoices()
    return {"stale_leads": leads, "overdue_invoices": invoices}


@app.post("/api/agent")
def api_agent(req: AgentRequest) -> dict:
    """Free-text entry point — lets the model decide which tool(s) to chain.

    This is what makes it an *agent* dashboard rather than four buttons that
    each call one function: "check my leads and draft follow-ups for
    anything pending" hits this route and the model orchestrates
    check_followups -> draft_followup itself.
    """
    if not req.prompt.strip():
        raise HTTPException(400, "prompt is required")
    agent = build_agent()
    result = agent(req.prompt)
    return {"response": str(result)}
