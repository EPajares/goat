/**
 * Atlas/Series Print Utilities
 *
 * Functions for calculating atlas pages from coverage (grid or feature-based),
 * computing map viewports, and generating multi-page map series.
 */
import type {
  AtlasFeatureCoverage,
  AtlasGridCoverage,
  MapAtlasControl,
} from "@/lib/validations/reportLayout";

// =============================================================================
// Types
// =============================================================================

/**
 * Represents a single page in an atlas series.
 */
export interface AtlasPage {
  /** Zero-based page index */
  index: number;
  /** One-based page number for display */
  pageNumber: number;
  /** Total number of pages */
  totalPages: number;
  /** Resolved label from template */
  label: string;

  /** For grid coverage: grid position */
  grid?: {
    row: number;
    column: number;
  };

  /** For feature coverage: the feature data */
  feature?: {
    id: string | number;
    geometry: GeoJSON.Geometry;
    properties: Record<string, unknown>;
  };

  /** Computed bounds for this page [west, south, east, north] */
  bounds: [number, number, number, number];
  /** Computed center [lng, lat] */
  center: [number, number];
}

/**
 * Result of atlas page generation.
 */
export interface AtlasResult {
  pages: AtlasPage[];
  totalPages: number;
  /** Overall bounds of all coverage */
  overviewBounds: [number, number, number, number];
  /** Coverage type used */
  coverageType: "grid" | "feature";
}

/**
 * Computed viewport for a map element on a specific atlas page.
 */
export interface AtlasMapViewport {
  center: [number, number];
  zoom: number;
  bounds: [number, number, number, number];
}

// =============================================================================
// Grid Coverage Functions
// =============================================================================

/**
 * Generate atlas pages from grid coverage.
 */
export function generateGridPages(
  coverage: AtlasGridCoverage,
  labelTemplate: string = "Page {page_number} of {total_pages}",
  pageAspectRatio: number = 1.414 // A4 portrait default
): AtlasResult {
  const [west, south, east, north] = coverage.bounds;
  const boundsWidth = east - west;
  const boundsHeight = north - south;

  let rows: number;
  let columns: number;

  if (coverage.rows && coverage.columns) {
    // Manual grid specification
    rows = coverage.rows;
    columns = coverage.columns;
  } else {
    // Auto-calculate grid based on aspect ratio and extent
    const boundsAspect = boundsWidth / boundsHeight;
    const targetPages = Math.max(1, Math.ceil(Math.sqrt((boundsWidth * boundsHeight) / 10000)));

    if (boundsAspect > pageAspectRatio) {
      columns = Math.ceil(Math.sqrt((targetPages * boundsAspect) / pageAspectRatio));
      rows = Math.ceil(targetPages / columns);
    } else {
      rows = Math.ceil(Math.sqrt((targetPages * pageAspectRatio) / boundsAspect));
      columns = Math.ceil(targetPages / rows);
    }

    rows = Math.max(1, rows);
    columns = Math.max(1, columns);
  }

  const overlapPercent = coverage.overlap_percent || 0;
  const baseTileWidth = boundsWidth / columns;
  const baseTileHeight = boundsHeight / rows;
  const tileWidth = baseTileWidth * (1 + overlapPercent / 100);
  const tileHeight = baseTileHeight * (1 + overlapPercent / 100);

  const pages: AtlasPage[] = [];
  const totalPages = rows * columns;
  let pageIndex = 0;

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < columns; col++) {
      const tileWest = west + col * baseTileWidth - (tileWidth - baseTileWidth) / 2;
      const tileEast = tileWest + tileWidth;
      const tileSouth = north - (row + 1) * baseTileHeight - (tileHeight - baseTileHeight) / 2;
      const tileNorth = tileSouth + tileHeight;

      // Clamp to overall bounds
      const clampedWest = Math.max(tileWest, west);
      const clampedEast = Math.min(tileEast, east);
      const clampedSouth = Math.max(tileSouth, south);
      const clampedNorth = Math.min(tileNorth, north);

      const center: [number, number] = [(clampedWest + clampedEast) / 2, (clampedSouth + clampedNorth) / 2];

      const label = resolvePageLabel(labelTemplate, {
        page_number: pageIndex + 1,
        total_pages: totalPages,
      });

      pages.push({
        index: pageIndex,
        pageNumber: pageIndex + 1,
        totalPages,
        label,
        grid: { row, column: col },
        bounds: [clampedWest, clampedSouth, clampedEast, clampedNorth],
        center,
      });

      pageIndex++;
    }
  }

  return {
    pages,
    totalPages,
    overviewBounds: coverage.bounds,
    coverageType: "grid",
  };
}

// =============================================================================
// Feature Coverage Functions
// =============================================================================

/**
 * Generate atlas pages from feature coverage.
 * Requires features to be fetched from the layer first.
 */
export function generateFeaturePages(
  coverage: AtlasFeatureCoverage,
  features: GeoJSON.Feature[],
  labelTemplate: string = "Page {page_number} of {total_pages}"
): AtlasResult {
  // Sort features if sort_by is specified
  const sortedFeatures = [...features];
  if (coverage.sort_by) {
    sortedFeatures.sort((a, b) => {
      const aVal = a.properties?.[coverage.sort_by!];
      const bVal = b.properties?.[coverage.sort_by!];

      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      const comparison = aVal < bVal ? -1 : 1;
      return coverage.sort_order === "desc" ? -comparison : comparison;
    });
  }

  const totalPages = sortedFeatures.length;
  const pages: AtlasPage[] = [];

  // Calculate overview bounds (union of all feature bounds)
  let overviewBounds: [number, number, number, number] = [Infinity, Infinity, -Infinity, -Infinity];

  sortedFeatures.forEach((feature, index) => {
    const featureBounds = getFeatureBounds(feature.geometry);

    // Update overview bounds
    overviewBounds = [
      Math.min(overviewBounds[0], featureBounds[0]),
      Math.min(overviewBounds[1], featureBounds[1]),
      Math.max(overviewBounds[2], featureBounds[2]),
      Math.max(overviewBounds[3], featureBounds[3]),
    ];

    const center: [number, number] = [
      (featureBounds[0] + featureBounds[2]) / 2,
      (featureBounds[1] + featureBounds[3]) / 2,
    ];

    const label = resolvePageLabel(labelTemplate, {
      page_number: index + 1,
      total_pages: totalPages,
      feature: feature.properties || {},
    });

    pages.push({
      index,
      pageNumber: index + 1,
      totalPages,
      label,
      feature: {
        id: feature.id ?? index,
        geometry: feature.geometry,
        properties: feature.properties || {},
      },
      bounds: featureBounds,
      center,
    });
  });

  return {
    pages,
    totalPages,
    overviewBounds,
    coverageType: "feature",
  };
}

// =============================================================================
// Map Viewport Calculation
// =============================================================================

/**
 * Calculate the map viewport for a specific atlas page based on map's atlas_control settings.
 */
export function calculateMapViewport(
  page: AtlasPage,
  atlasControl: MapAtlasControl,
  mapWidthPx: number,
  mapHeightPx: number
): AtlasMapViewport {
  if (!atlasControl.enabled) {
    throw new Error("Atlas control is not enabled for this map");
  }

  const marginPercent = atlasControl.margin_percent || 10;

  // Apply margin to bounds
  const [west, south, east, north] = page.bounds;
  const boundsWidth = east - west;
  const boundsHeight = north - south;
  const marginX = boundsWidth * (marginPercent / 100);
  const marginY = boundsHeight * (marginPercent / 100);

  const expandedBounds: [number, number, number, number] = [
    west - marginX,
    south - marginY,
    east + marginX,
    north + marginY,
  ];

  let zoom: number;

  switch (atlasControl.mode) {
    case "fixed_scale":
      if (atlasControl.fixed_scale) {
        // Convert scale denominator to zoom level
        // This is an approximation - actual conversion depends on latitude and DPI
        zoom = scaleToZoom(atlasControl.fixed_scale, page.center[1]);
      } else {
        zoom = calculateZoomForBounds(expandedBounds, mapWidthPx, mapHeightPx);
      }
      break;

    case "predefined_scales":
      if (atlasControl.predefined_scales?.length) {
        // Find best fitting predefined scale
        const idealZoom = calculateZoomForBounds(expandedBounds, mapWidthPx, mapHeightPx);
        const predefinedZooms = atlasControl.predefined_scales.map((s) => scaleToZoom(s, page.center[1]));
        // Find closest predefined zoom that's less than or equal to ideal (don't zoom in too much)
        const validZooms = predefinedZooms.filter((z) => z <= idealZoom);
        zoom = validZooms.length > 0 ? Math.max(...validZooms) : Math.min(...predefinedZooms);
      } else {
        zoom = calculateZoomForBounds(expandedBounds, mapWidthPx, mapHeightPx);
      }
      break;

    case "best_fit":
    default:
      zoom = calculateZoomForBounds(expandedBounds, mapWidthPx, mapHeightPx);
      break;
  }

  return {
    center: page.center,
    zoom,
    bounds: expandedBounds,
  };
}

// =============================================================================
// Label Template Resolution
// =============================================================================

/**
 * Resolve a label template with values.
 * Supports: {page_number}, {total_pages}, {feature.ATTR_NAME}
 */
export function resolvePageLabel(
  template: string,
  values: {
    page_number: number;
    total_pages: number;
    feature?: Record<string, unknown>;
  }
): string {
  let result = template;

  // Replace simple placeholders
  result = result.replace(/{page_number}/g, String(values.page_number));
  result = result.replace(/{total_pages}/g, String(values.total_pages));

  // Replace feature attribute placeholders
  if (values.feature) {
    result = result.replace(/{feature\.([^}]+)}/g, (_, attr) => {
      const value = values.feature?.[attr];
      return value !== undefined && value !== null ? String(value) : "";
    });
  }

  return result;
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Get bounding box of a GeoJSON geometry.
 */
export function getFeatureBounds(geometry: GeoJSON.Geometry): [number, number, number, number] {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;

  const processCoord = (coord: GeoJSON.Position) => {
    minX = Math.min(minX, coord[0]);
    minY = Math.min(minY, coord[1]);
    maxX = Math.max(maxX, coord[0]);
    maxY = Math.max(maxY, coord[1]);
  };

  switch (geometry.type) {
    case "Point":
      processCoord(geometry.coordinates);
      // For points, create a small bbox around the point
      const pointBuffer = 0.001; // ~100m at equator
      return [minX - pointBuffer, minY - pointBuffer, maxX + pointBuffer, maxY + pointBuffer];

    case "MultiPoint":
      geometry.coordinates.forEach(processCoord);
      break;

    case "LineString":
      geometry.coordinates.forEach(processCoord);
      break;

    case "MultiLineString":
    case "Polygon":
      geometry.coordinates.forEach((ring) => ring.forEach(processCoord));
      break;

    case "MultiPolygon":
      geometry.coordinates.forEach((poly) => poly.forEach((ring) => ring.forEach(processCoord)));
      break;

    case "GeometryCollection":
      geometry.geometries.forEach((g) => {
        const bounds = getFeatureBounds(g);
        minX = Math.min(minX, bounds[0]);
        minY = Math.min(minY, bounds[1]);
        maxX = Math.max(maxX, bounds[2]);
        maxY = Math.max(maxY, bounds[3]);
      });
      break;
  }

  return [minX, minY, maxX, maxY];
}

/**
 * Calculate zoom level to fit bounds in a map container.
 * Simplified approximation - actual implementation should use MapLibre's fitBounds logic.
 */
export function calculateZoomForBounds(
  bounds: [number, number, number, number],
  mapWidthPx: number,
  mapHeightPx: number
): number {
  const [west, south, east, north] = bounds;
  const boundsWidth = east - west;
  const boundsHeight = north - south;

  // Web Mercator approximation
  const WORLD_SIZE = 512;
  const latZoom = Math.log2((mapHeightPx * 360) / (boundsHeight * WORLD_SIZE));
  const lngZoom = Math.log2((mapWidthPx * 360) / (boundsWidth * WORLD_SIZE));

  return Math.min(latZoom, lngZoom, 22) - 0.5; // -0.5 for padding
}

/**
 * Convert scale denominator to approximate zoom level.
 * e.g., 5000 (1:5000) -> ~17
 */
export function scaleToZoom(scaleDenominator: number, latitude: number = 0): number {
  // At zoom 0, 1 pixel = 156543.03 meters at equator
  // Scale = 156543.03 * cos(lat) / (2^zoom)
  const metersPerPixelAtZoom0 = 156543.03;
  const cosLat = Math.cos((latitude * Math.PI) / 180);

  // Assuming 96 DPI, 1 inch = 0.0254 meters
  // scale = meters_per_pixel * pixels_per_meter_on_screen
  // For 96 DPI: pixels_per_meter = 96 / 0.0254 ≈ 3780
  const pixelsPerMeter = 3780;

  // scaleDenominator = metersPerPixelAtZoom0 * cosLat * pixelsPerMeter / 2^zoom
  // 2^zoom = metersPerPixelAtZoom0 * cosLat * pixelsPerMeter / scaleDenominator
  const zoom = Math.log2((metersPerPixelAtZoom0 * cosLat * pixelsPerMeter) / scaleDenominator);

  return Math.max(0, Math.min(22, zoom));
}

/**
 * Convert zoom level to approximate scale denominator.
 */
export function zoomToScale(zoom: number, latitude: number = 0): number {
  const metersPerPixelAtZoom0 = 156543.03;
  const cosLat = Math.cos((latitude * Math.PI) / 180);
  const pixelsPerMeter = 3780;

  return (metersPerPixelAtZoom0 * cosLat * pixelsPerMeter) / Math.pow(2, zoom);
}

/**
 * Get adjacent pages (for grid coverage navigation).
 */
export function getAdjacentGridPages(
  page: AtlasPage,
  allPages: AtlasPage[]
): {
  north?: AtlasPage;
  south?: AtlasPage;
  east?: AtlasPage;
  west?: AtlasPage;
} {
  if (!page.grid) return {};

  const { row, column } = page.grid;
  const adjacent: ReturnType<typeof getAdjacentGridPages> = {};

  adjacent.north = allPages.find((p) => p.grid?.row === row - 1 && p.grid?.column === column);
  adjacent.south = allPages.find((p) => p.grid?.row === row + 1 && p.grid?.column === column);
  adjacent.east = allPages.find((p) => p.grid?.row === row && p.grid?.column === column + 1);
  adjacent.west = allPages.find((p) => p.grid?.row === row && p.grid?.column === column - 1);

  return adjacent;
}
