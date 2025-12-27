/**
 * @p4b/draw - Geometry utilities
 */
import MapboxDraw from "@mapbox/mapbox-gl-draw";
import { circle } from "@turf/circle";
import { distance } from "@turf/distance";
import { point } from "@turf/helpers";

import type { LineStringGeometry, RouteSegment } from "../types";

const Constants = MapboxDraw.constants;

// ============================================================================
// Vertex
// ============================================================================

export function createVertex(
  parentId: string,
  coordinates: [number, number],
  path: string,
  selected: boolean
): GeoJSON.Feature<GeoJSON.Point> {
  return {
    type: Constants.geojsonTypes.FEATURE,
    properties: {
      meta: Constants.meta.VERTEX,
      parent: parentId,
      coord_path: path,
      active: selected ? Constants.activeStates.ACTIVE : Constants.activeStates.INACTIVE,
    },
    geometry: {
      type: Constants.geojsonTypes.POINT,
      coordinates,
    },
  } as GeoJSON.Feature<GeoJSON.Point>;
}

// ============================================================================
// Circle
// ============================================================================

export function createCirclePolygon(
  center: [number, number],
  radiusKm: number,
  options?: { active?: boolean; parentId?: string; interactive?: boolean }
): GeoJSON.Feature<GeoJSON.Polygon> {
  const { active = false, parentId, interactive = false } = options || {};
  return circle(center, radiusKm, {
    steps: 64,
    units: "kilometers",
    properties: {
      meta: interactive ? "feature" : "static",
      parent: parentId,
      active: active ? Constants.activeStates.ACTIVE : Constants.activeStates.INACTIVE,
      isCircle: true,
      isDisplayOnly: !interactive,
    },
  }) as GeoJSON.Feature<GeoJSON.Polygon>;
}

export function calculateRadius(center: [number, number], edge: [number, number]): number {
  return distance(point(center), point(edge), { units: "kilometers" });
}

// ============================================================================
// Route Geometry
// ============================================================================

export function buildRouteGeometry(segments: RouteSegment[]): {
  coordinates: [number, number][];
  totalDistance: number;
  totalDuration: number;
} {
  const coordinates: [number, number][] = [];
  let totalDistance = 0;
  let totalDuration = 0;

  for (let i = 0; i < segments.length; i++) {
    const seg = segments[i];
    if (seg?.geometry?.coordinates) {
      const coords = seg.geometry.coordinates;
      coordinates.push(...(i === 0 ? coords : coords.slice(1)));
      totalDistance += seg.distance || 0;
      totalDuration += seg.duration || 0;
    }
  }

  return { coordinates, totalDistance, totalDuration };
}

export function combineGeometries(
  confirmed: LineStringGeometry | null,
  preview: LineStringGeometry | null
): LineStringGeometry | null {
  if (!confirmed && !preview) return null;
  if (confirmed && !preview) return confirmed;
  if (!confirmed && preview) return preview;

  return {
    type: "LineString",
    coordinates: [...confirmed!.coordinates, ...preview!.coordinates.slice(1)],
  };
}
