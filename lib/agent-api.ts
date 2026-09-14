// Thin client for the FreelanceOps agent API.
//
// The browser never talks to the FastAPI backend directly — it calls these
// same-origin `/api/*` routes, which are Next.js server route handlers
// (see app/api/**/route.ts) that proxy to FastAPI with a server-only shared
// secret attached. This keeps the backend's address and API key out of the
// browser bundle entirely.

const BASE_URL = "";

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

export type ImpactStats = {
  proposals_count: number;
  followups_sent: number;
  hours_saved: number;
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

  impactStats: () => request<ImpactStats>("/api/impact-stats"),

  markFollowupSent: (leadId: string) =>
    request<{ status: string }>("/api/mark-followup-sent", {
      method: "POST",
      body: JSON.stringify({ lead_id: leadId }),
    }),

  askAgent: (prompt: string) =>
    request<{ response: string }>("/api/agent", {
      method: "POST",
      body: JSON.stringify({ prompt }),
    }),
};
