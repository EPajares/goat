import { getToken } from "next-auth/jwt";
import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import type { MiddlewareFactory } from "@/middlewares/types";

const protectedPaths = [
  "/home",
  "/projects",
  "/datasets",
  "/settings",
  "/map",
  "/onboarding/organization/create",
  "/onboarding/organization/suspended",
  "/onboarding/organization/invite",
];

const publicPaths = ["/map/public", "/print"];

export const withAuth: MiddlewareFactory = (next) => {
  return async (request: NextRequest, _next) => {
    // Check if auth is disabled - handle both actual values and unreplaced placeholders
    const authDisabled = process.env.NEXT_PUBLIC_AUTH_DISABLED;
    const isAuthDisabled =
      authDisabled &&
      authDisabled !== "APP_NEXT_PUBLIC_AUTH_DISABLED" &&
      authDisabled.toLowerCase() === "true";

    if (isAuthDisabled || !process.env.NEXTAUTH_URL || !process.env.NEXTAUTH_SECRET) {
      return next(request, _next);
    }
    const { pathname, search, origin, basePath } = request.nextUrl;

    // Skip public paths
    const isPublicPath = publicPaths.some((p) => pathname.startsWith(p));
    if (isPublicPath) return next(request, _next);

    // Skip if not protected
    const isProtected = protectedPaths.some((p) => pathname.startsWith(p));
    if (!isProtected) return next(request, _next);

    // Verify secret & token
    const nextAuthSecret = process.env.NEXTAUTH_SECRET;
    if (!nextAuthSecret) {
      return next(request, _next);
    }

    const token = await getToken({ req: request, secret: nextAuthSecret });
    const isAuthorized = !!token && token.error !== "RefreshAccessTokenError";

    if (isAuthorized) {
      return next(request, _next);
    }

    // Redirect unauthorized user to login
    const signInUrl = new URL(`${basePath}/auth/login`, origin);
    signInUrl.searchParams.set("callbackUrl", `${basePath}${pathname}${search}`);
    return NextResponse.redirect(signInUrl);
  };
};
