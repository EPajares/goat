import { apiRequestAuth } from "@/lib/api/fetcher";
import type { LayerSharedWith } from "@/lib/validations/layer";
import type { ProjectSharedWith } from "@/lib/validations/project";

export const SHARE_API_BASE_URL = new URL("api/v1/share", process.env.NEXT_PUBLIC_ACCOUNTS_API_URL).href;

const shareItem = async (
  itemType: "project" | "layer",
  itemId: string,
  payload: ProjectSharedWith | LayerSharedWith
) => {
  const organizationIdsParams = payload.organizations
    ?.map((organization) => {
      return `organization_ids=${organization.id}`;
    })
    .join("&");
  const teamIdsParams = payload.teams
    ?.map((team) => {
      return `team_ids=${team.id}`;
    })
    .join("&");

  const queryParams = [organizationIdsParams, teamIdsParams].filter(Boolean).join("&");

  const response = await apiRequestAuth(`${SHARE_API_BASE_URL}/${itemType}/${itemId}?${queryParams}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Failed to share ${itemType}`);
  }
  return await response.json();
};

export const shareProject = async (projectId: string, payload: ProjectSharedWith) => {
  return shareItem("project", projectId, payload);
};

export const shareLayer = async (layerId: string, payload: LayerSharedWith) => {
  return shareItem("layer", layerId, payload);
};

