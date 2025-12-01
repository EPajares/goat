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
];

const publicPaths = ["/map/public"];

export const withAuth: MiddlewareFactory = (next) => {
  return async (request: NextRequest, _next) => {
    const { pathname, search, origin, basePath } = request.nextUrl;
    
    // Debug logging for production
    console.log("🔐 Auth Middleware - Processing:", {
      pathname,
      authDisabled: !!process.env.NEXT_PUBLIC_AUTH_DISABLED,
      hasNextAuthUrl: !!process.env.NEXTAUTH_URL,
      hasNextAuthSecret: !!process.env.NEXTAUTH_SECRET,
      environment: process.env.NODE_ENV
    });

    if (process.env.NEXT_PUBLIC_AUTH_DISABLED || !process.env.NEXTAUTH_URL || !process.env.NEXTAUTH_SECRET) {
      console.log("❌ Auth bypassed - Missing config:", {
        authDisabled: !!process.env.NEXT_PUBLIC_AUTH_DISABLED,
        missingUrl: !process.env.NEXTAUTH_URL,
        missingSecret: !process.env.NEXTAUTH_SECRET
      });
      return next(request, _next);
    }

    // Skip public paths
    const isPublicPath = publicPaths.some((p) => pathname.startsWith(p));
    if (isPublicPath) {
      console.log("Auth bypassed - public path:", pathname);
      return next(request, _next);
    }

    // Skip if not protected
    const isProtected = protectedPaths.some((p) => pathname.startsWith(p));
    if (!isProtected) {
      console.log("Auth bypassed - unprotected path:", pathname);
      return next(request, _next);
    }

    // Verify secret & token
    const nextAuthSecret = process.env.NEXTAUTH_SECRET;
    if (!nextAuthSecret) {
      return next(request, _next);
    }

    const token = await getToken({ req: request, secret: nextAuthSecret });
    const isAuthorized = !!token && token.error !== "RefreshAccessTokenError";

    console.log("🔐 Auth check result:", {
      pathname,
      hasToken: !!token,
      tokenError: token?.error,
      isAuthorized
    });

    if (isAuthorized) {
      console.log("✅ Auth success - proceeding to next middleware");
      return next(request, _next);
    }

    // Redirect unauthorized user to login
    console.log("🚫 Auth failed - redirecting to login");
    const signInUrl = new URL(`${basePath}/auth/login`, origin);
    signInUrl.searchParams.set("callbackUrl", `${basePath}${pathname}${search}`);
    return NextResponse.redirect(signInUrl);
  };
};
