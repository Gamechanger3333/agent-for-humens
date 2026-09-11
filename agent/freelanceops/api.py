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
import time
from collections import defaultdict, deque

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, Header, HTTPException, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from . import db  # noqa: E402
from .agent import build_agent  # noqa: E402
from .tools import (  # noqa: E402
    check_followups,
    draft_followup,
    draft_proposal,
    invoice_reminder,
)

app = FastAPI(title="FreelanceOps Agent API", version="1.0.0")

# --- CORS ---
# The Next.js frontend proxies through its own server (app/api/**/route.ts),
# so the browser never calls this API directly. CORS only matters for direct
# callers (curl, Postman, another service). Default is *closed*; set
# ALLOWED_ORIGINS explicitly to open it up, e.g. for local frontend dev.
_allowed = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[] if not _allowed else _allowed.split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# --- API key ---
# Optional but recommended: set AGENT_API_KEY in agent/.env. When set, every
# route below /api/health requires a matching X-API-Key header. This is a
# shared secret between the Next.js proxy and this service — it is never
# sent to (or readable by) the browser.
_API_KEY = os.getenv("AGENT_API_KEY")
if not _API_KEY:
    print(
        "[freelanceops] WARNING: AGENT_API_KEY is not set — the API is running "
        "with no authentication. Set AGENT_API_KEY in agent/.env before deploying."
    )


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if _API_KEY and x_api_key != _API_KEY:
        raise HTTPException(401, "Invalid or missing API key")


# --- Rate limiting ---
# Simple fixed-window limiter, in-memory, per client IP. Good enough for a
# single-instance demo deployment; swap for a shared store (Redis) if this
# ever runs behind multiple workers/instances.
_RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
_hits: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = _hits[client_ip]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= _RATE_LIMIT:
        raise HTTPException(429, "Too many requests — please slow down.")
    window.append(now)
    return await call_next(request)


class ProposalRequest(BaseModel):
    job_description: str = Field(min_length=1, max_length=6000)
    save: bool = True


class FollowupRequest(BaseModel):
    lead_id: str = Field(min_length=1, max_length=100)
    mark_sent: bool = False


class InvoiceRequest(BaseModel):
    client_name: str = Field(default="", max_length=200)


class AgentRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/proposal", dependencies=[Depends(require_api_key)])
def api_draft_proposal(req: ProposalRequest) -> dict:
    if not req.job_description.strip():
        raise HTTPException(400, "job_description is required")
    text = draft_proposal(req.job_description, save=req.save)
    return {"proposal": text}


@app.get("/api/followups", dependencies=[Depends(require_api_key)])
def api_check_followups(days: int = 4) -> dict:
    return {"leads": check_followups(days)}


@app.post("/api/followup", dependencies=[Depends(require_api_key)])
def api_draft_followup(req: FollowupRequest) -> dict:
    text = draft_followup(req.lead_id, mark_sent=req.mark_sent)
    return {"message": text}


@app.post("/api/invoice-reminder", dependencies=[Depends(require_api_key)])
def api_invoice_reminder(req: InvoiceRequest) -> dict:
    text = invoice_reminder(req.client_name)
    return {"reminder": text}


@app.get("/api/dashboard-summary", dependencies=[Depends(require_api_key)])
def api_dashboard_summary() -> dict:
    """One call for the dashboard's landing view: stale leads + overdue invoices."""
    leads = check_followups(days=4)
    invoices = db.fetch_overdue_invoices()
    return {"stale_leads": leads, "overdue_invoices": invoices}


@app.post("/api/agent", dependencies=[Depends(require_api_key)])
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
