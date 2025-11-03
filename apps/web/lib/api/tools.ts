import { apiRequestAuth } from "@/lib/api/fetcher";
import type {
  PostAggregatePoint,
  PostAggregatePolygon,
  PostBuffer,
  PostHeatmapClosestAverage,
  PostHeatmapConnectivity,
  PostHeatmapGravity,
  PostJoin,
  PostNearbyStations,
  PostOevGueteKlassen,
  PostOriginDestinationMatrix,
  PostTripCount,
} from "@/lib/validations/tools";

const TOOLS_API_BASE_URL = new URL("api/v2/tool", process.env.NEXT_PUBLIC_API_URL).href;

const API_BASE_URL = new URL("api/v2", process.env.NEXT_PUBLIC_API_URL).href;

export const computeOevGueteKlassen = async (body: PostOevGueteKlassen, projectId: string) => {
  const response = await apiRequestAuth(
    `${API_BASE_URL}/motorized-mobility/oev-gueteklassen?project_id=${projectId}`,
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

export const computeTripCount = async (body: PostTripCount, projectId: string) => {
  const response = await apiRequestAuth(
    `${API_BASE_URL}/motorized-mobility/trip-count-station?project_id=${projectId}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }
  );
  if (!response.ok) {
    throw new Error("Failed to compute trip count station");
  }
  return await response.json();
};

export const computeJoin = async (body: PostJoin, projectId: string) => {
  const response = await apiRequestAuth(`${TOOLS_API_BASE_URL}/join?project_id=${projectId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error("Failed to compute join");
  }
  return await response.json();
};

export const computeBuffer = async (body: PostBuffer, projectId: string) => {
  const response = await apiRequestAuth(`${TOOLS_API_BASE_URL}/buffer?project_id=${projectId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error("Failed to compute buffer");
  }
  return await response.json();
};

export const computeAggregatePoint = async (body: PostAggregatePoint, projectId: string) => {
  const response = await apiRequestAuth(`${TOOLS_API_BASE_URL}/aggregate-points?project_id=${projectId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error("Failed to compute aggregate");
  }
  return await response.json();
};

export const computeAggregatePolygon = async (body: PostAggregatePolygon, projectId: string) => {
  const response = await apiRequestAuth(`${TOOLS_API_BASE_URL}/aggregate-polygons?project_id=${projectId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error("Failed to compute aggregate");
  }
  return await response.json();
};

export const computeOriginDestination = async (body: PostOriginDestinationMatrix, projectId: string) => {
  const response = await apiRequestAuth(`${TOOLS_API_BASE_URL}/origin-destination?project_id=${projectId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error("Failed to compute origin destination");
  }
  return await response.json();
};

export const computeNearbyStations = async (body: PostNearbyStations, projectId: string) => {
  const response = await apiRequestAuth(
    `${API_BASE_URL}/motorized-mobility/nearby-station-access?project_id=${projectId}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }
  );
  if (!response.ok) {
    throw new Error("Failed to compute nearby stations access");
  }
  return await response.json();
};

export const computeHeatmapGravity = async (body: PostHeatmapGravity, projectId: string) => {
  const routing = ["public_transport", "car"].includes(body.routing_type)
    ? "motorized-mobility"
    : "active-mobility";
  const response = await apiRequestAuth(`${API_BASE_URL}/${routing}/heatmap-gravity?project_id=${projectId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error("Failed to compute heatmap gravity");
  }
  return await response.json();
};

export const computeHeatmapClosestAverage = async (body: PostHeatmapClosestAverage, projectId: string) => {
  const routing = ["public_transport", "car"].includes(body.routing_type)
    ? "motorized-mobility"
    : "active-mobility";
  const response = await apiRequestAuth(
    `${API_BASE_URL}/${routing}/heatmap-closest-average?project_id=${projectId}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }
  );
  if (!response.ok) {
    throw new Error("Failed to compute heatmap closest average");
  }
  return await response.json();
};

export const computeHeatmapConnectivity = async (body: PostHeatmapConnectivity, projectId: string) => {
  const routing = ["public_transport", "car"].includes(body.routing_type)
    ? "motorized-mobility"
    : "active-mobility";
  const response = await apiRequestAuth(
    `${API_BASE_URL}/${routing}/heatmap-connectivity?project_id=${projectId}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }
  );
  if (!response.ok) {
    throw new Error("Failed to compute heatmap connectivity");
  }
  return await response.json();
};
