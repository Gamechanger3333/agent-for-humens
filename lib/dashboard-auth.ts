// SERVER-ONLY. Used by middleware.ts and app/api/login/route.ts.
//
// A lightweight password gate for the whole dashboard — this is a hackathon
// demo protection (stop a public URL from being used/spammed by strangers),
// not a full auth system. Uses Web Crypto (not Node's `crypto` module) so it
// runs in both the Node and Edge runtimes.

export const SESSION_COOKIE_NAME = "fo_session";

async function hmac(message: string, secret: string): Promise<string> {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(message));
  return Array.from(new Uint8Array(sig))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

/**
 * The token a valid session cookie must equal. `null` means no password is
 * configured — the dashboard is intentionally open (e.g. local dev).
 */
export async function expectedSessionToken(): Promise<string | null> {
  const password = process.env.DASHBOARD_PASSWORD;
  if (!password) return null;
  const secret = process.env.AGENT_API_KEY || "dev-only-fallback-secret";
  return hmac(password, secret);
}
