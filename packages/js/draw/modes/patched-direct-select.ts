/**
 * @p4b/draw - Patched direct select mode
 *
 * Extends the default direct_select mode to:
 * - Render great circle features as geodesic arcs
 * - Render circle features from radius lines
 * - Handle routing features with waypoint-only editing
 */
import MapboxDraw from "@mapbox/mapbox-gl-draw";

import { regenerateCircleFromLine } from "../helpers";
import type { RouteFetcher, RouteSegment, RoutingProfile } from "../types";
import { GREAT_CIRCLE_PROPERTY, generateGreatCirclePath } from "./great-circle";

const DirectSelect = MapboxDraw.modes.direct_select;
const Constants = MapboxDraw.constants;

const USER_GREAT_CIRCLE_PROPERTY = `user_${GREAT_CIRCLE_PROPERTY}`;

// ============================================================================
// Feature Detection Helpers
// ============================================================================

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function isRoutedFeature(feature: any): boolean {
  if (!feature?.properties) return false;
  return !!(
    feature.properties.isRoutedFeature ||
    feature.properties.user_isRoutedFeature ||
    feature.properties.routingProfile ||
    feature.properties.user_routingProfile
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function getRoutingProfile(feature: any): RoutingProfile {
  return (feature?.properties?.routingProfile ||
    feature?.properties?.user_routingProfile ||
    "WALK") as RoutingProfile;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function getWaypointsFromFeature(feature: any, fallback?: [number, number][]): [number, number][] {
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

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function getSegmentsFromFeature(feature: any): RouteSegment[] {
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

// ============================================================================
// Geometry Helpers
// ============================================================================

function buildGeometryFromSegments(segments: RouteSegment[]): {
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
      totalDistance += seg.distance;
      totalDuration += seg.duration;
    }
  }

  return { coordinates, totalDistance, totalDuration };
}

function createWaypointVertex(
  coord: [number, number],
  index: number,
  featureId: string,
  isSelected: boolean
): GeoJSON.Feature {
  return {
    type: "Feature",
    properties: {
      meta: Constants.meta.VERTEX,
      parent: featureId,
      coord_path: `${index}`,
      active: isSelected ? Constants.activeStates.ACTIVE : Constants.activeStates.INACTIVE,
      isWaypointVertex: true,
      waypointIndex: index,
    },
    geometry: {
      type: "Point",
      coordinates: coord,
    },
  } as GeoJSON.Feature;
}

function createRouteLineFeature(geojson: GeoJSON.Feature, isActive: boolean): GeoJSON.Feature {
  return {
    ...geojson,
    properties: {
      ...geojson.properties,
      active: isActive ? Constants.activeStates.ACTIVE : Constants.activeStates.INACTIVE,
    },
  };
}

// ============================================================================
// Patch Factory
// ============================================================================

interface RoutingDragState {
  isDragging: boolean;
  draggedWaypointIndex: number | null;
  originalWaypoints: [number, number][];
}

/**
 * Create a patched direct select mode with optional routing support.
 *
 * @param fetchRoute - Optional route fetcher for routing feature editing
 */
export function createPatchedDirectSelect(fetchRoute?: RouteFetcher) {
  let routingDragState: RoutingDragState = {
    isDragging: false,
    draggedWaypointIndex: null,
    originalWaypoints: [],
  };

  let selectedFeatureIsRouting = false;
  let selectedFeatureId: string | null = null;

  // Use 'any' to allow adding custom event handlers
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const DirectSelectPatched: any = { ...DirectSelect };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  DirectSelectPatched.onSetup = function (this: any, opts: any) {
    const feature = this.getFeature(opts.featureId);
    selectedFeatureIsRouting = feature && isRoutedFeature(feature);
    selectedFeatureId = opts.featureId;

    routingDragState = {
      isDragging: false,
      draggedWaypointIndex: null,
      originalWaypoints: [],
    };

    if (selectedFeatureIsRouting) {
      const waypoints = getWaypointsFromFeature(feature);
      if (waypoints.length > 0) {
        routingDragState.originalWaypoints = waypoints.map(
          (w: [number, number]) => [...w] as [number, number]
        );
      }
    }

    return DirectSelect.onSetup?.call(this, opts);
  };

  DirectSelectPatched.toDisplayFeatures = function (
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    this: any,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    state: any,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    geojson: any,
    display: (feature: GeoJSON.Feature) => void
  ) {
    const geojsonId = geojson.properties?.id || geojson.id;
    const parentId = geojson.properties?.parent;

    // Check if this is a great circle feature - these should NEVER be treated as routing
    const isGreatCircle =
      geojson.properties &&
      (geojson.properties[GREAT_CIRCLE_PROPERTY] || geojson.properties[USER_GREAT_CIRCLE_PROPERTY]);

    const isThisFeatureRouting = !isGreatCircle && isRoutedFeature(geojson);
    const isSelectedFeature = geojsonId === selectedFeatureId || parentId === selectedFeatureId;

    // Only treat as routing if THIS specific feature is a routing feature
    // Don't let selectedFeatureIsRouting affect non-routing features
    const isRouting = isThisFeatureRouting;

    // Handle routing features
    if (isRouting) {
      const isMainFeature =
        geojson.properties?.meta === "feature" || geojson.properties?.meta === Constants.meta.FEATURE;

      if (!isMainFeature) return;

      if (geojson.geometry?.type === "LineString") {
        const featureFromStore = this.getFeature(geojsonId);
        const fallbackWaypoints = isSelectedFeature ? routingDragState.originalWaypoints : undefined;
        let waypoints = getWaypointsFromFeature(geojson, fallbackWaypoints);

        if (waypoints.length === 0 && featureFromStore) {
          waypoints = getWaypointsFromFeature(featureFromStore, fallbackWaypoints);
        }

        if (waypoints.length >= 2) {
          display(createRouteLineFeature(geojson, isSelectedFeature));

          if (isSelectedFeature) {
            const featureId = geojson.properties?.id || geojson.id;
            waypoints.forEach((coord: [number, number], index: number) => {
              const isVertexSelected = state.selectedCoordPaths?.includes(`${index}`);
              display(createWaypointVertex(coord, index, featureId, isVertexSelected));
            });
          }
          return;
        }
      }

      display({
        ...geojson,
        properties: {
          ...geojson.properties,
          active: isSelectedFeature ? Constants.activeStates.ACTIVE : Constants.activeStates.INACTIVE,
        },
      });
      return;
    }

    // Handle non-routing features with geodesic display
    const displayGeodesic = (feat: GeoJSON.GeoJSON) => {
      // Cast to Feature for property access (MapboxDraw always passes Features)
      const feature = feat as GeoJSON.Feature;
      const featureProps = feature.properties;
      const featureGeometry = feature.geometry;

      const isMeta = featureProps?.meta === "vertex" || featureProps?.meta === "midpoint";
      if (isMeta) {
        display(feature);
        return;
      }

      // Handle circle
      const isRadiusLine = featureProps?.isRadiusLine || featureProps?.user_isRadiusLine;
      const isCircle = featureProps?.isCircle || featureProps?.user_isCircle;

      if ((isRadiusLine || isCircle) && featureGeometry?.type === "LineString") {
        const coords = (featureGeometry as GeoJSON.LineString).coordinates;
        if (coords.length === 2) {
          display(feature);
          const featureId = featureProps?.id || feature.id;
          const circlePolygon = regenerateCircleFromLine(feature, {
            meta: "static",
            parent: featureId,
            active: featureProps?.active,
            isCircle: true,
            isDisplayOnly: true,
          });
          if (circlePolygon) display(circlePolygon);
          return;
        }
      }

      // Don't render stored circle polygons directly
      if (
        featureGeometry?.type === "Polygon" &&
        (featureProps?.isCircle ||
          featureProps?.user_isCircle ||
          featureProps?.isDisplayOnly ||
          featureProps?.user_isDisplayOnly)
      ) {
        return;
      }

      // Handle great circle
      const isGreatCircle =
        featureProps && (featureProps[GREAT_CIRCLE_PROPERTY] || featureProps[USER_GREAT_CIRCLE_PROPERTY]);

      const parentIdCheck = featureProps?.parent;
      let parentIsGreatCircle = false;
      if (parentIdCheck && this._ctx?.store) {
        const parentFeature = this._ctx.store.get(parentIdCheck);
        if (parentFeature) {
          parentIsGreatCircle = parentFeature.properties?.[GREAT_CIRCLE_PROPERTY] === true;
        }
      }

      if (parentIsGreatCircle && featureProps?.meta === "midpoint") {
        return;
      }

      if (
        isGreatCircle &&
        featureGeometry?.type === "LineString" &&
        (featureGeometry as GeoJSON.LineString).coordinates.length >= 2
      ) {
        const originalCoords = (featureGeometry as GeoJSON.LineString).coordinates as [number, number][];
        const greatCircleCoords = generateGreatCirclePath(originalCoords);
        display({
          ...feature,
          geometry: { ...featureGeometry, coordinates: greatCircleCoords },
        } as GeoJSON.Feature);
      } else {
        display(feature);
      }
    };

    DirectSelect.toDisplayFeatures.call(this, state, geojson, displayGeodesic);
  };

  // Handle vertex click for routing features
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  DirectSelectPatched.onVertex = function (this: any, state: any, e: any) {
    const feature = this.getFeature(state.featureId);

    if (feature && isRoutedFeature(feature)) {
      const featureProps = e.featureTarget?.properties;

      if (featureProps?.isWaypointVertex) {
        routingDragState.draggedWaypointIndex = featureProps.waypointIndex;
        state.selectedCoordPaths = [`${routingDragState.draggedWaypointIndex}`];
      } else {
        const coordPath = featureProps?.coord_path;
        if (coordPath !== undefined) {
          routingDragState.draggedWaypointIndex = parseInt(coordPath, 10);
          state.selectedCoordPaths = [coordPath];
        }
      }

      const waypoints = feature.properties?.routeWaypoints;
      if (waypoints && Array.isArray(waypoints)) {
        routingDragState.originalWaypoints = waypoints.map(
          (w: [number, number]) => [...w] as [number, number]
        );
      }
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return (DirectSelect as any).onVertex?.call(this, state, e);
  };

  // Handle drag for routing features
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  DirectSelectPatched.onDrag = function (this: any, state: any, e: any) {
    const feature = this.getFeature(state.featureId);

    if (
      feature &&
      isRoutedFeature(feature) &&
      routingDragState.draggedWaypointIndex !== null &&
      state.canDragMove
    ) {
      routingDragState.isDragging = true;

      let waypoints = feature.properties?.routeWaypoints;
      if (!waypoints || !Array.isArray(waypoints)) return;

      waypoints = waypoints.map((w: [number, number]) => [...w] as [number, number]);
      waypoints[routingDragState.draggedWaypointIndex] = [e.lngLat.lng, e.lngLat.lat];

      feature.properties = {
        ...feature.properties,
        routeWaypoints: waypoints,
        isUpdatingRoute: true,
      };

      if (this._ctx?.store) {
        this._ctx.store.featureChanged(state.featureId);
      }
      this.map.fire(Constants.events.RENDER);

      return;
    }

    return DirectSelect.onDrag?.call(this, state, e);
  };

  // Handle mouse up for routing features - trigger route update
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  DirectSelectPatched.onMouseUp = async function (this: any, state: any, e: any) {
    DirectSelect.onMouseUp?.call(this, state, e);

    const feature = this.getFeature(state.featureId);

    if (
      !feature ||
      !isRoutedFeature(feature) ||
      !routingDragState.isDragging ||
      routingDragState.draggedWaypointIndex === null ||
      !fetchRoute
    ) {
      routingDragState.isDragging = false;
      routingDragState.draggedWaypointIndex = null;
      return;
    }

    const waypoints = getWaypointsFromFeature(feature);
    const segments = getSegmentsFromFeature(feature);
    const profile = getRoutingProfile(feature);

    if (waypoints.length < 2 || segments.length === 0) {
      routingDragState.isDragging = false;
      routingDragState.draggedWaypointIndex = null;
      return;
    }

    const draggedIndex = routingDragState.draggedWaypointIndex;
    const segmentsToUpdate: number[] = [];
    if (draggedIndex > 0) segmentsToUpdate.push(draggedIndex - 1);
    if (draggedIndex < waypoints.length - 1) segmentsToUpdate.push(draggedIndex);

    feature.properties = { ...feature.properties, isUpdatingRoute: true };
    this.map.fire(Constants.events.RENDER);

    try {
      const updatedSegments = [...segments];

      for (const segmentIndex of segmentsToUpdate) {
        const fromPoint = waypoints[segmentIndex];
        const toPoint = waypoints[segmentIndex + 1];

        if (fromPoint && toPoint) {
          try {
            const route = await fetchRoute([fromPoint, toPoint], profile);
            updatedSegments[segmentIndex] = {
              geometry: route.geometry,
              distance: route.distance,
              duration: route.duration,
            };
          } catch (error) {
            console.warn(`Failed to route segment ${segmentIndex}:`, error);
          }
        }
      }

      const { coordinates, totalDistance, totalDuration } = buildGeometryFromSegments(updatedSegments);

      feature.coordinates = coordinates;
      feature.properties = {
        ...feature.properties,
        routeSegments: updatedSegments,
        routeWaypoints: waypoints,
        routedGeometry: { type: "LineString", coordinates },
        routeDistance: totalDistance,
        routeDuration: totalDuration,
        isUpdatingRoute: false,
        isRoutedFeature: true,
      };

      routingDragState.originalWaypoints = waypoints.map((w: [number, number]) => [...w] as [number, number]);

      if (this._ctx?.store) {
        this._ctx.store.featureChanged(state.featureId);
        if (this._ctx.store.render) this._ctx.store.render();
      }

      this.map.fire(Constants.events.RENDER);
      this.map.fire("draw.render");

      const currentFeatureId = state.featureId;
      setTimeout(() => {
        this.changeMode("simple_select", { featureIds: [currentFeatureId] });
        setTimeout(() => {
          this.changeMode("direct_select", { featureId: currentFeatureId });
        }, 0);
      }, 0);

      this.map.fire(Constants.events.UPDATE, {
        features: [feature.toGeoJSON()],
        action: "change_coordinates",
      });
    } catch (error) {
      console.error("Error updating route:", error);
      feature.properties = { ...feature.properties, isUpdatingRoute: false };
      this.map.fire(Constants.events.RENDER);
    }

    routingDragState.isDragging = false;
    routingDragState.draggedWaypointIndex = null;
  };

  // Disable midpoint creation for routing features
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  DirectSelectPatched.onMidpoint = function (this: any, state: any, e: any) {
    const feature = this.getFeature(state.featureId);
    if (feature && isRoutedFeature(feature)) return;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return (DirectSelect as any).onMidpoint?.call(this, state, e);
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  DirectSelectPatched.onFeature = function (this: any, state: any, e: any) {
    const feature = this.getFeature(state.featureId);
    if (feature && isRoutedFeature(feature)) return;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return (DirectSelect as any).onFeature?.call(this, state, e);
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  DirectSelectPatched.onStop = function (this: any, state: any) {
    routingDragState = {
      isDragging: false,
      draggedWaypointIndex: null,
      originalWaypoints: [],
    };
    return DirectSelect.onStop?.call(this, state);
  };

  return DirectSelectPatched;
}

// Default export without routing support
export default createPatchedDirectSelect();
