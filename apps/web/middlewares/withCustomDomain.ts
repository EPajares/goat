/**
 * If the incoming Host header is not the canonical app host, try to
 * resolve it as a customer's custom domain and rewrite the request to
 * the public-dashboard route for the assigned project.
 *
 * Runs first in the stack — withAuth's `publicPaths` ("/map/public")
 * exemption then naturally permits the rewritten request.
 *
 * Unknown hosts fall through to existing routing (typically a 404 from
 * Next.js for an unrecognized origin), which is the desired behavior:
 * we never silently serve someone else's content from an unbound host.
 */

import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { lookupCustomDomain } from "@/lib/api/customDomainLookup";
import { serverAppUrl } from "@/lib/utils/server-env";
import type { MiddlewareFactory } from "@/middlewares/types";

function deriveCanonicalHost(): string | null {
  const url = serverAppUrl();
  if (!url) return null;
  try {
    // hostname (port stripped) — the request host below is compared
    // port-stripped too, and lib/pwa/manifest.ts#isCustomDomainHost
    // must agree with this check.
    return new URL(url).hostname.toLowerCase();
  } catch {
    return null;
  }
}

export const withCustomDomain: MiddlewareFactory = (next) => {
  return async (request: NextRequest, _next) => {
    const host = request.headers.get("host")?.split(":")[0]?.toLowerCase();
    const canonical = deriveCanonicalHost();

    // Canonical host or no Host header → continue normally.
    if (!host || !canonical || host === canonical) {
      return next(request, _next);
    }

    // Static assets and API routes must not be rewritten — they're
    // served verbatim by Next.js / the routing layer. Only the page
    // route(s) and /favicon.ico get rewritten.
    const path = request.nextUrl.pathname;
    const isFavicon = path === "/favicon.ico";
    if (
      !isFavicon &&
      (path.startsWith("/_next/") ||
        path.startsWith("/api/") ||
        // any path with a file extension is almost certainly a static
        // asset (woff2, png, css, js, json, ico, svg, ...).
        /\.[a-z0-9]{2,5}$/i.test(path))
    ) {
      return next(request, _next);
    }

    const projectId = await lookupCustomDomain(host);
    if (!projectId) {
      // Unknown custom host: let the rest of the stack handle it.
      return next(request, _next);
    }

    if (isFavicon) {
      // Serve the project's favicon instead of the bundled GOAT one:
      // crawlers (notably Google's favicon bot) fall back to
      // /favicon.ico when the <link rel="icon"> candidate is unsuitable,
      // and must never see the GOAT icon on a customer domain. The
      // target is path-based — query params on middleware rewrites are
      // dropped before route handlers run (vercel/next.js#84448).
      const url = request.nextUrl.clone();
      url.pathname = `/api/pwa-icon/${projectId}/favicon`;
      url.search = "";
      return NextResponse.rewrite(url);
    }

    // Rewrite to the public-dashboard route. Preserve any sub-path
    // and query string — they should keep working on the customer
    // domain just like on the canonical one.
    const url = request.nextUrl.clone();
    const trailing = url.pathname === "/" ? "" : url.pathname;
    url.pathname = `/map/public/${projectId}${trailing}`;
    return NextResponse.rewrite(url);
  };
};
