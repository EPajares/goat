import { afterAll, afterEach, describe, expect, it, vi } from "vitest";

// `API_BASE_URL` is read from `process.env.NEXT_PUBLIC_API_URL` at
// module-evaluation time in lib/constants, so the env var must be set
// before the route (and its imports) load — hence `vi.hoisted`, which
// vitest hoists above the imports below. The previous value is captured
// and restored in `afterAll` to avoid leaking this mutation into other
// test files sharing the worker process.
const PREV_API_URL = vi.hoisted(() => {
  const prev = process.env.NEXT_PUBLIC_API_URL;
  process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000";
  return prev;
});

import { GET } from "@/app/map/public/[projectId]/manifest.webmanifest/route";

const PROJECT_ID = "11111111-1111-1111-1111-111111111111";
const DECOY_PAYLOAD_ID = "99999999-9999-9999-9999-999999999999";
const params = { params: Promise.resolve({ projectId: PROJECT_ID }) };

function stubProjectFetch(ok = true) {
  vi.stubGlobal("fetch", vi.fn(async () =>
    ok
      ? new Response(
          JSON.stringify({
            config: {
              project: {
                id: DECOY_PAYLOAD_ID,
                name: "Test Dashboard",
                builder_config: { settings: { primary_color: "#ffcc00" } },
              },
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      : new Response("nope", { status: 404 })
  ));
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

afterAll(() => {
  if (PREV_API_URL === undefined) delete process.env.NEXT_PUBLIC_API_URL;
  else process.env.NEXT_PUBLIC_API_URL = PREV_API_URL;
});

describe("GET manifest.webmanifest", () => {
  it("serves a canonical-host manifest", async () => {
    vi.stubEnv("NEXT_PUBLIC_APP_URL", "https://goat.plan4better.de");
    stubProjectFetch();
    const res = await GET(
      new Request(`https://goat.plan4better.de/map/public/${PROJECT_ID}/manifest.webmanifest`, {
        headers: { host: "goat.plan4better.de" },
      }),
      params
    );
    expect(res.status).toBe(200);
    expect(res.headers.get("Content-Type")).toBe("application/manifest+json");
    expect(res.headers.get("Cache-Control")).toBe("public, s-maxage=3600, stale-while-revalidate=86400");
    const manifest = await res.json();
    expect(manifest.name).toBe("Test Dashboard");
    expect(manifest.start_url).toBe(`/map/public/${PROJECT_ID}`);
    expect(manifest.id).toBe(PROJECT_ID);
    expect(manifest.icons[0].src).toBe(`/api/pwa-icon/${PROJECT_ID}?size=192`);
  });

  it("serves a root-scoped manifest on custom domains", async () => {
    vi.stubEnv("NEXT_PUBLIC_APP_URL", "https://goat.plan4better.de");
    stubProjectFetch();
    const res = await GET(
      new Request(`https://dashboards.client.com/manifest.webmanifest`, {
        headers: { host: "dashboards.client.com" },
      }),
      params
    );
    const manifest = await res.json();
    expect(manifest.start_url).toBe("/");
    expect(manifest.scope).toBe("/");
  });

  it("404s when core returns a 200 with an unparseable body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("<html>gateway error</html>", { status: 200 }))
    );
    const res = await GET(
      new Request(`https://goat.plan4better.de/map/public/${PROJECT_ID}/manifest.webmanifest`),
      params
    );
    expect(res.status).toBe(404);
  });

  it("404s for unknown projects", async () => {
    stubProjectFetch(false);
    const res = await GET(
      new Request(`https://goat.plan4better.de/map/public/${PROJECT_ID}/manifest.webmanifest`),
      params
    );
    expect(res.status).toBe(404);
  });

  it("404s when the core fetch throws (network error)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("ECONNREFUSED");
      })
    );
    const res = await GET(
      new Request(`https://goat.plan4better.de/map/public/${PROJECT_ID}/manifest.webmanifest`),
      params
    );
    expect(res.status).toBe(404);
    expect(await res.text()).not.toContain("DIAG");
  });
});
