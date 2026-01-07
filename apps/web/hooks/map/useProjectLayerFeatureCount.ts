/**
 * Hook for fetching feature count for a project layer.
 *
 * This hook fetches the feature count on-demand via GeoAPI's feature-count process,
 * respecting any CQL filters applied to the project layer.
 *
 * Use this hook instead of relying on `filtered_count` from the project layer schema,
 * as counts are now fetched on-demand rather than stored with the project.
 */
import { useMemo } from "react";

import { useFeatureCount } from "@/lib/api/processes";
import type { ProjectLayer } from "@/lib/validations/project";

export interface UseProjectLayerFeatureCountOptions {
  /** The project layer to get the feature count for */
  projectLayer?: ProjectLayer | null;
  /** Whether to fetch the count (defaults to true) */
  enabled?: boolean;
}

export interface UseProjectLayerFeatureCountResult {
  /** The feature count (undefined while loading or if no layer) */
  featureCount: number | undefined;
  /** Whether the count is being fetched */
  isLoading: boolean;
  /** Whether there was an error fetching the count */
  isError: boolean;
  /** Refetch the count */
  mutate: () => void;
}

/**
 * Hook to fetch feature count for a project layer.
 *
 * Automatically applies the layer's CQL filter if present.
 *
 * @example
 * ```tsx
 * const { featureCount, isLoading } = useProjectLayerFeatureCount({
 *   projectLayer: targetLayer,
 * });
 *
 * // Use in validation
 * const isValid = featureCount !== undefined && featureCount <= maxFeatureCnt;
 * ```
 */
export function useProjectLayerFeatureCount({
  projectLayer,
  enabled = true,
}: UseProjectLayerFeatureCountOptions): UseProjectLayerFeatureCountResult {
  // Extract the layer_id (collection ID for GeoAPI)
  const layerId = projectLayer?.layer_id;

  // Build the CQL filter string from the project layer's query
  const cqlFilter = useMemo(() => {
    if (!projectLayer?.query?.cql) {
      return undefined;
    }
    // Convert the CQL object to a JSON string for the API
    return JSON.stringify(projectLayer.query.cql);
  }, [projectLayer?.query?.cql]);

  // Use the existing feature count hook
  const { featureCount, isLoading, isError, mutate } = useFeatureCount(
    enabled && layerId ? layerId : undefined,
    cqlFilter
  );

  return {
    featureCount,
    isLoading,
    isError: !!isError,
    mutate,
  };
}

/**
 * Hook to fetch feature counts for multiple project layers at once.
 *
 * Useful when you need to validate multiple layers (e.g., target and join layers).
 * Supports up to 10 layers due to React hooks rules (hooks must be called unconditionally).
 *
 * @example
 * ```tsx
 * const counts = useMultipleProjectLayerFeatureCounts([
 *   { projectLayer: targetLayer },
 *   { projectLayer: joinLayer },
 * ]);
 *
 * const targetCount = counts[0].featureCount;
 * const joinCount = counts[1].featureCount;
 * ```
 */
export function useMultipleProjectLayerFeatureCounts(
  layers: UseProjectLayerFeatureCountOptions[]
): UseProjectLayerFeatureCountResult[] {
  // We need to call hooks unconditionally, so we create results for each layer
  // Note: This is a simplified version - for a more robust implementation,
  // you might want to batch requests or use a different approach
  // Supports up to 10 layers

  const result0 = useProjectLayerFeatureCount(layers[0] || { enabled: false });
  const result1 = useProjectLayerFeatureCount(layers[1] || { enabled: false });
  const result2 = useProjectLayerFeatureCount(layers[2] || { enabled: false });
  const result3 = useProjectLayerFeatureCount(layers[3] || { enabled: false });
  const result4 = useProjectLayerFeatureCount(layers[4] || { enabled: false });
  const result5 = useProjectLayerFeatureCount(layers[5] || { enabled: false });
  const result6 = useProjectLayerFeatureCount(layers[6] || { enabled: false });
  const result7 = useProjectLayerFeatureCount(layers[7] || { enabled: false });
  const result8 = useProjectLayerFeatureCount(layers[8] || { enabled: false });
  const result9 = useProjectLayerFeatureCount(layers[9] || { enabled: false });

  // Return only the results we need
  const results = [result0, result1, result2, result3, result4, result5, result6, result7, result8, result9];
  return results.slice(0, Math.min(layers.length, 10));
}

/**
 * Hook to get the total feature count for multiple project layers.
 *
 * Useful for heatmap tools that need to validate the total number of features
 * across multiple opportunity layers.
 *
 * @example
 * ```tsx
 * const { totalCount, isLoading } = useTotalProjectLayerFeatureCount(
 *   opportunities.map(o => layers?.find(l => l.id === o.layer?.value))
 * );
 * ```
 */
export function useTotalProjectLayerFeatureCount(projectLayers: (ProjectLayer | undefined | null)[]): {
  totalCount: number;
  isLoading: boolean;
  isError: boolean;
} {
  // Convert to hook options
  const layerOptions = useMemo(() => {
    return projectLayers.map((layer) => ({
      projectLayer: layer,
      enabled: !!layer,
    }));
  }, [projectLayers]);

  const results = useMultipleProjectLayerFeatureCounts(layerOptions);

  const totalCount = useMemo(() => {
    return results.reduce((acc, result) => acc + (result.featureCount || 0), 0);
  }, [results]);

  const isLoading = results.some((r) => r.isLoading);
  const isError = results.some((r) => r.isError);

  return {
    totalCount,
    isLoading,
    isError,
  };
}

export default useProjectLayerFeatureCount;
