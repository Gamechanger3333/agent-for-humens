import { proxyToAgent } from "@/lib/agent-proxy";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const days = searchParams.get("days") ?? "4";
  return proxyToAgent(`/api/followups?days=${encodeURIComponent(days)}`);
}
