import { apiRequestAuth } from "@/lib/api/fetcher";
import type { PostActiveMobilityAndCarCatchmentArea, PostPTCatchmentArea } from "@/lib/validations/tools";

const ACTIVE_MOBILITY_CATCHMENT_AREA_API_BASE_URL = new URL(
  "api/v2/active-mobility/catchment-area",
  process.env.NEXT_PUBLIC_API_URL
).href;

const CAR_CATCHMENT_AREA_API_BASE_URL = new URL(
  "api/v2/motorized-mobility/car/catchment-area",
  process.env.NEXT_PUBLIC_API_URL
).href;

const PT_CATCHMENT_AREA_API_BASE_URL = new URL(
  "api/v2/motorized-mobility/pt/catchment-area",
  process.env.NEXT_PUBLIC_API_URL
).href;

export const computeActiveMobilityCatchmentArea = async (
  body: PostActiveMobilityAndCarCatchmentArea,
  projectId: string
) => {
  const response = await apiRequestAuth(
    `${ACTIVE_MOBILITY_CATCHMENT_AREA_API_BASE_URL}?project_id=${projectId}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }
  );
  if (!response.ok) {
    throw new Error("Failed to compute active mobility catchment area");
  }
  return await response.json();
};

export const computeCarCatchmentArea = async (
  body: PostActiveMobilityAndCarCatchmentArea,
  projectId: string
) => {
  const response = await apiRequestAuth(`${CAR_CATCHMENT_AREA_API_BASE_URL}?project_id=${projectId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error("Failed to compute car catchment area");
  }
  return await response.json();
};

export const computePTCatchmentArea = async (body: PostPTCatchmentArea, projectId: string) => {
  const response = await apiRequestAuth(`${PT_CATCHMENT_AREA_API_BASE_URL}?project_id=${projectId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error("Failed to compute PT catchment area");
  }
  return await response.json();
};
