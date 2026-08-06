import { renderProjectIcon } from "@/lib/pwa/serve-icon";

export const runtime = "nodejs";

/**
 * Rewrite target for /favicon.ico on custom domains. Size and source are
 * fixed in the path because query params on middleware rewrites are
 * dropped before they reach route handlers (vercel/next.js#84448).
 * 48px = the multiple-of-48 square Google's favicon crawler requires.
 */
export async function GET(_request: Request, props: { params: Promise<{ projectId: string }> }): Promise<Response> {
  const params = await props.params;
  return renderProjectIcon(params.projectId, 48, "favicon");
}
