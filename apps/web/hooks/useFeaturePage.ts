import { useCallback, useEffect, useMemo, useState } from "react";

import { useDatasetCollectionItems } from "@/lib/api/layers";
import { offsetToPage } from "@/lib/utils/pagination";
import type { GetCollectionItemsQueryParams } from "@/lib/validations/layer";

import useLayerFields from "@/hooks/map/CommonHooks";

type UseFeaturePageOptions = {
  limit?: number;
  /** CQL filter object, e.g. a project layer's saved query. */
  filter?: object;
};

/**
 * Fields plus one page of features for a layer, with the paging handlers
 * `TablePagination` expects. Shared by the read-only feature views (dataset
 * detail tab, view-data modal), which all fetched and paged identically.
 */
export const useFeaturePage = (datasetId: string, options?: UseFeaturePageOptions) => {
  const limit = options?.limit ?? 50;
  const { layerFields: fields, isLoading: areFieldsLoading } = useLayerFields(datasetId, undefined);

  const serializedFilter = useMemo(
    () => (options?.filter ? JSON.stringify(options.filter) : undefined),
    [options?.filter]
  );

  const [queryParams, setQueryParams] = useState<GetCollectionItemsQueryParams>(() => ({
    limit,
    offset: 0,
    ...(serializedFilter ? { filter: serializedFilter } : {}),
  }));

  // Keep the filter in sync without resetting the page on unrelated re-renders.
  useEffect(() => {
    setQueryParams((previous) => {
      if (previous.filter === serializedFilter) return previous;
      const { filter: _dropped, ...rest } = previous;
      return { ...rest, offset: 0, ...(serializedFilter ? { filter: serializedFilter } : {}) };
    });
  }, [serializedFilter]);

  const { data, isLoading } = useDatasetCollectionItems(datasetId, queryParams);

  // Hold the last successful page so the table does not blank out while the
  // next one loads.
  const [displayData, setDisplayData] = useState(data);
  useEffect(() => {
    if (data) setDisplayData(data);
  }, [data]);

  const onPageChange = useCallback((_event: unknown, nextPage: number) => {
    setQueryParams((previous) => ({ ...previous, offset: nextPage * previous.limit }));
  }, []);

  const onRowsPerPageChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const nextLimit = parseInt(event.target.value, 10);
    setQueryParams((previous) => ({ ...previous, limit: nextLimit, offset: 0 }));
  }, []);

  return {
    fields,
    areFieldsLoading,
    data: displayData,
    isLoading,
    rowsPerPage: queryParams.limit,
    page: offsetToPage(queryParams.offset, queryParams.limit),
    totalCount: displayData?.numberMatched ?? 0,
    onPageChange,
    onRowsPerPageChange,
  };
};

export default useFeaturePage;
