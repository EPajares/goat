import useSWR from "swr";

import { apiRequestAuth, fetcher } from "@/lib/api/fetcher";
import type { PaginatedQueryParams } from "@/lib/validations/common";
import type {
  ClassBreaks,
  CreateLayerFromDataset,
  CreateRasterLayer,
  DatasetCollectionItems,
  DatasetDownloadRequest,
  DatasetMetadataAggregated,
  ExternalDatasetFeatureUrl,
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
export const COLLECTIONS_API_BASE_URL = new URL("collections", process.env.NEXT_PUBLIC_GEOAPI_URL).href;

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
}

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

export const updateLayerDataset = async (layerId: string, datasetId: string, s3_key: string) => {
  const url = new URL(`${LAYERS_API_BASE_URL}/${layerId}/dataset`);
  if (datasetId) {
    url.searchParams.append('dataset_id', datasetId);
  }
  if (s3_key) {
    url.searchParams.append('s3_key', s3_key);
  }
  const response = await apiRequestAuth(url.toString(), {
    method: "PUT",
  });
  if (!response.ok) {
    throw new Error("Failed to update layer dataset");
  }
  return await response.json();
}

export const useDatasetCollectionItems = (datasetId: string, queryParams?: GetCollectionItemsQueryParams) => {
  const collectionId = `user_data.${datasetId.replace(/-/g, "")}`;
  const { data, isLoading, error, mutate } = useSWR<DatasetCollectionItems>(
    () => (datasetId ? [`${COLLECTIONS_API_BASE_URL}/${collectionId}/items`, queryParams] : null),
    fetcher
  );
  return { data, isLoading, isError: error, mutate };
};

export const useLayerQueryables = (layerId: string) => {
  // remove dashes from layerId UUID
  const _layerId = `user_data.${layerId.replace(/-/g, "")}`;
  const { data, isLoading, error } = useSWR<LayerQueryables>(
    () => (layerId ? [`${COLLECTIONS_API_BASE_URL}/${_layerId}/queryables`] : null),
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
        ? [`${LAYERS_API_BASE_URL}/${layerId}/class-breaks/${operation}/${column}?breaks=${breaks}`]
        : null,
    fetcher
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

export const createFeatureLayer = async (payload: CreateLayerFromDataset, projectId?: string) => {
  const url = new URL(`${LAYERS_API_BASE_URL}/feature-standard`);
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
    throw new Error("Failed to create feature layer");
  }
  return await response.json();
};

export const createTableLayer = async (payload: CreateLayerFromDataset, projectId?: string) => {
  const url = new URL(`${LAYERS_API_BASE_URL}/table`);
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
    throw new Error("Failed to create table layer");
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
}


export const layerFeatureUrlUpload = async (payload: ExternalDatasetFeatureUrl) => {
  const response = await apiRequestAuth(`${LAYERS_API_BASE_URL}/file-upload-external-service`, {
    method: "POST",
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json",
    },
  });
  if (!response.ok) {
    throw new Error("Failed to upload external dataset feature url");
  }
  return await response.json();
};

export const getLayerClassBreaks = async (
  layerId: string,
  operation: ClassBreaks,
  column: string,
  breaks: number
): Promise<LayerClassBreaks> => {
  const response = await apiRequestAuth(
    `${LAYERS_API_BASE_URL}/${layerId}/class-breaks/${operation}/${column}?breaks=${breaks}`,
    {
      method: "GET",
    }
  );
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
  const response = await apiRequestAuth(
    `${LAYERS_API_BASE_URL}/${layerId}/unique-values/${column}${size ? `?size=${size}` : ""}`,
    {
      method: "GET",
    }
  );
  if (!response.ok) {
    throw new Error("Failed to get unique values");
  }
  return await response.json();
};

export const useUniqueValues = (layerId: string, column: string, page?: number) => {
  const { data, isLoading, error } = useSWR<LayerUniqueValuesPaginated>(
    [`${LAYERS_API_BASE_URL}/${layerId}/unique-values/${column}${page ? `?page=${page}` : ""}`],
    fetcher
  );
  return { data, isLoading, error };
};

export const useLayerUniqueValues = (
  layerId: string,
  column: string,
  queryParams?: GetLayerUniqueValuesQueryParams
) => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<LayerUniqueValuesPaginated>(
    [`${LAYERS_API_BASE_URL}/${layerId}/unique-values/${column}`, queryParams],
    fetcher
  );
  return { data, isLoading, error, mutate, isValidating };
};

export const downloadDataset = async (payload: DatasetDownloadRequest) => {
  const response = await apiRequestAuth(`${LAYERS_API_BASE_URL}/${payload.id}/export`, {
    method: "POST",
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json",
    },
  });
  if (!response.ok) {
    throw new Error("Failed to download layer");
  }
  return await response.blob();
};
export const useClassBreak = (layerId: string, operation: string, column: string, breaks: number) => {
  const { data, isLoading, error } = useSWR<Record<string, number>>(
    [`${LAYERS_API_BASE_URL}/${layerId}/class-breaks/${operation}/${column}?breaks=${breaks}`],
    fetcher
  );
  return { data, isLoading, error };
};
