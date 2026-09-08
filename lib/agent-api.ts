// Thin client for the FreelanceOps FastAPI backend (agent/freelanceops/api.py).
// Set NEXT_PUBLIC_AGENT_API_URL in .env (see .env.example) to point at your
// running backend — local FastAPI during dev, or the deployed AgentCore/API
// endpoint once you've run `agentcore launch`.

const BASE_URL = process.env.NEXT_PUBLIC_AGENT_API_URL ?? "http://localhost:8787";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export type Lead = {
  id: string;
  client_name: string;
  company?: string | null;
  job_title: string;
  status: string;
  days_since_contact: number;
  followup_count: number;
  notes?: string | null;
};

export type Invoice = {
  id: string;
  client_name: string;
  amount: number;
  currency: string;
  due_date: string;
  days_overdue: number;
};

export const agentApi = {
  health: () => request<{ status: string }>("/api/health"),

  dashboardSummary: () =>
    request<{ stale_leads: Lead[]; overdue_invoices: Invoice[] }>("/api/dashboard-summary"),

  draftProposal: (jobDescription: string, save = true) =>
    request<{ proposal: string }>("/api/proposal", {
      method: "POST",
      body: JSON.stringify({ job_description: jobDescription, save }),
    }),

  checkFollowups: (days = 4) => request<{ leads: Lead[] }>(`/api/followups?days=${days}`),

  draftFollowup: (leadId: string, markSent = false) =>
    request<{ message: string }>("/api/followup", {
      method: "POST",
      body: JSON.stringify({ lead_id: leadId, mark_sent: markSent }),
    }),

  invoiceReminder: (clientName = "") =>
    request<{ reminder: string }>("/api/invoice-reminder", {
      method: "POST",
      body: JSON.stringify({ client_name: clientName }),
    }),

  askAgent: (prompt: string) =>
    request<{ response: string }>("/api/agent", {
      method: "POST",
      body: JSON.stringify({ prompt }),
    }),
};
