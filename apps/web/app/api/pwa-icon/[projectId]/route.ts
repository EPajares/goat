import { isAllowedIconSize, isIconSource } from "@/lib/pwa/icon";
import { renderProjectIcon } from "@/lib/pwa/serve-icon";

export const runtime = "nodejs";

export async function GET(request: Request, props: { params: Promise<{ projectId: string }> }): Promise<Response> {
  const params = await props.params;
  const searchParams = new URL(request.url).searchParams;
  const size = Number(searchParams.get("size") ?? "192");
  if (!isAllowedIconSize(size)) {
    return new Response("Invalid size. Allowed: 48, 96, 180, 192, 512.", { status: 400 });
  }
  const source = searchParams.get("source") ?? "app";
  if (!isIconSource(source)) {
    return new Response("Invalid source. Allowed: app, favicon.", { status: 400 });
  }

  return renderProjectIcon(params.projectId, size, source);
}
