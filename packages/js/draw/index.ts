/**
 * @p4b/draw
 *
 * MapboxDraw custom modes and utilities for drawing geometries.
 *
 * The modes are generic - they just draw geometry. Whether you use them
 * for "measuring" (with labels) or just "drawing" is up to your app.
 *
 * @example
 * ```typescript
 * import {
 *   // Modes
 *   LineStringMode,
 *   PolygonMode,
 *   CircleMode,
 *   GreatCircleMode,
 *   createRoutingMode,
 *   PatchedSimpleSelect,
 *   PatchedDirectSelect,
 *   createPatchedDirectSelect,
 *
 *   // Types
 *   DrawMode,
 *   RoutingProfile,
 *   UnitSystem,
 *
 *   // Formatting
 *   formatDistance,
 *   formatArea,
 *   formatDuration,
 *
 *   // Styles
 *   defaultDrawStyles,
 *
 *   // Helpers
 *   isRoutedFeature,
 *   getWaypoints,
 * } from "@p4b/draw";
 *
 * // Create routing mode with your own route fetcher
 * const WalkingMode = createRoutingMode("WALK", myApi.fetchRoute);
 * const DrivingMode = createRoutingMode("CAR", myApi.fetchRoute);
 *
 * // Set up MapboxDraw with custom modes
 * const modes = {
 *   ...MapboxDraw.modes,
 *   simple_select: PatchedSimpleSelect,
 *   direct_select: createPatchedDirectSelect(myApi.fetchRoute), // with routing support
 *   draw_line_string: LineStringMode,
 *   draw_polygon: PolygonMode,
 *   draw_circle: CircleMode,
 *   draw_great_circle: GreatCircleMode,
 *   draw_walking: WalkingMode,
 *   draw_car: DrivingMode,
 * };
 * ```
 */

// Types
export * from "./types";

// Utilities
export * from "./utils";

// Styles
export * from "./styles";

// Helpers
export * from "./helpers";

// Modes
export * from "./modes";
