import { apiRequestAuth } from "@/lib/api/fetcher";
import type { LayerSharedWith } from "@/lib/validations/layer";
import type { ProjectSharedWith } from "@/lib/validations/project";

const ACCOUNTS_BASE = process.env.NEXT_PUBLIC_ACCOUNTS_API_URL;
export const ACCOUNTS_ENABLED = Boolean(ACCOUNTS_BASE);

export const SHARE_API_BASE_URL = ACCOUNTS_ENABLED ? new URL("api/v1/share", ACCOUNTS_BASE!).href : "";

const ACCOUNTS_DISABLED_ERROR = { error: "ACCOUNTS_DISABLED" } as const;

const shareItem = async (
  itemType: "project" | "layer",
  itemId: string,
  payload: ProjectSharedWith | LayerSharedWith
) => {
  if (!ACCOUNTS_ENABLED) throw ACCOUNTS_DISABLED_ERROR;

  const params = new URLSearchParams();
  payload.organizations?.forEach((o) => params.append("organization_ids", o.id));
  payload.teams?.forEach((t) => params.append("team_ids", t.id));

  const qs = params.toString();
  const url = `${SHARE_API_BASE_URL}/${itemType}/${itemId}${qs ? `?${qs}` : ""}`;

  const response = await apiRequestAuth(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    try {
      throw await response.json();
    } catch {
      throw new Error(`Failed to share ${itemType}`);
    }
  }
  return await response.json();
};

export const shareProject = async (projectId: string, payload: ProjectSharedWith) => {
  return shareItem("project", projectId, payload);
};

export const shareLayer = async (layerId: string, payload: LayerSharedWith) => {
  return shareItem("layer", layerId, payload);
};
