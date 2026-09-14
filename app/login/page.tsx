"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";

export default function LoginPage() {
  const [password, setPassword] = useState("");
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);

  async function submit() {
    if (!password) return;
    setLoading(true);
    setError(false);
    try {
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      if (res.ok) {
        const params = new URLSearchParams(window.location.search);
        window.location.href = params.get("next") || "/";
      } else {
        setError(true);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6">
      <div className="w-full max-w-sm rounded-md border border-border/60 bg-card p-6 text-card-foreground">
        <span className="font-mono text-xs text-primary">Alif Dev Studio</span>
        <h1 className="font-display mt-1 text-2xl italic">FreelanceOps Agent</h1>
        <p className="mt-2 text-sm text-card-foreground/70">Enter the password to continue.</p>

        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder="Password"
          autoFocus
          className="mt-4 w-full rounded-sm border border-card-foreground/20 bg-background/5 px-3 py-2 text-sm text-card-foreground outline-none focus-visible:ring-2 focus-visible:ring-primary"
        />
        {error && <p className="mt-2 text-xs text-destructive">Wrong password — try again.</p>}

        <Button className="mt-4 w-full" onClick={submit} disabled={loading || !password}>
          {loading ? "Checking…" : "Enter"}
        </Button>
      </div>
    </div>
  );
}
