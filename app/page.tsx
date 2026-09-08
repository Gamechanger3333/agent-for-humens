"use client";

import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { agentApi, type Invoice, type Lead } from "@/lib/agent-api";

export default function Index() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="mx-auto flex max-w-5xl flex-col gap-1 px-6 py-8">
          <p className="text-sm font-medium text-muted-foreground">Alif Dev Studio</p>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">FreelanceOps Agent</h1>
          <p className="max-w-2xl text-sm text-muted-foreground">
            An agent that drafts proposals, chases quiet leads, and reminds clients about overdue
            invoices — built with Strands Agents on Amazon Bedrock. Only pings you for real
            decisions.
          </p>
        </div>
      </header>

      <main className="mx-auto flex max-w-5xl flex-col gap-8 px-6 py-10">
        <AgentConsole />
        <div className="grid gap-8 md:grid-cols-2">
          <ProposalDrafter />
          <OperationsPanel />
        </div>
      </main>
    </div>
  );
}

/* ---------------------------------------------------------------------- */
/* Free-text agent console — the "actually agentic" entry point           */
/* ---------------------------------------------------------------------- */

function AgentConsole() {
  const [prompt, setPrompt] = useState("");
  const [response, setResponse] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function ask() {
    if (!prompt.trim()) return;
    setLoading(true);
    setResponse(null);
    try {
      const { response } = await agentApi.askAgent(prompt);
      setResponse(response);
    } catch (err) {
      toast.error("Agent request failed", { description: (err as Error).message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ask the agent</CardTitle>
        <CardDescription>
          It decides which tools to call — try "check my leads and draft follow-ups for anything
          pending".
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <Textarea
          placeholder="What do you need done?"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={2}
        />
        <div>
          <Button onClick={ask} disabled={loading}>
            {loading ? "Thinking…" : "Run"}
          </Button>
        </div>
        {response && (
          <pre className="whitespace-pre-wrap rounded-md border bg-muted p-4 text-sm text-foreground">
            {response}
          </pre>
        )}
      </CardContent>
    </Card>
  );
}

/* ---------------------------------------------------------------------- */
/* Proposal drafter                                                       */
/* ---------------------------------------------------------------------- */

function ProposalDrafter() {
  const [jobDescription, setJobDescription] = useState("");
  const [proposal, setProposal] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function draft() {
    if (!jobDescription.trim()) return;
    setLoading(true);
    setProposal(null);
    try {
      const { proposal } = await agentApi.draftProposal(jobDescription);
      setProposal(proposal);
      toast.success("Proposal drafted and saved");
    } catch (err) {
      toast.error("Couldn't draft proposal", { description: (err as Error).message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Draft a proposal</CardTitle>
        <CardDescription>Paste a job post — the agent matches it to real past work.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <Textarea
          placeholder="Paste the job post here…"
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          rows={6}
        />
        <div>
          <Button onClick={draft} disabled={loading}>
            {loading ? "Drafting…" : "Draft proposal"}
          </Button>
        </div>
        {proposal && (
          <pre className="whitespace-pre-wrap rounded-md border bg-muted p-4 text-sm text-foreground">
            {proposal}
          </pre>
        )}
      </CardContent>
    </Card>
  );
}

/* ---------------------------------------------------------------------- */
/* Stale leads + overdue invoices                                         */
/* ---------------------------------------------------------------------- */

function OperationsPanel() {
  const [leads, setLeads] = useState<Lead[] | null>(null);
  const [invoices, setInvoices] = useState<Invoice[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [drafting, setDrafting] = useState<string | null>(null);
  const [followupText, setFollowupText] = useState<Record<string, string>>({});

  async function load() {
    setLoading(true);
    try {
      const { stale_leads, overdue_invoices } = await agentApi.dashboardSummary();
      setLeads(stale_leads);
      setInvoices(overdue_invoices);
    } catch (err) {
      toast.error("Couldn't load dashboard", { description: (err as Error).message });
    } finally {
      setLoading(false);
    }
  }

  async function draftFor(leadId: string) {
    setDrafting(leadId);
    try {
      const { message } = await agentApi.draftFollowup(leadId);
      setFollowupText((prev) => ({ ...prev, [leadId]: message }));
    } catch (err) {
      toast.error("Couldn't draft follow-up", { description: (err as Error).message });
    } finally {
      setDrafting(null);
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle>Needs attention</CardTitle>
          <CardDescription>Quiet leads and overdue invoices, pulled live.</CardDescription>
        </div>
        <Button variant="outline" size="sm" onClick={load} disabled={loading}>
          {loading ? "Loading…" : "Refresh"}
        </Button>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {leads === null && invoices === null && (
          <p className="text-sm text-muted-foreground">
            Click refresh to pull today's stale leads and overdue invoices from Supabase.
          </p>
        )}

        {leads && leads.length > 0 && (
          <div className="flex flex-col gap-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Quiet leads
            </p>
            {leads.map((lead) => (
              <div key={lead.id} className="rounded-md border p-3">
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <p className="text-sm font-medium text-foreground">{lead.client_name}</p>
                    <p className="text-xs text-muted-foreground">{lead.job_title}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">{lead.days_since_contact}d quiet</Badge>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => draftFor(lead.id)}
                      disabled={drafting === lead.id}
                    >
                      {drafting === lead.id ? "Drafting…" : "Draft follow-up"}
                    </Button>
                  </div>
                </div>
                {followupText[lead.id] && (
                  <pre className="mt-2 whitespace-pre-wrap rounded-md bg-muted p-3 text-xs text-foreground">
                    {followupText[lead.id]}
                  </pre>
                )}
              </div>
            ))}
          </div>
        )}

        {leads && leads.length === 0 && (
          <p className="text-sm text-muted-foreground">No quiet leads right now. 🎉</p>
        )}

        {invoices && invoices.length > 0 && (
          <div className="flex flex-col gap-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Overdue invoices
            </p>
            {invoices.map((inv) => (
              <div
                key={inv.id}
                className="flex items-center justify-between rounded-md border p-3 text-sm"
              >
                <span className="text-foreground">{inv.client_name}</span>
                <span className="text-muted-foreground">
                  {inv.currency} {inv.amount} · {inv.days_overdue}d overdue
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
