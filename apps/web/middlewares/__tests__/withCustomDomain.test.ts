import type { NextFetchEvent } from "next/server";
import { NextRequest, NextResponse } from "next/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api/customDomainLookup", () => ({
  lookupCustomDomain: vi.fn(),
}));
vi.mock("@/lib/utils/server-env", () => ({
  serverAppUrl: () => "https://goat.plan4better.de",
}));

import { lookupCustomDomain } from "@/lib/api/customDomainLookup";
import { withCustomDomain } from "@/middlewares/withCustomDomain";

const PROJECT_ID = "de4e7a04-e535-47a3-8528-3d3d6e87b1c8";

const next = vi.fn(async () => NextResponse.next());
const middleware = withCustomDomain(next);

function request(url: string): NextRequest {
  return new NextRequest(url, { headers: { host: new URL(url).host } });
}

function run(url: string) {
  return middleware(request(url), {} as NextFetchEvent);
}

function rewriteTarget(res: Awaited<ReturnType<typeof middleware>>): string | null {
  return res instanceof Response ? res.headers.get("x-middleware-rewrite") : null;
}

beforeEach(() => {
  vi.mocked(lookupCustomDomain).mockReset();
  next.mockClear();
});

describe("withCustomDomain", () => {
  it("rewrites the root of a custom domain to the public dashboard", async () => {
    vi.mocked(lookupCustomDomain).mockResolvedValue(PROJECT_ID);
    const res = await run("https://verkehrsinfo-bw.de/");
    expect(rewriteTarget(res)).toContain(`/map/public/${PROJECT_ID}`);
    expect(next).not.toHaveBeenCalled();
  });

  it("rewrites /favicon.ico on a custom domain to the project favicon", async () => {
    vi.mocked(lookupCustomDomain).mockResolvedValue(PROJECT_ID);
    const res = await run("https://verkehrsinfo-bw.de/favicon.ico");
    // Path-based target, deliberately without query params — middleware
    // rewrites drop them for route handlers (vercel/next.js#84448).
    expect(rewriteTarget(res)).toContain(`/api/pwa-icon/${PROJECT_ID}/favicon`);
  });

  it("passes /favicon.ico through on the canonical host", async () => {
    await run("https://goat.plan4better.de/favicon.ico");
    expect(lookupCustomDomain).not.toHaveBeenCalled();
    expect(next).toHaveBeenCalled();
  });

  it("passes /favicon.ico through on an unknown custom host", async () => {
    vi.mocked(lookupCustomDomain).mockResolvedValue(null);
    await run("https://unknown.example.com/favicon.ico");
    expect(next).toHaveBeenCalled();
  });

  it("still passes other static assets through without a lookup", async () => {
    const res = await run("https://verkehrsinfo-bw.de/_next/static/chunks/main.js");
    expect(lookupCustomDomain).not.toHaveBeenCalled();
    expect(next).toHaveBeenCalled();
    expect(rewriteTarget(res)).toBeNull();
  });
});
