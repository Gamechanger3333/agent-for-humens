"""Supabase access layer for FreelanceOps.

Tools stay thin: they call these helpers, get plain dicts back, and let the
model decide what to do. The service-role key is used because the agent runs
server-side only (never in a browser), so it bypasses RLS.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

from supabase import Client, create_client

ACTIVE_STATUSES = ("new", "proposal_sent", "in_conversation")


@lru_cache(maxsize=1)
def client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in agent/.env"
        )
    return create_client(url, key)


def _days_since(iso_ts: str | None) -> int:
    if not iso_ts:
        return 9999
    ts = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - ts).days


def fetch_stale_leads(days: int = 4) -> list[dict[str, Any]]:
    """Leads still in play whose last contact is older than `days`."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows = (
        client()
        .table("leads")
        .select("*")
        .in_("status", list(ACTIVE_STATUSES))
        .lt("last_contact_at", cutoff)
        .order("last_contact_at")
        .execute()
        .data
        or []
    )
    for row in rows:
        row["days_since_contact"] = _days_since(row.get("last_contact_at"))
    return rows


def fetch_lead(lead_id: str) -> dict[str, Any] | None:
    rows = client().table("leads").select("*").eq("id", lead_id).limit(1).execute().data
    return rows[0] if rows else None


def find_lead_by_name(name: str) -> dict[str, Any] | None:
    # `name` gets interpolated into a PostgREST `or=` filter string below.
    # Strip characters that are syntactically significant there (`,`, `(`,
    # `)`, `%`, `*`) so a crafted client name can't widen or break the
    # filter — e.g. injecting `,status.eq.paid` to match unrelated rows.
    safe = re.sub(r"[,()%*]", "", name).strip()
    if not safe:
        return None
    rows = (
        client()
        .table("leads")
        .select("*")
        .or_(f"client_name.ilike.%{safe}%,company.ilike.%{safe}%")
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if rows else None


def mark_followed_up(lead_id: str) -> None:
    lead = fetch_lead(lead_id) or {}
    client().table("leads").update(
        {
            "last_contact_at": datetime.now(timezone.utc).isoformat(),
            "followup_count": int(lead.get("followup_count") or 0) + 1,
        }
    ).eq("id", lead_id).execute()


def save_proposal(
    job_description: str,
    proposal_text: str,
    matched_projects: list[str],
    job_title: str | None = None,
    lead_id: str | None = None,
) -> dict[str, Any]:
    payload = {
        "job_description": job_description,
        "proposal_text": proposal_text,
        "matched_projects": matched_projects,
        "job_title": job_title,
        "lead_id": lead_id,
    }
    rows = client().table("proposals").insert(payload).execute().data or []
    return rows[0] if rows else payload


def fetch_overdue_invoices() -> list[dict[str, Any]]:
    today = datetime.now(timezone.utc).date().isoformat()
    rows = (
        client()
        .table("invoices")
        .select("*")
        .eq("paid", False)
        .lt("due_date", today)
        .order("due_date")
        .execute()
        .data
        or []
    )
    for row in rows:
        row["days_overdue"] = (
            datetime.now(timezone.utc).date()
            - datetime.fromisoformat(row["due_date"]).date()
        ).days
    return rows


def fetch_impact_stats() -> dict[str, int]:
    """Counts behind the dashboard's "time saved" figure.

    Deliberately conservative, real counts — no invented numbers: how many
    proposals the agent has actually drafted, and how many follow-ups have
    actually been sent (bumped via mark_followed_up).
    """
    proposals_res = client().table("proposals").select("id", count="exact").execute()
    proposals_count = proposals_res.count or 0

    leads = client().table("leads").select("followup_count").execute().data or []
    followups_sent = sum(int(lead.get("followup_count") or 0) for lead in leads)

    return {"proposals_count": proposals_count, "followups_sent": followups_sent}
