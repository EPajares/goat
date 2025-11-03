/* eslint-disable @typescript-eslint/no-explicit-any */
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState, useCallback } from "react";
import { useMap } from "react-map-gl/maplibre";
import type { ZodSchema } from "zod";

import { getMapExtentCQL } from "@/lib/utils/map/navigate";
import { useAppSelector } from "@/hooks/store/ContextHooks";

interface UseLayerFiltersParams {
  layerId?: number;
}

/**
 * Returns a combined CQL filter from temporary filters in the store,
 * merging per-layer and spatial cross-filters for the specified layer.
 */
function useTemporaryFilters({ layerId }: UseLayerFiltersParams) {
  const { temporaryFilters } = useAppSelector(state => state.map);

  return useMemo(() => {
    if (!layerId) return undefined;

    const nonCross = temporaryFilters
      .filter(f => f.layer_id === layerId)
      .map(f => f.filter);

    const spatialCross = temporaryFilters
      .filter(f => f.layer_id !== layerId && f.spatial_cross_filter)
      .map(f => f.spatial_cross_filter as any);

    const filters = [...nonCross, ...spatialCross];
    if (!filters.length) return undefined;

    return { op: "and", args: filters };
  }, [temporaryFilters, layerId]);
}

interface ChartWidgetResult<TConfig, TQueryParams> {
  config?: TConfig;
  queryParams?: TQueryParams;
  projectId: string;
}

/**
 * Hook to parse config, build and update query params for chart widgets.
 * Applies temporary filters only if options.cross_filter is true.
 */
export function useChartWidget<TConfig, TQueryParams>(
  rawConfig: unknown,
  configSchema: ZodSchema<TConfig>,
  querySchema: ZodSchema<TQueryParams>
): ChartWidgetResult<TConfig, TQueryParams> {
  const { map } = useMap();
  const { projectId } = useParams() as { projectId: string };

  const config = useMemo(() => {
    const result = configSchema.safeParse(rawConfig);
    return result.success ? result.data : undefined;
  }, [rawConfig, configSchema]);

  // Get temporary filters for this layer
  const tempFilters = useTemporaryFilters({ layerId: (config as any)?.setup?.layer_project_id });

  const buildQuery = useCallback((): any | undefined => {
    if (!config) return;

    const base = { ...(config as any).setup, ...(config as any).options };
    const parsed = querySchema.safeParse(base);
    if (!parsed.success) return;

    // Apply cross filters only when enabled
    let cqlQuery;
    if ((config as any).options?.cross_filter && tempFilters) {
      cqlQuery = JSON.parse(JSON.stringify(tempFilters));
    }

    if ((config as any).options?.filter_by_viewport && map) {
      const extentRaw = getMapExtentCQL(map);
      if (extentRaw) {
        const extent = JSON.parse(extentRaw);
        if (cqlQuery && cqlQuery.args) {
          cqlQuery.args.push(extent);
        } else {
          cqlQuery = extent;
        }
      }
    }

    return cqlQuery
      ? { ...parsed.data, query: JSON.stringify(cqlQuery) }
      : (parsed.data as TQueryParams);
  }, [config, map, querySchema, tempFilters]);

  const [queryParams, setQueryParams] = useState<TQueryParams | undefined>(() => buildQuery());

  // Update on config, filters, or map load
  useEffect(() => {
    setQueryParams(buildQuery());
  }, [buildQuery]);

  // Update viewport filter on map moves
  useEffect(() => {
    if (!map || !(config as any)?.options?.filter_by_viewport) return;

    const onMoveEnd = () => setQueryParams(buildQuery());

    map.on("moveend", onMoveEnd);
    return () => {
      map.off("moveend", onMoveEnd);
    };
  }, [map, config, buildQuery]);

  return { config, queryParams, projectId };
}
