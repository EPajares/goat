/**
 * Server-side project icon rendering shared by the pwa-icon route
 * handlers. Node runtime only (fs + sharp) — don't import from client
 * components or edge middleware.
 */

import { promises as fs } from "fs";
import path from "path";

import { API_BASE_URL } from "@/lib/constants";
import { rasterizeToPng, resolveIconUrl } from "@/lib/pwa/icon";
import type { IconSettings, IconSource, PwaIconSize } from "@/lib/pwa/icon";

const GOAT_LOGO_PATH = path.join(process.cwd(), "public/assets/svg/goat-logo.svg");
const CACHE_CONTROL = "public, max-age=3600, s-maxage=86400, stale-while-revalidate=604800";

// Per-process memo of rendered icons. The endpoint is anonymous and each
// render costs a core API call, an icon fetch and a sharp resize — without
// the memo, cheap repeated requests (crawlers, bursts) amplify load onto
// core. Bounded FIFO so a flood of distinct project IDs can't grow it.
const MEMO_TTL_MS = 10 * 60 * 1000;
const MEMO_MAX_ENTRIES = 500;
const iconMemo = new Map<string, { png: Buffer; at: number }>();

function memoGet(key: string): Buffer | null {
  const entry = iconMemo.get(key);
  if (!entry) return null;
  if (Date.now() - entry.at > MEMO_TTL_MS) {
    iconMemo.delete(key);
    return null;
  }
  return entry.png;
}

function memoSet(key: string, png: Buffer): void {
  if (iconMemo.size >= MEMO_MAX_ENTRIES) {
    const oldest = iconMemo.keys().next().value;
    if (oldest !== undefined) iconMemo.delete(oldest);
  }
  iconMemo.set(key, { png, at: Date.now() });
}

export function clearIconCache(): void {
  iconMemo.clear();
}

function pngResponse(png: Buffer): Response {
  return new Response(new Uint8Array(png), {
    status: 200,
    headers: { "Content-Type": "image/png", "Cache-Control": CACHE_CONTROL },
  });
}

async function loadSourceImage(iconUrl: string | null): Promise<Buffer> {
  if (iconUrl) {
    // Relative URLs ("/assets/...") are files in our own public dir;
    // absolute URLs live on the assets store (S3).
    if (iconUrl.startsWith("/")) {
      const publicRoot = path.resolve(process.cwd(), "public");
      const resolved = path.resolve(publicRoot, `.${iconUrl}`);
      if (!resolved.startsWith(publicRoot + path.sep)) {
        throw new Error("icon path escapes public dir");
      }
      return fs.readFile(resolved);
    }
    const res = await fetch(iconUrl);
    if (!res.ok) throw new Error(`icon fetch failed: ${res.status}`);
    return Buffer.from(await res.arrayBuffer());
  }
  return fs.readFile(GOAT_LOGO_PATH);
}

export async function renderProjectIcon(
  projectId: string,
  size: PwaIconSize,
  source: IconSource
): Promise<Response> {
  const memoKey = `${projectId}:${size}:${source}`;
  const memoized = memoGet(memoKey);
  if (memoized) return pngResponse(memoized);

  const projectUrl = `${new URL("api/v2/project", API_BASE_URL).href}/${projectId}/public`;
  let settings: IconSettings | null | undefined = null;
  // A render based on a transient core failure must not be memoized —
  // it would pin the GOAT fallback for the TTL after core recovers.
  let memoizable = true;
  try {
    const projectRes = await fetch(projectUrl, { cache: "no-store" });
    if (!projectRes.ok) return new Response("Project not found", { status: 404 });
    const publicProject = await projectRes.json();
    settings = publicProject?.config?.project?.builder_config?.settings;
  } catch {
    // Core unreachable or malformed payload — a broken upstream must not
    // break installability; serve the GOAT logo.
    settings = null;
    memoizable = false;
  }

  // Broken icons must degrade to the GOAT logo, never to an error —
  // a failing icon must not break installability.
  let png: Buffer;
  try {
    png = await rasterizeToPng(await loadSourceImage(resolveIconUrl(settings, source)), size);
  } catch {
    png = await rasterizeToPng(await fs.readFile(GOAT_LOGO_PATH), size);
  }

  if (memoizable) memoSet(memoKey, png);
  return pngResponse(png);
}
