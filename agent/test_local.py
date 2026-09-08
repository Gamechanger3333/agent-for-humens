"""Local end-to-end test for draft_proposal.

Two modes:
  python test_local.py          -> offline: verifies tool wiring, schema and
                                   portfolio matching with the LLM call stubbed.
  python test_local.py --live   -> real Amazon Bedrock call (needs AWS creds).
"""

from __future__ import annotations

import sys

from dotenv import load_dotenv

load_dotenv()

JOB = """We need a senior Next.js developer to build a multi-tenant SaaS
invoicing dashboard. Must support Stripe subscription billing, PDF invoice
generation, and role-based team access. Node.js backend, Postgres, hosted on AWS.
Existing codebase is a mess, we want it rebuilt properly."""


def offline() -> None:
    import freelanceops.tools as tools

    tools._generate = lambda prompt: f"[STUBBED MODEL OUTPUT]\n---\n{prompt}"

    from freelanceops.portfolio import match_projects

    matched = [p["name"] for p in match_projects(JOB)]
    print("Matched projects:", matched)
    assert "LedgerLite" in matched, "expected invoicing project to match"

    spec = tools.draft_proposal.tool_spec
    print("Tool name:", spec["name"])
    print("Input schema:", spec["inputSchema"])
    assert spec["name"] == "draft_proposal"

    out = tools.draft_proposal(job_description=JOB)
    assert "LedgerLite" in out and "multi-tenant" in out
    print("\n--- prompt sent to Bedrock ---\n")
    print(out[:1200])
    print("\nOFFLINE TEST PASSED")


def live() -> None:
    from freelanceops.agent import build_agent

    agent = build_agent()
    print(agent(f"Draft a proposal for this job post:\n\n{JOB}"))


if __name__ == "__main__":
    live() if "--live" in sys.argv else offline()
