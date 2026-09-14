import { proxyToAgent } from "@/lib/agent-proxy";

export async function GET() {
  return proxyToAgent("/api/impact-stats");
}
