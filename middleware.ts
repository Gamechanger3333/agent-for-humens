import { NextResponse, type NextRequest } from "next/server";

import { expectedSessionToken, SESSION_COOKIE_NAME } from "@/lib/dashboard-auth";

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Always let the login page and its own API route through.
  if (pathname === "/login" || pathname === "/api/login") {
    return NextResponse.next();
  }

  const expected = await expectedSessionToken();
  if (!expected) return NextResponse.next(); // no DASHBOARD_PASSWORD set -> open

  const cookie = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  if (cookie === expected) return NextResponse.next();

  const loginUrl = new URL("/login", request.url);
  loginUrl.searchParams.set("next", pathname);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  // Guard everything except Next's own static/image assets.
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
