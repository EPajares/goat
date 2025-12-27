/**
 * @p4b/draw - Types
 */

// ============================================================================
// Geometry Types
// ============================================================================

export interface LineStringGeometry {
  type: "LineString";
  coordinates: [number, number][];
}

// ============================================================================
// Unit System Types
// ============================================================================

export type UnitSystem = "metric" | "imperial";
export type UnitPreference = UnitSystem | "default";

// ============================================================================
// Routing Types
// ============================================================================

/**
 * Routing profile - supports common OSRM naming conventions
 * - "foot" / "walk" / "WALK" for pedestrian routing
 * - "car" / "CAR" for vehicle routing
 */
export type RoutingProfile = "foot" | "car" | "WALK" | "CAR" | "walk";

export interface RouteSegment {
  geometry: LineStringGeometry;
  distance: number;
  duration: number;
}

export interface RouteResult {
  geometry: LineStringGeometry;
  distance: number;
  duration: number;
  snappedWaypoints?: [number, number][];
}

/**
 * Function signature for fetching routes - allows dependency injection
 */
export type RouteFetcher = (waypoints: [number, number][], profile: RoutingProfile) => Promise<RouteResult>;

// ============================================================================
// Draw Mode Names
// ============================================================================

export enum DrawMode {
  LINE_STRING = "draw_line_string_enhanced",
  POLYGON = "draw_polygon_enhanced",
  CIRCLE = "draw_circle",
  GREAT_CIRCLE = "draw_great_circle",
  ROUTING = "draw_routing",
}

// ============================================================================
// Feature Property Constants (defined in modes, re-exported here for convenience)
// ============================================================================

export const ROUTED_FEATURE_PROPERTY = "isRoutedFeature";

// ============================================================================
// Style Types
// ============================================================================

export interface DrawStyle {
  id: string;
  type: "fill" | "line" | "circle" | "symbol";
  filter?: unknown[];
  layout?: Record<string, unknown>;
  paint?: Record<string, unknown>;
}
