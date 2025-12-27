/**
 * @p4b/draw - Feature helpers
 */
import bearing from "@turf/bearing";
import { distance } from "@turf/distance";
import { point } from "@turf/helpers";

import type { RouteSegment, RoutingProfile } from "../types";

/**
 * Check if a feature is a routed feature
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function isRoutedFeature(feature: any): boolean {
  if (!feature?.properties) return false;
  return !!(
    feature.properties.isRoutedFeature ||
    feature.properties.user_isRoutedFeature ||
    feature.properties.routingProfile ||
    feature.properties.user_routingProfile
  );
}

/**
 * Get the routing profile from a feature
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function getRoutingProfile(feature: any): RoutingProfile {
  return (feature?.properties?.routingProfile ||
    feature?.properties?.user_routingProfile ||
    "WALK") as RoutingProfile;
}

/**
 * Get waypoints from a feature
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function getWaypoints(feature: any, fallback?: [number, number][]): [number, number][] {
  let waypoints =
    feature?.properties?.routeWaypoints || feature?.properties?.user_routeWaypoints || fallback || [];

  if (typeof waypoints === "string") {
    try {
      waypoints = JSON.parse(waypoints);
    } catch {
      waypoints = [];
    }
  }

  return Array.isArray(waypoints)
    ? (waypoints.filter((w: unknown) => w !== undefined && w !== null) as [number, number][])
    : [];
}

/**
 * Get route segments from a feature
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function getRouteSegments(feature: any): RouteSegment[] {
  let segments = feature?.properties?.routeSegments || feature?.properties?.user_routeSegments || [];

  if (typeof segments === "string") {
    try {
      segments = JSON.parse(segments);
    } catch {
      segments = [];
    }
  }

  return segments as RouteSegment[];
}

/**
 * Generate a geodesic circle polygon with proper vertex alignment.
 *
 * @param centerCoords - Center coordinates [lng, lat]
 * @param radiusKm - Radius in kilometers
 * @param startBearing - Optional starting bearing in degrees to align first vertex
 * @returns Circle polygon feature
 */
export function generateCirclePolygon(
  centerCoords: [number, number],
  radiusKm: number,
  startBearing?: number
): GeoJSON.Feature<GeoJSON.Polygon> {
  const steps = radiusKm > 100 ? 128 : 64;
  const circleCoords: [number, number][] = [];
  const angleStep = 360 / steps;
  const startAngle = startBearing !== undefined ? startBearing : 0;

  for (let i = 0; i <= steps; i++) {
    const angle = startAngle + i * angleStep;
    const angleRad = (angle * Math.PI) / 180;
    const lat1 = (centerCoords[1] * Math.PI) / 180;
    const lon1 = (centerCoords[0] * Math.PI) / 180;
    const R = 6371; // Earth's radius in km

    // Calculate point at bearing and distance using Haversine formula
    const lat2 = Math.asin(
      Math.sin(lat1) * Math.cos(radiusKm / R) + Math.cos(lat1) * Math.sin(radiusKm / R) * Math.cos(angleRad)
    );
    const lon2 =
      lon1 +
      Math.atan2(
        Math.sin(angleRad) * Math.sin(radiusKm / R) * Math.cos(lat1),
        Math.cos(radiusKm / R) - Math.sin(lat1) * Math.sin(lat2)
      );

    circleCoords.push([(lon2 * 180) / Math.PI, (lat2 * 180) / Math.PI]);
  }

  return {
    type: "Feature",
    properties: {},
    geometry: {
      type: "Polygon",
      coordinates: [circleCoords],
    },
  } as GeoJSON.Feature<GeoJSON.Polygon>;
}

/**
 * Regenerate a circle polygon from a radius line feature.
 * Uses stored azimuth to maintain vertex alignment.
 *
 * @param lineFeature - Line feature with 2 coordinates (center and edge)
 * @param properties - Additional properties to add to the circle feature
 * @returns Circle polygon feature or null if invalid
 */
export function regenerateCircleFromLine(
  lineFeature: GeoJSON.Feature,
  properties?: Record<string, unknown>
): GeoJSON.Feature<GeoJSON.Polygon> | null {
  if (lineFeature.geometry.type !== "LineString") return null;
  const coords = (lineFeature.geometry as GeoJSON.LineString).coordinates;
  if (coords.length < 2) return null;

  const centerCoords = coords[0] as [number, number];
  const edgeCoords = coords[1] as [number, number];
  const center = point(centerCoords);
  const edge = point(edgeCoords);
  const radiusKm = distance(center, edge, { units: "kilometers" });

  // Get stored azimuth to maintain circle vertex alignment
  const storedAzimuth = lineFeature.properties?.azimuthDegrees || lineFeature.properties?.user_azimuthDegrees;
  let startBearing = storedAzimuth;

  if (startBearing === undefined) {
    const bearingValue = bearing(center, edge);
    startBearing = bearingValue < 0 ? bearingValue + 360 : bearingValue;
  }

  const circlePolygon = generateCirclePolygon(centerCoords, radiusKm, startBearing);

  // Merge properties
  circlePolygon.properties = {
    ...circlePolygon.properties,
    ...properties,
  };

  return circlePolygon;
}
