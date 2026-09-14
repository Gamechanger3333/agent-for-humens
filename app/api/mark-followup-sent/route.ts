import { proxyToAgent } from "@/lib/agent-proxy";

export async function POST(req: Request) {
  const body = await req.text();
  return proxyToAgent("/api/mark-followup-sent", { method: "POST", body });
}
