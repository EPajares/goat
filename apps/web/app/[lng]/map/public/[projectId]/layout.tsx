import { API_BASE_URL, APP_URL } from "@/lib/constants";
import { getLocalizedMetadata } from "@/lib/metadata";

export async function generateMetadata({ params: { projectId, lng } }) {
  const PROJECTS_API_BASE_URL = new URL("api/v2/project", API_BASE_URL).href;
  const publicProject = await fetch(`${PROJECTS_API_BASE_URL}/${projectId}/public`).then((res) => res.json());
  if (publicProject?.config?.project?.name && lng) {
    const title = `${publicProject.config.project.name} | GOAT`;
    const url = `${APP_URL}/${lng}/map/public/${projectId}`;
    return getLocalizedMetadata(
      lng,
      {
        en: {
          title,
        },
        de: {
          title,
        },
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
