/**
 * @p4b/draw - Routing draw mode
 *
 * A MapboxDraw mode that draws routed lines (via walking, driving, etc.)
 * The routing service is injected via factory function.
 */
import MapboxDraw from "@mapbox/mapbox-gl-draw";

import { regenerateCircleFromLine } from "../helpers";
import type { LineStringGeometry, RouteFetcher, RouteSegment, RoutingProfile } from "../types";
import { formatDuration } from "../utils/formatting";
import { generateGreatCirclePath } from "./great-circle";

const Constants = MapboxDraw.constants;
const DrawLineString = MapboxDraw.modes.draw_line_string;

/**
 * Helper to create a vertex point feature
 */
function createVertex(parentId: string, coordinates: [number, number], path: string, selected: boolean) {
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
  };
}

/**
 * Create a routing draw mode.
 *
 * @param profile - Routing profile (foot, car, WALK, CAR, etc.)
 * @param fetchRoute - Function to fetch routes (injected)
 *
 * @example
 * import { createRoutingMode } from "@p4b/draw";
 * import osrmClient from "./api/osrm";
 *
 * // Create modes for different routing profiles
 * const WalkingMode = createRoutingMode("foot", osrmClient.fetchRoute);
 * const DrivingMode = createRoutingMode("car", osrmClient.fetchRoute);
 */
export function createRoutingMode(profile: RoutingProfile, fetchRoute: RouteFetcher): typeof DrawLineString {
  const RoutingMode = { ...DrawLineString };

  // Store the confirmed route (all completed segments combined)
  let confirmedRoute: {
    geometry: LineStringGeometry;
    totalDistance: number;
    totalDuration: number;
    waypointCount: number;
  } | null = null;

  // Store individual segments for editing support
  let routeSegments: RouteSegment[] = [];

  // Store clicked waypoints (the actual user-clicked points)
  let clickedWaypoints: [number, number][] = [];

  // Store the preview segment (from last waypoint to mouse position)
  let previewSegment: RouteSegment | null = null;

  let isLoadingRoute = false;
  let routeFetchTimeout: ReturnType<typeof setTimeout> | null = null;

  // Flag to prevent async callbacks from updating after mode stopped
  let isStopped = false;

  // Queue for confirmed segment requests - processes them in order
  type SegmentRequest = {
    fromPoint: [number, number];
    toPoint: [number, number];
    fromIndex: number;
  };
  let segmentQueue: SegmentRequest[] = [];
  let isProcessingQueue = false;

  // Helper to combine confirmed route with preview segment
  function getCombinedGeometry(): LineStringGeometry | null {
    if (!confirmedRoute && !previewSegment) return null;

    if (confirmedRoute && !previewSegment) {
      return confirmedRoute.geometry;
    }

    if (!confirmedRoute && previewSegment) {
      return previewSegment.geometry;
    }

    // Combine both - append preview coordinates (skip first point to avoid duplicate)
    const confirmedCoords = confirmedRoute!.geometry.coordinates;
    const previewCoords = previewSegment!.geometry.coordinates;

    return {
      type: "LineString",
      coordinates: [...confirmedCoords, ...previewCoords.slice(1)],
    };
  }

  // Override onSetup to initialize the mode
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  RoutingMode.onSetup = function (this: any, opts: any) {
    // Reset the stopped flag when starting a new drawing
    isStopped = false;
    confirmedRoute = null;
    routeSegments = [];
    clickedWaypoints = [];
    previewSegment = null;
    isLoadingRoute = false;
    segmentQueue = [];
    isProcessingQueue = false;

    // Call the original onSetup if it exists
    return DrawLineString.onSetup ? DrawLineString.onSetup.call(this, opts) : {};
  };

  // Override toDisplayFeatures to show waypoints and routed line
  RoutingMode.toDisplayFeatures = function (
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    this: any,
    state: { line: { id: string } },
    geojson: GeoJSON.Feature<GeoJSON.LineString> & { properties: Record<string, unknown> },
    display: (feature: GeoJSON.Feature) => void
  ) {
    const isActiveLine = geojson.properties.id === state.line.id;
    geojson.properties.active = isActiveLine
      ? Constants.activeStates.ACTIVE
      : Constants.activeStates.INACTIVE;

    if (!isActiveLine) {
      // For inactive features, check if it has a stored route
      if (geojson.properties?.routedGeometry) {
        const routedFeature = {
          ...geojson,
          geometry: geojson.properties.routedGeometry as GeoJSON.LineString,
        };
        return display(routedFeature as GeoJSON.Feature);
      }

      // Handle circle features - render them with their polygon
      const isRadiusLine = geojson.properties?.isRadiusLine || geojson.properties?.user_isRadiusLine;
      const isCircle = geojson.properties?.isCircle || geojson.properties?.user_isCircle;

      if (
        (isRadiusLine || isCircle) &&
        geojson.geometry.type === "LineString" &&
        geojson.geometry.coordinates.length === 2
      ) {
        display(geojson);
        const featureId = geojson.properties?.id || geojson.id;
        const circlePolygon = regenerateCircleFromLine(geojson, {
          meta: "feature",
          parent: featureId,
          parentRadiusLine: featureId,
          id: `${featureId}-circle-display`,
          active: geojson.properties?.active,
          isCircle: true,
          isDisplayOnly: true,
        });
        if (circlePolygon) display(circlePolygon);
        return;
      }

      // Handle great circle features - render them with their curved path
      const isGreatCircle =
        geojson.properties && (geojson.properties.isGreatCircle || geojson.properties.user_isGreatCircle);

      if (
        isGreatCircle &&
        geojson.geometry.type === "LineString" &&
        geojson.geometry.coordinates.length >= 2
      ) {
        // Generate the great circle path and display it
        const originalCoords = geojson.geometry.coordinates as [number, number][];
        const greatCircleCoords = generateGreatCirclePath(originalCoords);
        const greatCircleFeature = {
          ...geojson,
          geometry: { ...geojson.geometry, coordinates: greatCircleCoords },
        };
        return display(greatCircleFeature as GeoJSON.Feature);
      }

      return display(geojson);
    }

    // Only render if we have at least one waypoint
    if (geojson.geometry.coordinates.length < 1) {
      return;
    }

    // Display waypoint vertices - use actual feature coordinates (snapped waypoints)
    const coords = geojson.geometry.coordinates;
    for (let i = 0; i < coords.length - 1; i++) {
      const isLastVertex = i === coords.length - 2;
      display(
        createVertex(state.line.id, coords[i] as [number, number], `${i}`, isLastVertex) as GeoJSON.Feature
      );
    }

    // Display combined route (confirmed + preview)
    const combinedGeometry = getCombinedGeometry();
    if (combinedGeometry && coords.length >= 2) {
      const totalDistance = (confirmedRoute?.totalDistance || 0) + (previewSegment?.distance || 0);
      const totalDuration = (confirmedRoute?.totalDuration || 0) + (previewSegment?.duration || 0);

      const routedFeature: GeoJSON.Feature<GeoJSON.LineString> = {
        type: "Feature",
        properties: {
          ...geojson.properties,
          meta: Constants.meta.FEATURE,
          isRoutedLine: true,
          routingProfile: profile,
          isLoading: isLoadingRoute,
          active: Constants.activeStates.INACTIVE,
          routeDuration: totalDuration,
          routeDistance: totalDistance,
        },
        geometry: combinedGeometry,
      };
      display(routedFeature);
    }
  };

  // Helper function to fetch preview segment (from last waypoint to mouse position)
  async function fetchPreviewSegment(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ctx: any,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    state: any,
    fromPoint: [number, number],
    toPoint: [number, number]
  ) {
    isLoadingRoute = true;
    ctx.map.fire(Constants.events.RENDER);

    try {
      // Fetch route for just this segment
      const route = await fetchRoute([fromPoint, toPoint], profile);

      // Don't update if mode has stopped
      if (isStopped) return;

      // Store as preview segment
      previewSegment = {
        geometry: route.geometry,
        distance: route.distance,
        duration: route.duration,
      };

      isLoadingRoute = false;

      // Update feature properties with combined totals
      const feature = ctx.getFeature(state.line.id);
      if (feature) {
        const totalDistance = (confirmedRoute?.totalDistance || 0) + route.distance;
        const totalDuration = (confirmedRoute?.totalDuration || 0) + route.duration;
        const formattedDur = formatDuration(totalDuration);

        feature.properties = {
          ...feature.properties,
          routedGeometry: getCombinedGeometry(),
          routeDuration: totalDuration,
          routeDistance: totalDistance,
          routingProfile: profile,
          formattedDuration: formattedDur,
        };
      }

      // Force re-render
      setTimeout(() => {
        // Don't re-render if mode has stopped
        if (isStopped) return;

        if (ctx._ctx && ctx._ctx.store) {
          ctx._ctx.store.featureChanged(state.line.id);
          if (ctx._ctx.store.render) {
            ctx._ctx.store.render();
          }
        }
        ctx.map.fire(Constants.events.RENDER);
        ctx.map.fire("draw.render");

        // Fire UPDATE event so MeasureProvider can update measurements in real-time
        const currentFeature = ctx._ctx?.store?.get(state.line.id);
        if (currentFeature) {
          ctx.map.fire(Constants.events.UPDATE, {
            features: [currentFeature.toGeoJSON()],
            action: "change_coordinates",
          });
        }

        if (ctx.map.triggerRepaint) {
          ctx.map.triggerRepaint();
        }
      }, 0);
    } catch (error) {
      if (error instanceof Error && error.message === "Request cancelled") {
        return;
      }
      isLoadingRoute = false;
      ctx.map.fire(Constants.events.RENDER);
    }
  }

  // Process the segment queue one at a time, in order
  async function processSegmentQueue(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    context: any,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    state: any
  ) {
    if (isProcessingQueue || segmentQueue.length === 0) return;

    isProcessingQueue = true;

    while (segmentQueue.length > 0) {
      const segment = segmentQueue.shift()!;
      await processOneSegment.call(context, state, segment.fromPoint, segment.toPoint, segment.fromIndex);
    }

    isProcessingQueue = false;
  }

  // Process a single segment (internal - called by queue processor)
  async function processOneSegment(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    this: any,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    state: any,
    fromPoint: [number, number],
    toPoint: [number, number],
    fromIndex: number
  ) {
    isLoadingRoute = true;
    this.map.fire(Constants.events.RENDER);

    try {
      // Fetch route for this segment
      const route = await fetchRoute([fromPoint, toPoint], profile);

      // Don't update if mode has stopped
      if (isStopped) return;

      const feature = this.getFeature(state.line.id);
      if (!feature || !feature.coordinates) return;

      // Snap the waypoints in feature.coordinates to road network
      if (route.snappedWaypoints && route.snappedWaypoints.length >= 2) {
        // Snap the source waypoint in feature coordinates
        if (fromIndex < feature.coordinates.length - 1) {
          feature.coordinates[fromIndex] = route.snappedWaypoints[0];
        }
        // Snap the destination waypoint in feature coordinates
        if (fromIndex + 1 < feature.coordinates.length - 1) {
          feature.coordinates[fromIndex + 1] = route.snappedWaypoints[1];
        }

        // Update clickedWaypoints with snapped positions
        const segmentIndex = routeSegments.length;
        if (segmentIndex < clickedWaypoints.length) {
          clickedWaypoints[segmentIndex] = route.snappedWaypoints[0];
        }
        if (segmentIndex + 1 < clickedWaypoints.length) {
          clickedWaypoints[segmentIndex + 1] = route.snappedWaypoints[1];
        } else if (segmentIndex + 1 === clickedWaypoints.length) {
          clickedWaypoints[segmentIndex] = route.snappedWaypoints[0];
        }
      }

      // Store this segment
      routeSegments.push({
        geometry: route.geometry,
        distance: route.distance,
        duration: route.duration,
      });

      // Add this segment to confirmed route
      if (confirmedRoute) {
        // Append to existing route
        const existingCoords = confirmedRoute.geometry.coordinates;
        const newCoords = route.geometry.coordinates;

        confirmedRoute = {
          geometry: {
            type: "LineString",
            coordinates: [...existingCoords, ...newCoords.slice(1)],
          },
          totalDistance: confirmedRoute.totalDistance + route.distance,
          totalDuration: confirmedRoute.totalDuration + route.duration,
          waypointCount: confirmedRoute.waypointCount + 1,
        };
      } else {
        // First segment
        confirmedRoute = {
          geometry: route.geometry,
          totalDistance: route.distance,
          totalDuration: route.duration,
          waypointCount: 2,
        };
      }

      // Clear preview since we've confirmed a new segment
      previewSegment = null;

      isLoadingRoute = segmentQueue.length > 0; // Still loading if more in queue

      // Update feature properties
      const totalDistance = confirmedRoute.totalDistance;
      const totalDuration = confirmedRoute.totalDuration;
      const formattedDur = formatDuration(totalDuration);

      feature.properties = {
        ...feature.properties,
        routedGeometry: confirmedRoute.geometry,
        routeDuration: totalDuration,
        routeDistance: totalDistance,
        routingProfile: profile,
        formattedDuration: formattedDur,
        // Store waypoints and segments for editing
        routeWaypoints: [...clickedWaypoints],
        routeSegments: [...routeSegments],
      };

      // Force re-render
      if (this._ctx && this._ctx.store) {
        this._ctx.store.featureChanged(state.line.id);
        if (this._ctx.store.render) {
          this._ctx.store.render();
        }
      }
      this.map.fire(Constants.events.RENDER);
      this.map.fire("draw.render");

      // Fire UPDATE event so MeasureProvider can update measurements in real-time
      const currentFeature = this._ctx?.store?.get(state.line.id);
      if (currentFeature) {
        this.map.fire(Constants.events.UPDATE, {
          features: [currentFeature.toGeoJSON()],
          action: "change_coordinates",
        });
      }

      if (this.map.triggerRepaint) {
        this.map.triggerRepaint();
      }
    } catch (error) {
      if (error instanceof Error && error.message === "Request cancelled") {
        return;
      }
      isLoadingRoute = segmentQueue.length > 0;
      this.map.fire(Constants.events.RENDER);
    }
  }

  // Queue a segment for processing (called on click)
  function queueSegment(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    context: any,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    state: any,
    fromPoint: [number, number],
    toPoint: [number, number],
    fromIndex: number
  ) {
    segmentQueue.push({ fromPoint, toPoint, fromIndex });
    processSegmentQueue(context, state);
  }

  // Override onMouseMove to track cursor and fetch routes in real-time
  RoutingMode.onMouseMove = function (
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    this: any,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    state: any,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    e: any
  ) {
    // Call the original onMouseMove
    const result = DrawLineString.onMouseMove?.call(this, state, e);

    // Get the feature
    const feature = this.getFeature(state.line.id);
    if (!feature || !feature.coordinates) {
      return result;
    }

    const coords = feature.coordinates;

    // Only fetch route if we have at least one fixed waypoint
    if (coords.length >= 2) {
      const mousePos: [number, number] = [e.lngLat.lng, e.lngLat.lat];

      // Only start routing if we have at least one confirmed waypoint
      const fixedWaypoints = coords.slice(0, -1) as [number, number][]; // Exclude ghost point
      if (fixedWaypoints.length >= 1) {
        // Clear previous timeout
        if (routeFetchTimeout) {
          clearTimeout(routeFetchTimeout);
        }

        // Debounce the route fetch (500ms for preview segment)
        routeFetchTimeout = setTimeout(() => {
          // Route from last fixed waypoint to mouse position (preview segment only)
          const lastWaypoint = fixedWaypoints[fixedWaypoints.length - 1];
          fetchPreviewSegment(this, state, lastWaypoint, mousePos);
        }, 500);
      }
    }

    return result;
  };

  // Override onClick to add waypoint and immediately fetch route to cursor position
  RoutingMode.onClick = function (
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    this: any,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    state: any,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    e: any
  ) {
    // Call the original onClick to add the coordinate
    const result = DrawLineString.onClick?.call(this, state, e);

    // Clear any pending debounced route fetch since we're adding a fixed waypoint
    if (routeFetchTimeout) {
      clearTimeout(routeFetchTimeout);
      routeFetchTimeout = null;
    }

    // Check if state.line exists and has an id
    if (!state.line || !state.line.id) {
      return result;
    }

    // Get the feature
    const feature = this.getFeature(state.line.id);
    if (!feature || !feature.coordinates) {
      return result;
    }

    // After adding a waypoint, queue the segment for processing
    const coords = feature.coordinates;
    // Need at least 2 fixed waypoints to create a route
    // coords includes ghost point, so coords.length >= 3 means at least 2 fixed waypoints
    if (coords.length >= 3) {
      const fixedWaypoints = coords.slice(0, -1) as [number, number][];

      // Store the clicked waypoint
      const newWaypoint = fixedWaypoints[fixedWaypoints.length - 1];
      clickedWaypoints.push(newWaypoint);

      // Route only the NEW segment (from second-to-last to last waypoint)
      const fromWaypoint = fixedWaypoints[fixedWaypoints.length - 2];
      const toWaypoint = newWaypoint;
      const fromIndex = fixedWaypoints.length - 2;
      // Queue the segment - will be processed in order
      queueSegment(this, state, fromWaypoint, toWaypoint, fromIndex);
    } else if (coords.length === 2) {
      // First waypoint clicked - store it
      const firstWaypoint = coords[0] as [number, number];
      clickedWaypoints = [firstWaypoint];
    }

    return result;
  };

  // Override onStop to finalize the route
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  RoutingMode.onStop = function (this: any, state: any) {
    // Mark mode as stopped to prevent async callbacks from updating
    isStopped = true;

    // Clear any pending debounced request
    if (routeFetchTimeout) {
      clearTimeout(routeFetchTimeout);
      routeFetchTimeout = null;
    }

    // Clear the queue
    segmentQueue = [];
    isProcessingQueue = false;

    // Check if the feature exists
    const feature = this.getFeature(state.line.id);
    if (!feature || !feature.coordinates) {
      // Feature doesn't exist or is invalid - clean up and exit
      confirmedRoute = null;
      previewSegment = null;
      isLoadingRoute = false;
      clickedWaypoints = [];
      routeSegments = [];
      return;
    }

    const coords = feature.coordinates;

    // Must have at least 2 waypoints
    if (coords.length >= 3 || (coords.length === 2 && clickedWaypoints.length >= 2)) {
      const fixedWaypoints =
        clickedWaypoints.length >= 2 ? [...clickedWaypoints] : (coords.slice(0, -1) as [number, number][]);

      // If we already have a confirmed route with all segments, use it
      if (confirmedRoute && routeSegments.length > 0 && routeSegments.length >= fixedWaypoints.length - 1) {
        // Replace the coordinates with the routed geometry
        feature.coordinates = confirmedRoute.geometry.coordinates;

        // Extract waypoints from segments
        const extractedWaypoints: [number, number][] = [];
        for (let i = 0; i < routeSegments.length; i++) {
          const segment = routeSegments[i];
          if (segment.geometry.coordinates.length > 0) {
            if (i === 0) {
              extractedWaypoints.push(segment.geometry.coordinates[0]);
            }
            const lastCoord = segment.geometry.coordinates[segment.geometry.coordinates.length - 1];
            extractedWaypoints.push(lastCoord);
          }
        }

        const formattedDur = formatDuration(confirmedRoute.totalDuration);

        feature.properties = {
          ...feature.properties,
          routedGeometry: confirmedRoute.geometry,
          routeDuration: confirmedRoute.totalDuration,
          routeDistance: confirmedRoute.totalDistance,
          routingProfile: profile,
          formattedDuration: formattedDur,
          isRoutedFeature: true,
          routeWaypoints: extractedWaypoints,
          routeSegments: [...routeSegments],
        };
      } else if (fixedWaypoints.length >= 2) {
        // Route segments not complete yet - fetch missing segments
        if (confirmedRoute && confirmedRoute.geometry.coordinates.length > 0) {
          feature.coordinates = confirmedRoute.geometry.coordinates;
          const formattedDur = formatDuration(confirmedRoute.totalDuration);
          feature.properties = {
            ...feature.properties,
            routedGeometry: confirmedRoute.geometry,
            routeDuration: confirmedRoute.totalDuration,
            routeDistance: confirmedRoute.totalDistance,
            routingProfile: profile,
            formattedDuration: formattedDur,
            isRoutedFeature: true,
            routeWaypoints: [...clickedWaypoints],
            routeSegments: [...routeSegments],
          };
        }

        // Calculate how many segments we're missing
        const expectedSegments = fixedWaypoints.length - 1;
        const missingSegmentCount = expectedSegments - routeSegments.length;

        if (missingSegmentCount > 0) {
          const startSegmentIndex = routeSegments.length;
          const existingSegments = [...routeSegments];
          const featureId = state.line.id;
          const mapRef = this.map;
          const ctxRef = this._ctx;

          // Build array of segment fetch promises
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const segmentPromises: Promise<any>[] = [];

          for (let i = startSegmentIndex; i < expectedSegments; i++) {
            const fromPoint = fixedWaypoints[i];
            const toPoint = fixedWaypoints[i + 1];

            if (fromPoint && toPoint) {
              segmentPromises.push(
                fetchRoute([fromPoint, toPoint], profile)
                  .then((route) => ({
                    geometry: route.geometry,
                    distance: route.distance,
                    duration: route.duration,
                  }))
                  .catch(() => null)
              );
            }
          }

          if (segmentPromises.length > 0) {
            Promise.all(segmentPromises)
              .then((newSegments) => {
                const currentFeature = ctxRef?.store?.get(featureId);
                if (!currentFeature) return;

                const validNewSegments = newSegments.filter((s): s is NonNullable<typeof s> => s !== null);
                if (validNewSegments.length === 0) return;

                const allSegments = [...existingSegments, ...validNewSegments];

                const fullCoordinates: [number, number][] = [];
                let totalDistance = 0;
                let totalDuration = 0;

                for (let i = 0; i < allSegments.length; i++) {
                  const segment = allSegments[i];
                  const segCoords = segment.geometry.coordinates;
                  if (i === 0) {
                    fullCoordinates.push(...segCoords);
                  } else {
                    fullCoordinates.push(...segCoords.slice(1));
                  }
                  totalDistance += segment.distance;
                  totalDuration += segment.duration;
                }

                const extractedWaypoints: [number, number][] = [];
                for (let i = 0; i < allSegments.length; i++) {
                  const segment = allSegments[i];
                  if (segment.geometry.coordinates.length > 0) {
                    if (i === 0) {
                      extractedWaypoints.push(segment.geometry.coordinates[0]);
                    }
                    const lastCoord = segment.geometry.coordinates[segment.geometry.coordinates.length - 1];
                    extractedWaypoints.push(lastCoord);
                  }
                }

                currentFeature.coordinates = fullCoordinates;
                const formattedDur = formatDuration(totalDuration);

                currentFeature.properties = {
                  ...currentFeature.properties,
                  routedGeometry: { type: "LineString", coordinates: fullCoordinates },
                  routeDuration: totalDuration,
                  routeDistance: totalDistance,
                  routingProfile: profile,
                  formattedDuration: formattedDur,
                  isRoutedFeature: true,
                  routeWaypoints: extractedWaypoints,
                  routeSegments: allSegments,
                };

                if (ctxRef && ctxRef.store) {
                  ctxRef.store.featureChanged(featureId);
                }

                mapRef.fire(Constants.events.RENDER);
                mapRef.fire("draw.render");

                mapRef.fire("draw.update", {
                  features: [
                    {
                      type: "Feature" as const,
                      id: featureId,
                      properties: currentFeature.properties,
                      geometry: {
                        type: "LineString" as const,
                        coordinates: fullCoordinates,
                      },
                    },
                  ],
                  action: "change_coordinates",
                });

                // Force re-render using MapboxDraw API
                try {
                  if (ctxRef && ctxRef.api) {
                    try {
                      ctxRef.api.delete(featureId);
                    } catch {
                      // Feature might not exist
                    }

                    ctxRef.api.add({
                      type: "Feature",
                      id: featureId,
                      properties: currentFeature.properties,
                      geometry: {
                        type: "LineString",
                        coordinates: fullCoordinates,
                      },
                    });
                  }
                } catch {
                  // Silently handle errors
                }

                // Delayed backup
                setTimeout(() => {
                  try {
                    if (ctxRef && ctxRef.api) {
                      const existing = ctxRef.api.get(featureId);
                      if (!existing) {
                        ctxRef.api.add({
                          type: "Feature",
                          id: featureId,
                          properties: currentFeature.properties,
                          geometry: {
                            type: "LineString",
                            coordinates: fullCoordinates,
                          },
                        });
                      }
                    }
                  } catch {
                    // Silently handle errors
                  }
                }, 100);
              })
              .catch(() => {
                // Silently handle errors
              });
          }
        }
      }

      // Force re-render
      if (this._ctx && this._ctx.store) {
        this._ctx.store.featureChanged(state.line.id);
      }
      this.map.fire(Constants.events.RENDER);
      this.map.fire("draw.render");
      if (this.map.triggerRepaint) {
        this.map.triggerRepaint();
      }

      this.updateUIClasses({ mouse: Constants.cursors.POINTER });

      // Fire the create event
      this.map.fire(Constants.events.CREATE, {
        features: [feature.toGeoJSON()],
      });
    } else {
      // Invalid - delete silently
      this.deleteFeature(state.line.id, { silent: true });
    }

    // Clean up
    confirmedRoute = null;
    previewSegment = null;
    segmentQueue = [];
    isProcessingQueue = false;
    isLoadingRoute = false;
    clickedWaypoints = [];
    routeSegments = [];
  };

  // Override onKeyUp to handle escape and enter
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  RoutingMode.onKeyUp = function (this: any, state: any, e: any) {
    if (e.keyCode === 27) {
      // Escape - cancel drawing
      this.deleteFeature(state.line.id, { silent: true });
      this.changeMode(Constants.modes.SIMPLE_SELECT);
    } else if (e.keyCode === 13) {
      // Enter - finish
      const coords = this.getFeature(state.line.id)?.coordinates;
      if (coords && coords.length >= 2) {
        this.changeMode(Constants.modes.SIMPLE_SELECT, {
          featureIds: [state.line.id],
        });
      }
    }
  };

  // Override onTrash
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  RoutingMode.onTrash = function (this: any, state: any) {
    return DrawLineString.onTrash?.call(this, state);
  };

  return RoutingMode;
}
