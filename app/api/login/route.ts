import { NextResponse } from "next/server";

import { expectedSessionToken, SESSION_COOKIE_NAME } from "@/lib/dashboard-auth";

export async function POST(req: Request) {
  const { password } = (await req.json()) as { password?: string };
  const expected = await expectedSessionToken();

  if (!expected) return NextResponse.json({ ok: true }); // auth disabled

  const configured = process.env.DASHBOARD_PASSWORD ?? "";
  const valid =
    typeof password === "string" &&
    password.length === configured.length &&
    password === configured;

  if (!valid) {
    return NextResponse.json({ ok: false }, { status: 401 });
  }

  const res = NextResponse.json({ ok: true });
  res.cookies.set(SESSION_COOKIE_NAME, expected, {
    httpOnly: true,
    secure: true,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 7, // 7 days
  });
  return res;
}
