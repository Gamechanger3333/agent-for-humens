"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { agentApi, type ImpactStats, type Invoice, type Lead } from "@/lib/agent-api";

export default function Index() {
  return (
    <div className="min-h-screen bg-background">
      <header className="mx-auto max-w-5xl px-6 pt-14 pb-10">
        <div className="animate-in fade-in slide-in-from-bottom-2 duration-500">
          <span className="font-mono text-xs text-primary">Alif Dev Studio</span>
          <h1 className="font-display mt-2 text-4xl italic tracking-tight text-foreground sm:text-5xl">
            FreelanceOps Agent
          </h1>
          <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-muted-foreground">
            Drafts proposals, chases quiet leads, and reminds clients about overdue invoices.
            It works in the background and only surfaces when a real decision needs you.
          </p>
          <ImpactStrip />
        </div>
      </header>

      <main className="mx-auto flex max-w-5xl flex-col gap-6 px-6 pb-20">
        <AgentConsole />
        <div className="grid gap-6 md:grid-cols-2">
          <ProposalDrafter />
          <OperationsPanel />
        </div>
      </main>
    </div>
  );
}

/* ---------------------------------------------------------------------- */
/* Impact strip — real counts, not invented numbers                       */
/* ---------------------------------------------------------------------- */

function ImpactStrip() {
  const [stats, setStats] = useState<ImpactStats | null>(null);

  useEffect(() => {
    agentApi
      .impactStats()
      .then(setStats)
      .catch(() => {
        // Non-critical — the dashboard works fine without this figure.
      });
  }, []);

  if (!stats || (stats.proposals_count === 0 && stats.followups_sent === 0)) return null;

  return (
    <p className="mt-4 font-mono text-xs text-primary/80">
      ~{stats.hours_saved}h saved so far — {stats.proposals_count} proposals drafted,{" "}
      {stats.followups_sent} follow-ups sent
    </p>
  );
}

/* ---------------------------------------------------------------------- */
/* Agent console — dark, monospace: this is the agent's own voice         */
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
      toast.error("The agent couldn't complete that", { description: (err as Error).message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-sm border border-border/60 bg-secondary/60 p-5">
      <div className="flex items-baseline justify-between gap-4">
        <h2 className="font-display text-lg text-foreground">Ask the agent</h2>
        <p className="text-right font-mono text-xs text-muted-foreground">
          decides which tools to call
        </p>
      </div>
      <p className="mt-1 text-sm text-muted-foreground">
        Try "check my leads and draft follow-ups for anything pending."
      </p>

      <div className="mt-4 flex flex-col gap-3">
        <div className="flex items-start gap-2 rounded-sm border border-border/60 bg-background/40 px-3 py-2">
          <span className="mt-2 font-mono text-sm text-primary">›</span>
          <Textarea
            placeholder="What do you need done?"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={2}
            maxLength={2000}
            className="resize-none border-0 bg-transparent p-0 font-mono text-sm text-foreground shadow-none focus-visible:ring-0"
          />
        </div>
        <div>
          <Button onClick={ask} disabled={loading || !prompt.trim()}>
            {loading ? "Working…" : "Run"}
          </Button>
        </div>
        {response && (
          <pre className="mt-1 whitespace-pre-wrap rounded-sm border border-border/60 bg-background/40 p-4 font-mono text-sm leading-relaxed text-foreground">
            {response}
          </pre>
        )}
      </div>
    </section>
  );
}

/* ---------------------------------------------------------------------- */
/* Proposal drafter — a ledger/index card                                 */
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
      toast.error("Couldn't draft that proposal", { description: (err as Error).message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-md border border-border/60 bg-card p-5 text-card-foreground">
      <h2 className="font-display text-lg">Draft a proposal</h2>
      <p className="mt-1 text-sm text-card-foreground/70">
        Paste a job post. The agent matches it to real past work.
      </p>

      <div className="mt-4 flex flex-col gap-3">
        <Textarea
          placeholder="Paste the job post here…"
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          rows={6}
          maxLength={6000}
          className="border-card-foreground/15 bg-background/5 text-sm text-card-foreground placeholder:text-card-foreground/40"
        />
        <div>
          <Button onClick={draft} disabled={loading || !jobDescription.trim()}>
            {loading ? "Drafting…" : "Draft proposal"}
          </Button>
        </div>
        {proposal && (
          <pre className="ledger-rule whitespace-pre-wrap pt-3 text-sm leading-relaxed text-card-foreground">
            {proposal}
          </pre>
        )}
      </div>
    </section>
  );
}

/* ---------------------------------------------------------------------- */
/* Stale leads + overdue invoices — the ledger                            */
/* ---------------------------------------------------------------------- */

function OperationsPanel() {
  const [leads, setLeads] = useState<Lead[] | null>(null);
  const [invoices, setInvoices] = useState<Invoice[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [drafting, setDrafting] = useState<string | null>(null);
  const [followupText, setFollowupText] = useState<Record<string, string>>({});
  const [sending, setSending] = useState<string | null>(null);
  const [sentIds, setSentIds] = useState<Set<string>>(new Set());

  async function load() {
    setLoading(true);
    try {
      const { stale_leads, overdue_invoices } = await agentApi.dashboardSummary();
      setLeads(stale_leads);
      setInvoices(overdue_invoices);
      setSentIds(new Set());
    } catch (err) {
      toast.error("Couldn't load the ledger", { description: (err as Error).message });
    } finally {
      setLoading(false);
    }
  }

  // Load once on first paint so the panel isn't empty by default.
  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function draftFor(leadId: string) {
    setDrafting(leadId);
    try {
      const { message } = await agentApi.draftFollowup(leadId);
      setFollowupText((prev) => ({ ...prev, [leadId]: message }));
    } catch (err) {
      toast.error("Couldn't draft that follow-up", { description: (err as Error).message });
    } finally {
      setDrafting(null);
    }
  }

  async function markSent(leadId: string) {
    setSending(leadId);
    try {
      await agentApi.markFollowupSent(leadId);
      setSentIds((prev) => new Set(prev).add(leadId));
      toast.success("Marked as sent");
    } catch (err) {
      toast.error("Couldn't mark that as sent", { description: (err as Error).message });
    } finally {
      setSending(null);
    }
  }

  return (
    <section className="rounded-md border border-border/60 bg-card p-5 text-card-foreground">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-lg">Needs attention</h2>
          <p className="mt-1 text-sm text-card-foreground/70">
            Quiet leads and overdue invoices, pulled live.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={load}
          disabled={loading}
          className="border-card-foreground/20 bg-transparent text-card-foreground hover:bg-card-foreground/5"
        >
          {loading ? "Refreshing…" : "Refresh"}
        </Button>
      </div>

      <div className="mt-4 flex flex-col gap-5">
        {leads === null && invoices === null && !loading && (
          <p className="text-sm text-card-foreground/60">
            Refresh to pull today's stale leads and overdue invoices from Supabase.
          </p>
        )}

        {leads && leads.length > 0 && (
          <div className="flex flex-col gap-3">
            <p className="text-sm font-medium text-card-foreground/80">Quiet leads</p>
            {leads.map((lead) => (
              <div key={lead.id} className="ledger-rule pt-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium">{lead.client_name}</p>
                    <p className="text-sm text-card-foreground/60">{lead.job_title}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <Badge variant="secondary" className="font-mono text-[11px]">
                      {lead.days_since_contact}d quiet
                    </Badge>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => draftFor(lead.id)}
                      disabled={drafting === lead.id}
                      className="border-card-foreground/20 bg-transparent text-card-foreground hover:bg-card-foreground/5"
                    >
                      {drafting === lead.id ? "Drafting…" : "Draft follow-up"}
                    </Button>
                  </div>
                </div>
                {followupText[lead.id] && (
                  <div className="mt-2 flex flex-col gap-2">
                    <pre className="whitespace-pre-wrap rounded-sm bg-background/5 p-3 text-xs leading-relaxed text-card-foreground">
                      {followupText[lead.id]}
                    </pre>
                    {sentIds.has(lead.id) ? (
                      <p className="text-xs text-primary">✓ Marked as sent</p>
                    ) : (
                      <div>
                        <Button
                          size="sm"
                          onClick={() => markSent(lead.id)}
                          disabled={sending === lead.id}
                        >
                          {sending === lead.id ? "Recording…" : "Mark as sent"}
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {leads && leads.length === 0 && (
          <p className="text-sm text-card-foreground/60">No quiet leads right now.</p>
        )}

        {invoices && invoices.length > 0 && (
          <div className="flex flex-col gap-3">
            <p className="text-sm font-medium text-card-foreground/80">Overdue invoices</p>
            {invoices.map((inv) => (
              <div key={inv.id} className="ledger-rule flex items-start justify-between pt-3">
                <span className="text-sm">{inv.client_name}</span>
                <div className="text-right">
                  <p className="font-mono text-sm">
                    {inv.currency} {inv.amount.toLocaleString()}
                  </p>
                  <p className="text-xs text-destructive">{inv.days_overdue} days overdue</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
