"""FreelanceOps agent tools.

Strands tool pattern in one paragraph:
`@tool` turns a plain Python function into a tool the model can call. The SDK
reads the function NAME (tool name), the TYPE HINTS (JSON schema for the
arguments), and the DOCSTRING (the description the model uses to decide *when*
to call it) — so the docstring is prompt engineering, not just documentation.
You never call these yourself; you pass them to `Agent(tools=[...])` and the
model emits a toolUse block, Strands executes the function, feeds the return
value back as toolResult, and the loop continues until the model answers.

Return plain strings/dicts/lists — Strands serializes them for you.
"""

from __future__ import annotations

import os

from strands import tool
from strands.models import BedrockModel

from . import db
from .portfolio import STUDIO, format_projects, match_projects


# A small, cheap model instance used *inside* tools for text generation.
# Keeping generation inside the tool means the orchestrating agent stays focused
# on routing, and each tool owns its own writing style.
_writer = BedrockModel(
    model_id=os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0"),
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    temperature=0.4,
)


def _generate(prompt: str) -> str:
    """One-shot completion using the Bedrock model (no tools, no history)."""
    from strands import Agent

    return str(Agent(model=_writer, tools=[], callback_handler=None)(prompt))


@tool
def draft_proposal(job_description: str, save: bool = True) -> str:
    """Draft a tailored Upwork proposal for a job post and save it.

    Use this whenever the user shares a job description, job post, or client
    brief and wants to apply or bid. The proposal references real past projects
    from the Alif Dev Studio portfolio that match the job's requirements.

    Args:
        job_description: The full text of the job post / client brief.
        save: Whether to store the proposal in the proposals table (default true).

    Returns:
        A ready-to-send proposal, roughly 150-220 words.
    """
    relevant = match_projects(job_description)

    prompt = f"""You are writing an Upwork proposal for {STUDIO['name']}.
Author: {STUDIO['owner_role']}. Positioning: {STUDIO['positioning']}.
Core stack: {', '.join(STUDIO['stack'])}.

RELEVANT PAST WORK (cite these specifically, with their concrete results):
{format_projects(relevant)}

JOB POST:
\"\"\"{job_description.strip()}\"\"\"

Rules:
- Open with one specific sentence about THEIR problem. No "I hope this finds you well",
  no "I am excited", no "I am the perfect fit".
- Reference 1-2 of the past projects above by name, tied to a requirement in the post.
- Include one concrete clarifying question that proves you read the post.
- Propose a short first milestone.
- 150-220 words, plain text, first person, confident and direct. No markdown headings.

Return only the proposal text."""

    text = _generate(prompt).strip()

    if save:
        try:
            db.save_proposal(
                job_description=job_description,
                proposal_text=text,
                matched_projects=[p["name"] for p in relevant],
                job_title=job_description.strip().splitlines()[0][:120],
            )
        except Exception as exc:  # storage must never lose the draft
            return f"{text}\n\n[warning: proposal not saved — {exc}]"

    return text


@tool
def check_followups(days: int = 4) -> list[dict]:
    """List real leads that have gone quiet and need a follow-up.

    Queries the live leads table for leads still in play (new, proposal_sent,
    in_conversation) whose last contact is older than `days`. Call this when the
    user asks who needs chasing, what's pending, or to run their daily check.

    Args:
        days: Silence threshold in days before a lead is flagged (default 4).

    Returns:
        Lead records including id, client_name, company, job_title, status,
        days_since_contact and followup_count. Empty list means nothing is due.
    """
    leads = db.fetch_stale_leads(days)
    return [
        {
            "id": lead["id"],
            "client_name": lead.get("client_name"),
            "company": lead.get("company"),
            "job_title": lead.get("job_title"),
            "status": lead.get("status"),
            "days_since_contact": lead.get("days_since_contact"),
            "followup_count": lead.get("followup_count"),
            "notes": lead.get("notes"),
        }
        for lead in leads
    ]


@tool
def draft_followup(lead_id: str, mark_sent: bool = False) -> str:
    """Write a short follow-up message for one specific lead.

    Call this once per lead returned by check_followups. Never invent client
    details — this tool reads the real lead record.

    Args:
        lead_id: The lead's id from check_followups.
        mark_sent: If true, records the follow-up on the lead (bumps
            last_contact_at and followup_count). Only set this when the user
            confirms the message was actually sent.

    Returns:
        A ready-to-send follow-up message, under 120 words.
    """
    lead = db.fetch_lead(lead_id)
    if not lead:
        return f"No lead found with id {lead_id}."

    prompt = f"""Write a follow-up message from {STUDIO['owner_role']} at {STUDIO['name']}.

LEAD:
- Client: {lead.get('client_name')} ({lead.get('company') or 'no company listed'})
- Job: {lead.get('job_title')}
- Status: {lead.get('status')}
- Days since last contact: {lead.get('days_since_contact') or 'unknown'}
- Previous follow-ups sent: {lead.get('followup_count')}
- Notes: {lead.get('notes') or 'none'}

Rules:
- Under 120 words, plain text, first person, warm but not needy.
- No "just checking in" or "bumping this to the top of your inbox".
- Add one piece of forward momentum: a concrete next step, a small idea for
  their project, or an availability window.
- End with a single easy-to-answer question.
- Tone escalates slightly with follow-up count, but stays respectful.

Return only the message."""

    text = _generate(prompt).strip()
    if mark_sent:
        db.mark_followed_up(lead_id)
    return text


@tool
def invoice_reminder(client_name: str = "") -> str:
    """Draft payment reminders for real overdue, unpaid invoices.

    Reads the invoices table for unpaid invoices past their due date.

    Args:
        client_name: Optional filter — only remind this client. Empty means all.

    Returns:
        One reminder per overdue invoice, or a note that nothing is overdue.
    """
    invoices = db.fetch_overdue_invoices()
    if client_name:
        needle = client_name.lower()
        invoices = [i for i in invoices if needle in (i.get("client_name") or "").lower()]
    if not invoices:
        return "No overdue unpaid invoices."

    lines = [
        f"- {i['client_name']}: {i['currency']} {i['amount']} due {i['due_date']} "
        f"({i['days_overdue']} days overdue)"
        for i in invoices
    ]
    prompt = f"""Write one payment reminder per overdue invoice below, from
{STUDIO['owner_role']} at {STUDIO['name']}.

OVERDUE INVOICES:
{chr(10).join(lines)}

Rules per message:
- Under 90 words, plain text, professional and matter-of-fact — not apologetic.
- State the exact amount, invoice due date, and how many days overdue.
- Offer to resend the invoice.
- Firmness scales with how overdue it is.

Label each with the client name on its own line, then the message."""

    return _generate(prompt).strip()

