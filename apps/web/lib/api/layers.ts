import useSWR from "swr";

import { apiRequestAuth, fetcher } from "@/lib/api/fetcher";
import { type Job, PROCESSES_API_BASE_URL, executeProcessAsync } from "@/lib/api/processes";
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
  userId: string,
  options?: { s3_key?: string; refresh_wfs?: boolean }
): Promise<Job> => {
  // Use LayerUpdate process
  const inputs: Record<string, unknown> = {
    layer_id: layerId,
    user_id: userId,
    ...(options?.s3_key && { s3_key: options.s3_key }),
    ...(options?.refresh_wfs && { refresh_wfs: options.refresh_wfs }),
  };

  return executeProcessAsync("LayerUpdate", inputs);
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

export const deleteLayer = async (id: string, userId: string): Promise<Job> => {
  return executeProcessAsync("LayerDelete", {
    layer_id: id,
    user_id: userId,
  });
};

/**
 * Create a new layer from a dataset using OGC API Processes (LayerImport).
 * Supports both S3 file uploads and WFS imports.
 * Layer type (feature or table) is auto-detected based on geometry presence.
 */
export const createLayer = async (
  payload: CreateLayerFromDataset & {
    user_id: string;
    // Optional WFS import fields
    url?: string;
    other_properties?: Record<string, unknown>;
  },
  projectId?: string
): Promise<Job> => {
  // Map to LayerImport process inputs
  const inputs: Record<string, unknown> = {
    user_id: payload.user_id,
    layer_id: crypto.randomUUID(), // Generate new layer ID
    folder_id: payload.folder_id,
    name: payload.name,
    ...(payload.description && { description: payload.description }),
    ...(payload.tags && { tags: payload.tags }),
    ...(projectId && { project_id: projectId }),
    // S3 upload path
    ...(payload.s3_key && { s3_key: payload.s3_key }),
    // WFS import path
    ...(payload.url && { wfs_url: payload.url }),
    ...(payload.other_properties && { other_properties: payload.other_properties }),
  };

  return executeProcessAsync("LayerImport", inputs);
};

/**
 * Create a new raster/external layer (WMS, WMTS, XYZ, COG).
 * These don't upload data, just reference external URLs.
 */
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
 * Start a dataset export job using OGC API Processes.
 * Returns a Job that can be polled for completion.
 * When job is finished, use getExportDownloadUrl to get the download URL.
 */
export const startDatasetExport = async (
  payload: DatasetDownloadRequest & { user_id: string; layer_owner_id: string }
): Promise<Job> => {
  const inputs = {
    user_id: payload.user_id,
    layer_id: payload.id,
    layer_owner_id: payload.layer_owner_id,
    file_type: payload.file_type,
    file_name: payload.file_name,
    ...(payload.crs && { crs: payload.crs }),
    ...(payload.query && { query: payload.query }),
  };

  return executeProcessAsync("LayerExport", inputs);
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
