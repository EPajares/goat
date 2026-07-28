import { headers } from "next/headers";

import { API_BASE_URL, APP_URL } from "@/lib/constants";
import { getLocalizedMetadata } from "@/lib/metadata";
import { isCustomDomainHost } from "@/lib/pwa/manifest";
import type { ProjectPublic } from "@/lib/validations/project";

export async function generateMetadata(props) {
  const params = await props.params;

  const {
    projectId
  } = params;

  const lng = "en";
  const PROJECTS_API_BASE_URL = new URL("api/v2/project", API_BASE_URL).href;
  let publicProject: ProjectPublic | null = null;
  try {
    const res = await fetch(`${PROJECTS_API_BASE_URL}/${projectId}/public`, {
      cache: "no-store",
    });

    if (res.ok) {
      publicProject = await res.json();
    }
  } catch (err) {
    console.error("Failed to fetch public project:", err);
  }

  if (publicProject?.config?.project?.name) {
    const title = publicProject.config.project.name;
    const builderSettings = publicProject.config.project.builder_config?.settings;
    const ogImageUrl = builderSettings?.og_image_url;
    const metaDescription = builderSettings?.meta_description;

    // Use the request's Host header so OG previews on a custom domain
    // show that domain, not the canonical app URL.
    const headersList = await headers();
    const reqHost = headersList.get("host");
    const protocol = headersList.get("x-forwarded-proto") ?? "https";
    const fallbackUrl = APP_URL ?? "";
    let baseUrl: string;
    try {
      baseUrl = reqHost ? `${protocol}://${reqHost}` : fallbackUrl;
    } catch {
      baseUrl = fallbackUrl;
    }

    // On a custom domain the public path is hidden by middleware rewrite —
    // the user-visible URL is just `/`. On the canonical host we still
    // show the full path. Distinguish by comparing host.
    const isCustomDomain = isCustomDomainHost(reqHost);
    const url = isCustomDomain ? `${baseUrl}/` : `${baseUrl}/map/public/${projectId}`;

    const overrides: { title: string; description?: string; image?: string } = { title };
    if (metaDescription) overrides.description = metaDescription;
    if (ogImageUrl) overrides.image = ogImageUrl;

    const metadata = getLocalizedMetadata(
      lng,
      {
        en: overrides,
        de: overrides,
      },
      {
        openGraphUrl: url,
        robotsIndex: true,
      }
    );

    // Manifest URL must be host-aware: on custom domains the middleware
    // rewrite maps <domain>/manifest.webmanifest to this project's route.
    const manifestUrl = isCustomDomain
      ? `${baseUrl}/manifest.webmanifest`
      : `${baseUrl}/map/public/${projectId}/manifest.webmanifest`;

    return {
      ...metadata,
      icons: {
        // Served resized to a multiple of 48px — Google's favicon crawler
        // ignores smaller icons and falls back to /favicon.ico.
        icon: {
          url: `/api/pwa-icon/${projectId}?size=96&source=favicon`,
          sizes: "96x96",
          type: "image/png",
        },
        apple: `/api/pwa-icon/${projectId}?size=180`,
      },
      manifest: manifestUrl,
      // iOS ignores most of the manifest; these meta tags carry the
      // installed name and standalone behavior there.
      appleWebApp: { capable: true, title, statusBarStyle: "default" },
    };
  }

  return {};
}

export default function PageLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
