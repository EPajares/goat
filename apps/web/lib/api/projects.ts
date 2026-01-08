import useSWR from "swr";

import { apiRequestAuth, fetcher } from "@/lib/api/fetcher";
import { PROCESSES_API_BASE_URL } from "@/lib/api/processes";
import type { GetContentQueryParams } from "@/lib/validations/common";
import type {
  AggregationStatsQueryParams,
  AggregationStatsResponse,
  HistogramStatsQueryParams,
  HistogramStatsResponse,
  PostProject,
  Project,
  ProjectLayer,
  ProjectLayerGroup,
  ProjectLayerTreeUpdate,
  ProjectPaginated,
  ProjectPublic,
  ProjectViewState,
} from "@/lib/validations/project";
import type {
  PostScenario,
  ScenarioFeaturePost,
  ScenarioFeatureUpdate,
  ScenarioFeatures,
  ScenarioResponse,
} from "@/lib/validations/scenario";

export const PROJECTS_API_BASE_URL = new URL("api/v2/project", process.env.NEXT_PUBLIC_API_URL).href;

export const useProjects = (queryParams?: GetContentQueryParams) => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<ProjectPaginated>(
    [`${PROJECTS_API_BASE_URL}`, queryParams],
    fetcher
  );
  return {
    projects: data,
    isLoading: isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

export const useProject = (projectId?: string) => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<Project>(
    () => (projectId ? [`${PROJECTS_API_BASE_URL}/${projectId}`] : null),
    fetcher
  );

  return {
    project: data,
    isLoading: isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

export const useProjectLayers = (projectId?: string) => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<ProjectLayer[]>(
    () => (projectId ? [`${PROJECTS_API_BASE_URL}/${projectId}/layer`] : null),
    fetcher
  );

  return {
    layers: data,
    isLoading: isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

export const useProjectLayerGroups = (projectId?: string) => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<ProjectLayerGroup[]>(
    () => (projectId ? [`${PROJECTS_API_BASE_URL}/${projectId}/group`] : null),
    fetcher
  );

  return {
    layerGroups: data,
    isLoading: isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

export const useProjectScenarios = (projectId: string) => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<ScenarioResponse>(
    [`${PROJECTS_API_BASE_URL}/${projectId}/scenario`],
    fetcher
  );
  return {
    scenarios: data,
    isLoading: isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

export const useProjectScenarioFeatures = (projectId: string, scenarioId?: string | null) => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<ScenarioFeatures>(
    () => (scenarioId ? [`${PROJECTS_API_BASE_URL}/${projectId}/scenario/${scenarioId}/features`] : null),
    fetcher
  );
  return {
    scenarioFeatures: data,
    isLoading: isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

export const useProjectInitialViewState = (projectId: string) => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<ProjectViewState>(
    [`${PROJECTS_API_BASE_URL}/${projectId}/initial-view-state`],
    fetcher
  );
  return {
    initialView: data,
    isLoading: isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

export const useProjectLayerChartData = (projectId: string, layerId: number, cumSum: boolean = false) => {
  const { data, isLoading, error, mutate, isValidating } = useSWR(
    [`${PROJECTS_API_BASE_URL}/${projectId}/layer/${layerId}/chart-data?cumsum=${cumSum}`],
    fetcher
  );
  return {
    chartData: data,
    isLoading: isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

/**
 * Hook to get aggregation statistics for a layer using GeoAPI OGC Processes
 * @param layerId - The layer UUID (not layer_project_id)
 * @param queryParams - Query parameters including operation_type, group_by_column_name, etc.
 */
export const useProjectLayerAggregationStats = (
  layerId?: string,
  queryParams?: AggregationStatsQueryParams
) => {
  // Only require layerId and operation_type - group_by_column is optional (for Numbers widget)
  const shouldFetch = layerId && queryParams?.operation_type;

  const { data, isLoading, error, mutate, isValidating } = useSWR<AggregationStatsResponse>(
    shouldFetch
      ? [
          `${PROCESSES_API_BASE_URL}/aggregation-stats/execution`,
          {
            inputs: {
              collection: layerId,
              group_by_column: queryParams.group_by_column_name || undefined,
              operation: queryParams.operation_type,
              operation_column: queryParams.operation_value,
              limit: queryParams.size || 10,
              order: queryParams.order,
              filter: queryParams.query,
            },
          },
        ]
      : null,
    async ([url, body]) => {
      const response = await apiRequestAuth(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail?.detail || error.detail || "Failed to get aggregation stats");
      }
      const result = await response.json();
      // Transform response to match expected format
      return {
        items:
          result.items?.map((item: { grouped_value: string; operation_value: number }) => ({
            grouped_value: item.grouped_value,
            operation_value: item.operation_value,
          })) || [],
        total_items: result.total_items || 0,
        total_count: result.total_count || 0,
      };
    },
    {
      keepPreviousData: true,
    }
  );
  return {
    aggregationStats: data,
    isLoading: isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

/**
 * Hook to get histogram statistics for a layer using GeoAPI OGC Processes
 * @param layerId - The layer UUID (not layer_project_id)
 * @param queryParams - Query parameters including column_name, num_bins, etc.
 */
export const useProjectLayerHistogramStats = (layerId?: string, queryParams?: HistogramStatsQueryParams) => {
  const shouldFetch = layerId && queryParams?.column_name;

  const { data, isLoading, error, mutate, isValidating } = useSWR<HistogramStatsResponse>(
    shouldFetch
      ? [
          `${PROCESSES_API_BASE_URL}/histogram/execution`,
          {
            inputs: {
              collection: layerId,
              column: queryParams.column_name,
              num_bins: queryParams.num_bins || 10,
              filter: queryParams.query,
            },
          },
        ]
      : null,
    async ([url, body]) => {
      const response = await apiRequestAuth(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail?.detail || error.detail || "Failed to get histogram stats");
      }
      const result = await response.json();
      // Response already matches expected format (bins with range and count)
      return {
        bins:
          result.bins?.map((bin: { range: [number, number]; count: number }) => ({
            range: bin.range,
            count: bin.count,
          })) || [],
        missing_count: result.missing_count || 0,
        total_rows: result.total_rows || 0,
      };
    },
    {
      keepPreviousData: true,
    }
  );
  return {
    histogramStats: data,
    isLoading: isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

export const updateProjectInitialViewState = async (projectId: string, payload: ProjectViewState) => {
  const response = await apiRequestAuth(`${PROJECTS_API_BASE_URL}/${projectId}/initial-view-state`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to update project initial view state");
  }
  return await response.json();
};

export const updateProjectLayer = async (projectId: string, layerId: number, payload: ProjectLayer) => {
  const response = await apiRequestAuth(`${PROJECTS_API_BASE_URL}/${projectId}/layer/${layerId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw Error(`Failed to update project layer ${layerId}`);
  }
  return await response.json();
};

export const deleteProjectLayer = async (projectId: string, layerId: number) => {
  const response = await apiRequestAuth(
    `${PROJECTS_API_BASE_URL}/${projectId}/layer?layer_project_id=${layerId}`,
    {
      method: "DELETE",
    }
  );
  if (!response.ok) {
    throw Error(`deleteProjectLayer: unable to delete layer with id ${layerId}`);
  }
  return response;
};

export const addProjectLayers = async (projectId: string, layerIds: string[]) => {
  //todo: fix the api for this. This structure doesn't make sense.
  //layer_ids=1&layer_ids=2&layer_ids=3
  const layerIdsParams = layerIds.map((layerId) => {
    return `layer_ids=${layerId}`;
  });

  const response = await apiRequestAuth(
    `${PROJECTS_API_BASE_URL}/${projectId}/layer?${layerIdsParams.join("&")}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );
  if (!response.ok) {
    throw new Error("Failed to add layers to project");
  }
  return await response.json();
};

export const updateProject = async (projectId: string, payload: PostProject) => {
  const response = await apiRequestAuth(`${PROJECTS_API_BASE_URL}/${projectId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to update project");
  }
  return await response.json();
};

export const updateProjectLayerTree = async (projectId: string, payload: ProjectLayerTreeUpdate) => {
  const response = await apiRequestAuth(`${PROJECTS_API_BASE_URL}/${projectId}/layer-tree`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to update project layer tree structure");
  }
  // 204 No Content usually, returns undefined or empty
  return response;
};

export const createProject = async (payload: PostProject): Promise<Project> => {
  const response = await apiRequestAuth(`${PROJECTS_API_BASE_URL}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to create project");
  }
  return await response.json();
};

export const deleteProject = async (id: string) => {
  const response = await apiRequestAuth(`${PROJECTS_API_BASE_URL}/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw Error(`deleteProject: unable to delete project with id ${id}`);
  }
  return response;
};

export const createProjectScenario = async (projectId: string, payload: PostScenario) => {
  const response = await apiRequestAuth(`${PROJECTS_API_BASE_URL}/${projectId}/scenario`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to create project scenario");
  }
  return await response.json();
};

export const updateProjectScenario = async (projectId: string, scenarioId: string, payload: PostScenario) => {
  const response = await apiRequestAuth(`${PROJECTS_API_BASE_URL}/${projectId}/scenario/${scenarioId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to update project scenario");
  }
  return await response.json();
};

export const deleteProjectScenario = async (projectId: string, scenarioId: string) => {
  try {
    await apiRequestAuth(`${PROJECTS_API_BASE_URL}/${projectId}/scenario/${scenarioId}`, {
      method: "DELETE",
    });
  } catch (error) {
    console.error(error);
    throw Error(`deleteProjectScenario: unable to delete scenario with id ${scenarioId}`);
  }
};

export const deleteProjectScenarioFeature = async (
  projectId: string,
  project_layer_id: number,
  scenarioId: string,
  featureId: string | number,
  h33?: number
) => {
  let url = `${PROJECTS_API_BASE_URL}/${projectId}/layer/${project_layer_id}/scenario/${scenarioId}/features/${featureId}`;

  // H33 is mandatory for user data. It can be undefined for new features only.
  if (h33 !== undefined) {
    url += `?h3_3=${h33}`;
  }

  const response = await apiRequestAuth(url, {
    method: "DELETE",
  });

  if (!response.ok) throw await response.json();
  return response;
};

export const updateProjectScenarioFeatures = async (
  projectId: string,
  project_layer_id: number,
  scenarioId: string,
  payload: ScenarioFeatureUpdate[]
) => {
  const response = await apiRequestAuth(
    `${PROJECTS_API_BASE_URL}/${projectId}/layer/${project_layer_id}/scenario/${scenarioId}/features`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );
  if (!response.ok) {
    throw new Error("Failed to update project scenario features");
  }
  return await response.json();
};

export const createProjectScenarioFeatures = async (
  projectId: string,
  project_layer_id: number,
  scenarioId: string,
  payload: ScenarioFeaturePost[]
) => {
  const response = await apiRequestAuth(
    `${PROJECTS_API_BASE_URL}/${projectId}/layer/${project_layer_id}/scenario/${scenarioId}/features`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );
  if (!response.ok) {
    throw new Error("Failed to create project scenario features");
  }
  return await response.json();
};

export const usePublicProject = (projectId: string) => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<ProjectPublic>(
    `${PROJECTS_API_BASE_URL}/${projectId}/public`,
    fetcher
  );
  return {
    sharedProject: data,
    isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

export const publishProject = async (projectId: string) => {
  const response = await apiRequestAuth(`${PROJECTS_API_BASE_URL}/${projectId}/publish`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Failed to publish project");
  }
  return await response.json();
};

export const unpublishProject = async (projectId: string) => {
  const response = await apiRequestAuth(`${PROJECTS_API_BASE_URL}/${projectId}/unpublish`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Failed to unpublish project");
  }
  return await response.json();
};

export const createProjectLayerGroup = async (
  projectId: string,
  payload: { name: string; parent_id?: number }
) => {
  const response = await apiRequestAuth(`${PROJECTS_API_BASE_URL}/${projectId}/group`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to create project layer group");
  }
  return await response.json();
};

export const updateProjectLayerGroup = async (
  projectId: string,
  groupId: number,
  payload: {
    name?: string;
    parent_id?: number;
    properties?: Record<string, unknown> | null;
    expanded?: boolean;
  }
) => {
  const response = await apiRequestAuth(`${PROJECTS_API_BASE_URL}/${projectId}/group/${groupId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to update project layer group");
  }
  return await response.json();
};

export const deleteProjectLayerGroup = async (projectId: string, groupId: number) => {
  const response = await apiRequestAuth(`${PROJECTS_API_BASE_URL}/${projectId}/group/${groupId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw Error(`Failed to delete project layer group ${groupId}`);
  }
  return response;
};
