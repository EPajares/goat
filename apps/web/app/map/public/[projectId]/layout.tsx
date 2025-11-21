import { API_BASE_URL, APP_URL } from "@/lib/constants";
import { getLocalizedMetadata } from "@/lib/metadata";
import type { ProjectPublic } from "@/lib/validations/project";

export async function generateMetadata({ params: { projectId, lng } }) {
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
    // Swallow the error to avoid breaking metadata generation
    console.error("Failed to fetch public project:", err);
  }

  if (publicProject?.config?.project?.name && lng) {
    const title = `${publicProject.config.project.name} | GOAT`;
    const url = `${APP_URL}/${lng}/map/public/${projectId}`;

    return getLocalizedMetadata(
      lng,
      {
        en: { title },
        de: { title },
      },
      {
        openGraphUrl: url,
        robotsIndex: true,
      }
    );
  }

  return {};
}

export default function PageLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
