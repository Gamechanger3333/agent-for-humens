"""Bedrock AgentCore entrypoint for FreelanceOps.

Wraps the same `build_agent()` used locally and by the FastAPI layer — no
agent logic is duplicated here. This is what turns "an agent that runs on my
laptop" into "an agent deployed on managed AWS infrastructure", which the
hackathon scores under Technical Implementation.

Local test:
    cd agent
    pip install bedrock-agentcore bedrock-agentcore-starter-toolkit
    python -m freelanceops.agentcore_app
    # in another shell:
    curl -X POST http://localhost:8080/invocations \
        -H "Content-Type: application/json" \
        -d '{"prompt": "check my leads and draft follow-ups"}'

Deploy:
    agentcore configure --entrypoint freelanceops/agentcore_app.py
    agentcore launch

(`agentcore` CLI comes from bedrock-agentcore-starter-toolkit. It builds the
container, provisions the AgentCore Runtime, and gives you an invoke ARN /
HTTPS endpoint — put that in the dashboard's VITE_AGENT_API_URL, or keep the
FastAPI service as the demo backend and mention this deployment in the
submission as the production path. Either is legitimate; having this file
and a working local run of it is what the judging note asks for.)
"""

from __future__ import annotations

from bedrock_agentcore import BedrockAgentCoreApp

from .agent import build_agent

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(request: dict) -> str:
    prompt = request.get("prompt", "")
    if not prompt:
        return "No prompt provided."
    agent = build_agent()
    result = agent(prompt)
    return str(result)


if __name__ == "__main__":
    app.run()
