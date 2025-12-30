import useSWR from "swr";

import { apiRequestAuth, fetcher } from "@/lib/api/fetcher";
import { PROCESSES_API_BASE_URL } from "@/lib/api/processes";
import { GEOAPI_BASE_URL } from "@/lib/constants";
import type { PaginatedQueryParams } from "@/lib/validations/common";
import type {
  ClassBreaks,
  CreateLayerFromDataset,
  CreateRasterLayer,
  DatasetCollectionItems,
  DatasetDownloadRequest,
  DatasetMetadataAggregated,
  GetCollectionItemsQueryParams,
  GetDatasetSchema,
  GetLayerUniqueValuesQueryParams,
  Layer,
  LayerClassBreaks,
  LayerPaginated,
  LayerQueryables,
  LayerUniqueValuesPaginated,
  PostDataset,
} from "@/lib/validations/layer";

export const LAYERS_API_BASE_URL = new URL("api/v2/layer", process.env.NEXT_PUBLIC_API_URL).href;
export const COLLECTIONS_API_BASE_URL = `${GEOAPI_BASE_URL}/collections`;

/**
 * Fetcher for OGC API Processes execution endpoints (POST requests)
 */
const processExecuteFetcher = async ([url, body]: [string, object]) => {
  const response = await apiRequestAuth(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.detail || error.detail || "Process execution failed");
  }
  return response.json();
};

export const useLayers = (queryParams?: PaginatedQueryParams, payload: GetDatasetSchema = {}) => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<LayerPaginated>(
    [`${LAYERS_API_BASE_URL}`, queryParams, payload],
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

export const useCatalogLayers = (queryParams?: PaginatedQueryParams, payload: GetDatasetSchema = {}) => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<LayerPaginated>(
    [`${LAYERS_API_BASE_URL}/catalog`, queryParams, payload],
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

export const useMetadataAggregated = (payload: GetDatasetSchema = {}) => {
  const { data, isLoading, error, mutate } = useSWR<DatasetMetadataAggregated>(
    [`${LAYERS_API_BASE_URL}/metadata/aggregate`, null, payload],
    fetcher
  );
  return { metadata: data, isLoading, isError: error, mutate };
};

export const useDataset = (datasetId: string) => {
  const { data, isLoading, error, mutate } = useSWR<Layer>(
    () => (datasetId ? [`${LAYERS_API_BASE_URL}/${datasetId}`] : null),
    fetcher
  );
  return { dataset: data, isLoading, isError: error, mutate };
};

export const getDataset = async (datasetId: string): Promise<Layer> => {
  // The reason why getDataset is used instead of useDataset is when you want to get the data inside a function
  const response = await apiRequestAuth(`${LAYERS_API_BASE_URL}/${datasetId}`, {
    method: "GET",
  });
  if (!response.ok) {
    throw new Error("Failed to get dataset");
  }
  return await response.json();
};

export const updateDataset = async (datasetId: string, payload: PostDataset) => {
  const response = await apiRequestAuth(`${LAYERS_API_BASE_URL}/${datasetId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json",
    },
  });
  if (!response.ok) {
    await response.json();
  }
  return response;
};

export const updateLayerDataset = async (
  layerId: string,
  options?: { s3_key?: string; refresh_wfs?: boolean }
) => {
  const url = new URL(`${LAYERS_API_BASE_URL}/${layerId}/dataset`);
  if (options?.s3_key) {
    url.searchParams.append("s3_key", options.s3_key);
  }
  if (options?.refresh_wfs) {
    url.searchParams.append("refresh_wfs", "true");
  }
  const response = await apiRequestAuth(url.toString(), {
    method: "PUT",
  });
  if (!response.ok) {
    throw new Error("Failed to update layer dataset");
  }
  return await response.json();
};

export const useDatasetCollectionItems = (datasetId: string, queryParams?: GetCollectionItemsQueryParams) => {
  const { data, isLoading, error, mutate } = useSWR<DatasetCollectionItems>(
    () => (datasetId ? [`${COLLECTIONS_API_BASE_URL}/${datasetId}/items`, queryParams] : null),
    fetcher
  );
  return { data, isLoading, isError: error, mutate };
};

export const useLayerQueryables = (layerId: string) => {
  const { data, isLoading, error } = useSWR<LayerQueryables>(
    () => (layerId ? [`${COLLECTIONS_API_BASE_URL}/${layerId}/queryables`] : null),
    fetcher
  );
  return { queryables: data, isLoading, isError: error };
};

//TODO: remove this hook and use useLayerQueryables instead
export const useLayerKeys = (layerId: string) => {
  const { data, isLoading, error } = useSWR<LayerPaginated>(
    [`${COLLECTIONS_API_BASE_URL}/${layerId}/queryables`],
    fetcher
  );
  return { data, isLoading, error };
};

export const useLayerClassBreaks = (
  layerId: string,
  operation?: ClassBreaks,
  column?: string,
  breaks?: number
) => {
  const { data, isLoading, error } = useSWR<LayerClassBreaks>(
    () =>
      operation && column && breaks
        ? [
            `${PROCESSES_API_BASE_URL}/class-breaks/execution`,
            {
              inputs: {
                collection: layerId,
                attribute: column,
                method: operation,
                breaks: breaks,
              },
            },
          ]
        : null,
    processExecuteFetcher
  );
  return { classBreaks: data, isLoading, isError: error };
};

export const deleteLayer = async (id: string) => {
  try {
    await apiRequestAuth(`${LAYERS_API_BASE_URL}/${id}`, {
      method: "DELETE",
    });
  } catch (error) {
    console.error(error);
    throw Error(`deleteLayer: unable to delete project with id ${id}`);
  }
};

/**
 * Create a new layer from a dataset.
 * Layer type (feature or table) is auto-detected based on geometry presence.
 * CSV/Excel with WKT geometry columns will become feature layers.
 */
export const createLayer = async (payload: CreateLayerFromDataset, projectId?: string) => {
  const url = new URL(`${LAYERS_API_BASE_URL}/internal`);
  if (projectId) {
    url.searchParams.append("project_id", projectId);
  }
  const response = await apiRequestAuth(url.toString(), {
    method: "POST",
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json",
    },
  });
  if (!response.ok) {
    throw new Error("Failed to create layer");
  }
  return await response.json();
};

export const createRasterLayer = async (payload: CreateRasterLayer, projectId?: string) => {
  const url = new URL(`${LAYERS_API_BASE_URL}/raster`);
  if (projectId) {
    url.searchParams.append("project_id", projectId);
  }
  const response = await apiRequestAuth(url.toString(), {
    method: "POST",
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json",
    },
  });
  if (!response.ok) {
    throw new Error("Failed to create raster layer");
  }
  return await response.json();
};

export const getLayerClassBreaks = async (
  layerId: string,
  operation: ClassBreaks,
  column: string,
  breaks: number
): Promise<LayerClassBreaks> => {
  const response = await apiRequestAuth(`${PROCESSES_API_BASE_URL}/class-breaks/execution`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      inputs: {
        collection: layerId,
        attribute: column,
        method: operation,
        breaks: breaks,
      },
    }),
  });
  if (!response.ok) {
    throw new Error("Failed to get class breaks");
  }
  return await response.json();
};

export const getLayerUniqueValues = async (
  layerId: string,
  column: string,
  size?: number
): Promise<LayerUniqueValuesPaginated> => {
  const response = await apiRequestAuth(`${PROCESSES_API_BASE_URL}/unique-values/execution`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      inputs: {
        collection: layerId,
        attribute: column,
        limit: size || 100,
      },
    }),
  });
  if (!response.ok) {
    throw new Error("Failed to get unique values");
  }
  // Transform OGC Processes response to legacy paginated format
  const result = await response.json();
  return {
    items: result.values.map((v: { value: string | number; count: number }) => ({
      value: String(v.value),
      count: v.count,
    })),
    total: result.total,
    page: 1,
    size: result.values.length,
    pages: 1,
  };
};

/**
 * Transform OGC Processes unique-values response to legacy paginated format
 */
const transformUniqueValuesResponse = (result: {
  values: { value: string | number | null; count: number }[];
  total: number;
}): LayerUniqueValuesPaginated => ({
  items: result.values.map((v) => ({
    value: String(v.value ?? ""),
    count: v.count,
  })),
  total: result.total,
  page: 1,
  size: result.values.length,
  pages: 1,
});

export const useUniqueValues = (layerId: string, column: string, page?: number) => {
  const offset = page ? (page - 1) * 50 : 0;
  const { data, isLoading, error } = useSWR<LayerUniqueValuesPaginated>(
    layerId && column
      ? [
          `${PROCESSES_API_BASE_URL}/unique-values/execution`,
          {
            inputs: {
              collection: layerId,
              attribute: column,
              limit: 50,
              offset: offset,
            },
          },
        ]
      : null,
    async ([url, body]: [string, object]) => {
      const response = await apiRequestAuth(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) throw new Error("Failed to get unique values");
      const result = await response.json();
      return transformUniqueValuesResponse(result);
    }
  );
  return { data, isLoading, error };
};

export const useLayerUniqueValues = (
  layerId: string,
  column: string,
  queryParams?: GetLayerUniqueValuesQueryParams
) => {
  const limit = queryParams?.size || 50;
  const offset = queryParams?.page ? (queryParams.page - 1) * limit : 0;
  const { data, isLoading, error, mutate, isValidating } = useSWR<LayerUniqueValuesPaginated>(
    layerId && column
      ? [
          `${PROCESSES_API_BASE_URL}/unique-values/execution`,
          {
            inputs: {
              collection: layerId,
              attribute: column,
              order: queryParams?.order || "descendent",
              limit: limit,
              offset: offset,
              ...(queryParams?.query && { filter: queryParams.query }),
            },
          },
        ]
      : null,
    async ([url, body]: [string, object]) => {
      const response = await apiRequestAuth(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) throw new Error("Failed to get unique values");
      const result = await response.json();
      const transformed = transformUniqueValuesResponse(result);
      // Add proper pagination info
      transformed.page = queryParams?.page || 1;
      transformed.size = limit;
      transformed.pages = Math.ceil(transformed.total / limit);
      return transformed;
    }
  );
  return { data, isLoading, error, mutate, isValidating };
};

/**
 * Start a dataset export job. Returns a job_id that can be polled for completion.
 * When job is finished, use getExportDownloadUrl to get the download URL.
 */
export const startDatasetExport = async (payload: DatasetDownloadRequest): Promise<{ job_id: string }> => {
  const response = await apiRequestAuth(`${LAYERS_API_BASE_URL}/${payload.id}/export`, {
    method: "POST",
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json",
    },
  });
  if (!response.ok) {
    throw new Error("Failed to start export job");
  }
  return await response.json();
};

export const useClassBreak = (layerId: string, operation: string, column: string, breaks: number) => {
  const { data, isLoading, error } = useSWR<LayerClassBreaks>(
    layerId && operation && column && breaks
      ? [
          `${PROCESSES_API_BASE_URL}/class-breaks/execution`,
          {
            inputs: {
              collection: layerId,
              attribute: column,
              method: operation,
              breaks: breaks,
            },
          },
        ]
      : null,
    processExecuteFetcher
  );
  return { data, isLoading, error };
};
