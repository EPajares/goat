/**
 * Hook for fetching and managing atlas features.
 *
 * Fetches features from the coverage layer when atlas is enabled,
 * applying any CQL filters from the project layer.
 */
import { useMemo } from "react";

import { useDatasetCollectionItems } from "@/lib/api/layers";
import { generateFeaturePages } from "@/lib/print/atlas-utils";
import type { AtlasPage, AtlasResult } from "@/lib/print/atlas-utils";
import type { ProjectLayer } from "@/lib/validations/project";
import type { AtlasConfig, AtlasFeatureCoverage } from "@/lib/validations/reportLayout";

export interface UseAtlasFeaturesOptions {
  /** Atlas configuration from the report layout */
  atlasConfig?: AtlasConfig;
  /** Project layers to find the coverage layer */
  projectLayers?: ProjectLayer[];
  /** Current atlas page index (0-based) */
  currentPageIndex?: number;
}

export interface UseAtlasFeaturesResult {
  /** Whether atlas features are being loaded */
  isLoading: boolean;
  /** Error if fetching failed */
  isError: boolean;
  /** Generated atlas pages */
  atlasResult: AtlasResult | null;
  /** Current atlas page (based on currentPageIndex) */
  currentPage: AtlasPage | null;
  /** Total number of atlas pages */
  totalPages: number;
  /** The coverage layer (project layer) */
  coverageLayer: ProjectLayer | null;
  /** Raw GeoJSON features from the coverage layer */
  features: GeoJSON.Feature[];
}

/**
 * Combines two CQL filter objects with an AND operator.
 * Returns undefined if both filters are empty.
 */
function combineCqlFilters(
  layerCql?: object | null,
  atlasCql?: object | null
): object | undefined {
  if (!layerCql && !atlasCql) return undefined;
  if (!layerCql) return atlasCql as object;
  if (!atlasCql) return layerCql as object;

  // Combine with AND
  return {
    op: "and",
    args: [layerCql, atlasCql],
  };
}

/**
 * Hook for fetching atlas coverage layer features.
 *
 * When atlas is enabled with a feature coverage layer:
 * 1. Finds the coverage layer in projectLayers
 * 2. Fetches all features from that layer using GeoAPI
 * 3. Applies the layer's CQL filter (if any)
 * 4. Generates atlas pages from the features
 *
 * @example
 * ```tsx
 * const { atlasResult, currentPage, isLoading } = useAtlasFeatures({
 *   atlasConfig: reportLayout.config.atlas,
 *   projectLayers,
 *   currentPageIndex: 0,
 * });
 *
 * if (atlasResult) {
 *   console.log(`Atlas has ${atlasResult.totalPages} pages`);
 * }
 * ```
 */
export function useAtlasFeatures({
  atlasConfig,
  projectLayers,
  currentPageIndex = 0,
}: UseAtlasFeaturesOptions): UseAtlasFeaturesResult {
  // Find the coverage layer from project layers
  const coverageLayer = useMemo(() => {
    if (!atlasConfig?.enabled || atlasConfig?.coverage?.type !== "feature") {
      return null;
    }

    const featureCoverage = atlasConfig.coverage as AtlasFeatureCoverage;
    return projectLayers?.find((l) => l.id === featureCoverage.layer_project_id) ?? null;
  }, [atlasConfig, projectLayers]);

  // Build query params with CQL filter
  const queryParams = useMemo(() => {
    if (!coverageLayer || !atlasConfig?.enabled) {
      return undefined;
    }

    // Get filters
    const layerCqlFilter = coverageLayer.query?.cql;
    const atlasCqlFilter =
      atlasConfig.coverage?.type === "feature" && atlasConfig.coverage.filter
        ? JSON.parse(atlasConfig.coverage.filter)
        : null;

    const combinedFilter = combineCqlFilters(layerCqlFilter, atlasCqlFilter);

    return {
      limit: 10000, // Fetch all features for atlas
      offset: 0,
      ...(combinedFilter ? { filter: JSON.stringify(combinedFilter) } : {}),
    };
  }, [coverageLayer, atlasConfig]);

  // Fetch features from GeoAPI
  const { data, isLoading, isError } = useDatasetCollectionItems(
    coverageLayer?.layer_id || "",
    atlasConfig?.enabled ? queryParams : undefined
  );

  // Convert to GeoJSON features
  const features = useMemo<GeoJSON.Feature[]>(() => {
    if (!data?.features) return [];

    return data.features.map((f) => ({
      type: "Feature" as const,
      id: f.id,
      geometry: f.geometry as GeoJSON.Geometry,
      properties: f.properties as Record<string, unknown>,
    }));
  }, [data]);

  // Generate atlas pages
  const atlasResult = useMemo<AtlasResult | null>(() => {
    if (!atlasConfig?.enabled || atlasConfig?.coverage?.type !== "feature") {
      return null;
    }

    if (features.length === 0) {
      return null;
    }

    const featureCoverage = atlasConfig.coverage as AtlasFeatureCoverage;
    const labelTemplate = atlasConfig.page_label?.template || "Page {page_number} of {total_pages}";

    return generateFeaturePages(featureCoverage, features, labelTemplate);
  }, [atlasConfig, features]);

  // Get current page
  const currentPage = useMemo<AtlasPage | null>(() => {
    if (!atlasResult?.pages) return null;

    const index = Math.max(0, Math.min(currentPageIndex, atlasResult.pages.length - 1));
    return atlasResult.pages[index] ?? null;
  }, [atlasResult, currentPageIndex]);

  return {
    isLoading,
    isError,
    atlasResult,
    currentPage,
    totalPages: atlasResult?.totalPages ?? 0,
    coverageLayer,
    features,
  };
}
