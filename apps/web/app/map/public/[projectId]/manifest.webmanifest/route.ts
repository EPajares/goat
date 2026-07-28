import { API_BASE_URL } from "@/lib/constants";
import { buildManifest, isCustomDomainHost } from "@/lib/pwa/manifest";

export const runtime = "nodejs";

const CACHE_CONTROL = "public, s-maxage=3600, stale-while-revalidate=86400";

export async function GET(request: Request, props: { params: Promise<{ projectId: string }> }): Promise<Response> {
  const params = await props.params;
  const projectUrl = `${new URL("api/v2/project", API_BASE_URL).href}/${params.projectId}/public`;

  // Network errors, non-ok responses, and unparseable bodies (proxy error
  // page, truncated response) all mean the same thing to the installer:
  // there is no manifest to serve for this project right now.
  let publicProject;
  try {
    const res = await fetch(projectUrl, { cache: "no-store" });
    if (!res.ok) return new Response("Project not found", { status: 404 });
    publicProject = await res.json();
  } catch {
    return new Response("Project not found", { status: 404 });
  }
  const project = publicProject?.config?.project;
  if (!project?.name) {
    return new Response("Project not found", { status: 404 });
  }

  // Use the route param as the id — it's what the client requested and
  // what the icon/scope URLs must match, regardless of payload shape.
  const manifest = buildManifest(
    { id: params.projectId, name: project.name, builder_config: project.builder_config },
    { isCustomDomain: isCustomDomainHost(request.headers.get("host")) }
  );

  return new Response(JSON.stringify(manifest), {
    status: 200,
    headers: {
      "Content-Type": "application/manifest+json",
      "Cache-Control": CACHE_CONTROL,
    },
  });
}
