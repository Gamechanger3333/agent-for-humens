// SERVER-ONLY. Do not import this from a "use client" component — it reads
// process.env.AGENT_API_KEY (deliberately *not* NEXT_PUBLIC_*, so it never
// ships to the browser) and forwards requests to the FastAPI backend.
//
// Next.js route handlers under app/api/** call this so the browser only
// ever talks to our own origin, never to the FastAPI service directly.

const AGENT_API_URL = process.env.AGENT_API_URL ?? "http://localhost:8787";
const AGENT_API_KEY = process.env.AGENT_API_KEY;

export async function proxyToAgent(path: string, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");
  if (AGENT_API_KEY) headers.set("X-API-Key", AGENT_API_KEY);

  const upstream = await fetch(`${AGENT_API_URL}${path}`, {
    ...init,
    headers,
    // Never cache agent responses — they're per-request and can contain
    // freshly-generated text tied to the caller's own data.
    cache: "no-store",
  });

  const body = await upstream.text();
  return new Response(body, {
    status: upstream.status,
    headers: { "Content-Type": "application/json" },
  });
}
