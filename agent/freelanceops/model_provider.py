"""Builds the Strands model instance based on MODEL_PROVIDER in .env.

This lets the whole app switch between Amazon Bedrock and Groq (or any other
OpenAI-compatible host) with a single environment variable — no code changes
needed once AWS Bedrock quota is unblocked.

Usage in agent.py / tools.py:
    from .model_provider import build_model
    model = build_model(temperature=0.3)
"""

from __future__ import annotations

import os


def build_model(temperature: float = 0.3):
    """Return a configured Strands model based on MODEL_PROVIDER env var.

    MODEL_PROVIDER=bedrock (default) -> Amazon Bedrock (BEDROCK_MODEL_ID)
    MODEL_PROVIDER=groq              -> Groq via OpenAI-compatible API (GROQ_MODEL_ID, GROQ_API_KEY)
    """
    provider = os.getenv("MODEL_PROVIDER", "bedrock").lower()

    if provider == "groq":
        from strands.models.openai import OpenAIModel

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "MODEL_PROVIDER=groq but GROQ_API_KEY is not set in .env. "
                "Get a free key at https://console.groq.com/keys"
            )

        return OpenAIModel(
            client_args={
                "api_key": api_key,
                "base_url": "https://api.groq.com/openai/v1",
            },
            model_id=os.getenv("GROQ_MODEL_ID", "openai/gpt-oss-120b"),
            params={"temperature": temperature},
        )

    # default: Bedrock
    from strands.models import BedrockModel

    return BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        temperature=temperature,
    )
