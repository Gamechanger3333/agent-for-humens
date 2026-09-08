"""Static portfolio context for Alif Dev Studio.

Kept as plain data so the proposal tool can do cheap keyword matching before
handing only the *relevant* projects to the model. This is what keeps proposals
from reading generic.
"""

STUDIO = {
    "name": "Alif Dev Studio",
    "owner_role": "Freelance full-stack developer",
    "stack": ["Next.js", "React", "TypeScript", "Node.js", "Postgres", "AWS"],
    "positioning": "Ships production SaaS, not prototypes. 7 live products in production.",
}

PROJECTS = [
    {
        "name": "LedgerLite",
        "summary": "Multi-tenant invoicing SaaS with Stripe billing and PDF generation.",
        "stack": ["Next.js", "Node.js", "Postgres", "Stripe", "AWS Lambda"],
        "outcome": "Cut client invoice turnaround from 2 days to under 10 minutes.",
        "tags": ["saas", "payments", "stripe", "billing", "invoice", "multi-tenant", "dashboard"],
    },
    {
        "name": "ShiftBoard",
        "summary": "Realtime workforce scheduling app with role-based access and shift swaps.",
        "stack": ["React", "Node.js", "WebSockets", "Postgres", "AWS ECS"],
        "outcome": "Handles 4k concurrent users for a logistics operator.",
        "tags": ["realtime", "websocket", "scheduling", "rbac", "auth", "react"],
    },
    {
        "name": "InsightPanel",
        "summary": "Analytics dashboard with custom chart builder and scheduled email reports.",
        "stack": ["Next.js", "TypeScript", "Postgres", "Redis", "AWS SES"],
        "outcome": "Replaced a $900/mo BI tool for the client.",
        "tags": ["analytics", "dashboard", "charts", "reporting", "data", "bi", "email"],
    },
    {
        "name": "CartFlux",
        "summary": "Headless e-commerce storefront with Shopify backend and edge-cached PDPs.",
        "stack": ["Next.js", "GraphQL", "Shopify", "Vercel Edge"],
        "outcome": "LCP down from 4.1s to 1.2s; +18% conversion.",
        "tags": ["ecommerce", "shopify", "storefront", "performance", "seo", "headless"],
    },
    {
        "name": "DocuMind",
        "summary": "RAG document assistant over client knowledge bases with citation output.",
        "stack": ["Python", "Bedrock", "pgvector", "Next.js"],
        "outcome": "Deflected ~40% of inbound support tickets.",
        "tags": ["ai", "llm", "rag", "chatbot", "openai", "bedrock", "automation", "agent"],
    },
    {
        "name": "FieldSync",
        "summary": "Offline-first PWA for field technicians with conflict-free sync.",
        "stack": ["React", "IndexedDB", "Node.js", "Postgres"],
        "outcome": "Works fully offline across 200+ daily job sites.",
        "tags": ["pwa", "mobile", "offline", "sync", "react native", "app"],
    },
    {
        "name": "GateKeep",
        "summary": "Auth + subscription boilerplate: SSO, org invites, usage-based metering.",
        "stack": ["Next.js", "Auth.js", "Stripe", "Postgres", "AWS"],
        "outcome": "Cut new-SaaS launch time to under a week for 3 clients.",
        "tags": ["auth", "sso", "subscription", "saas", "onboarding", "api", "integration"],
    },
]


def match_projects(job_description: str, limit: int = 3) -> list[dict]:
    """Rank portfolio projects by tag/stack overlap with the job description."""
    text = job_description.lower()
    scored = []
    for project in PROJECTS:
        score = sum(2 for tag in project["tags"] if tag in text)
        score += sum(1 for tech in project["stack"] if tech.lower() in text)
        scored.append((score, project))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    top = [project for score, project in scored if score > 0][:limit]
    return top or [PROJECTS[0], PROJECTS[2], PROJECTS[6]][:limit]


def format_projects(projects: list[dict]) -> str:
    return "\n".join(
        f"- {p['name']}: {p['summary']} Stack: {', '.join(p['stack'])}. Result: {p['outcome']}"
        for p in projects
    )
