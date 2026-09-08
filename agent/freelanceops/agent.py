"""FreelanceOps Agent — Strands + Amazon Bedrock.

Run: python -m freelanceops.agent "Here's a job post: ..."
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel

load_dotenv()

from .tools import (  # noqa: E402  (after load_dotenv)
    check_followups,
    draft_followup,
    draft_proposal,
    invoice_reminder,
)

SYSTEM_PROMPT = """You are FreelanceOps, the operations agent for Alif Dev Studio,
a one-person freelance full-stack shop working on Upwork.

Your job is to remove repetitive client-ops work: drafting proposals, chasing
follow-ups, and sending payment reminders. Decide which tools to call and in
what order without asking permission for routine steps.

Rules:
- If the user pastes or describes a job post, call draft_proposal.
- If the user asks who needs chasing / what's pending / to run the daily check,
  call check_followups, then call draft_followup once per lead it returns.
- For money owed, call invoice_reminder.
- Never invent client names, amounts, or dates — pull them from tools.
- Only mark a follow-up as sent when the user explicitly confirms they sent it.
- Only ask the user a question when a real judgment call is needed
  (pricing, scope you cannot infer, or whether to actually send something).
- Return drafts as plain text the user can copy and send.
"""


def build_agent() -> Agent:
    """Create the agent. Tools are just functions decorated with @tool —
    Strands derives each tool's name/schema/description from the function
    signature and docstring, then handles the toolUse -> toolResult loop."""
    model = BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        temperature=0.3,
    )
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[draft_proposal, check_followups, draft_followup, invoice_reminder],
    )



def main() -> None:
    prompt = " ".join(sys.argv[1:]).strip()
    if not prompt:
        print('Usage: python -m freelanceops.agent "<your request>"')
        raise SystemExit(1)
    agent = build_agent()
    result = agent(prompt)
    print(result)


if __name__ == "__main__":
    main()
