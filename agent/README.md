# FreelanceOps Agent (Strands + Bedrock)

Step 1 of the build: `draft_proposal` working end-to-end.

```
agent/
  freelanceops/
    agent.py       # Agent + system prompt + Bedrock model
    tools.py       # @tool definitions (draft_proposal)
    portfolio.py   # Alif Dev Studio project data + matcher
  test_local.py    # offline + --live tests
  requirements.txt
  .env.example
```

## Run

```bash
cd agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # fill in AWS creds + BEDROCK_MODEL_ID

python test_local.py            # offline: schema + matching, no AWS
python test_local.py --live     # real Bedrock call
python -m freelanceops.agent "Draft a proposal for this post: <paste>"
```

Enable model access for your `BEDROCK_MODEL_ID` in the Bedrock console
(same region as `AWS_REGION`) before the live run.

## How Strands tool-calling works

1. `@tool` on a function registers it. Strands builds the JSON schema from the
   **type hints**, the tool name from the **function name**, and the description
   the model routes on from the **docstring** — so docstrings are prompt surface.
2. `Agent(model=..., system_prompt=..., tools=[draft_proposal])` starts the
   event loop. You call `agent("natural language request")`.
3. The model returns a `toolUse` block; Strands validates args, runs your
   Python function, wraps the return value as `toolResult`, and loops until the
   model produces a final text answer. You never dispatch tools manually.
4. Tools 2-4 (`check_followups`, `draft_followup`, `invoice_reminder`) are just
   more decorated functions in the `tools=[...]` list — orchestration
   ("check leads, then draft follow-ups for each") is emergent, not coded.

## Supabase

`freelanceops/db.py` holds all data access (service-role key, server-side only).
Run `schema.sql` in your Supabase SQL editor to create `leads`, `proposals` and
`invoices`, then fill `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` in `.env`.

- `check_followups(days=4)` → active leads whose `last_contact_at` is stale.
- `draft_followup(lead_id, mark_sent=False)` → reads the real lead, writes the
  message; `mark_sent=True` bumps `last_contact_at` + `followup_count`.
- `invoice_reminder(client_name="")` → unpaid invoices past `due_date`.
- `draft_proposal(job_post)` → also inserts into `proposals` (`save=False` opts out).

## Next steps

- Wrap `build_agent()` in a Bedrock AgentCore entrypoint for deployment.
- Dashboard (leads table, proposal composer) once the backend is provisioned.

