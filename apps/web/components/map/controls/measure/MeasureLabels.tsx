"use client";

import area from "@turf/area";
import bbox from "@turf/bbox";
import bearing from "@turf/bearing";
import centroid from "@turf/centroid";
import circle from "@turf/circle";
import distance from "@turf/distance";
import length from "@turf/length";
import type { Map as MaplibreMap } from "maplibre-gl";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Popup, useMap } from "react-map-gl/maplibre";

import { useDraw } from "@/lib/providers/DrawProvider";
import {
  type UnitSystem,
  formatArea as formatAreaByUnit,
  formatDistance as formatDistanceByUnit,
  resolveUnitSystem,
} from "@/lib/utils/measurementUnits";

import { usePreferredUnitSystem } from "@/hooks/settings/usePreferredUnitSystem";
import { useAppSelector } from "@/hooks/store/ContextHooks";

interface LabelData {
  id: string;
  coordinates: [number, number];
  label: string;
  type: "line" | "area" | "perimeter" | "radius" | "azimuth" | "route";
  visible: boolean; // Whether to show based on zoom/size
}

// Minimum screen size (in pixels) for a feature to show its label
const MIN_FEATURE_SCREEN_SIZE = 60;

// Calculate the screen size of a geometry (diagonal of bounding box in pixels)
function getFeatureScreenSize(geometry: GeoJSON.Geometry, mapInstance: MaplibreMap): number {
  try {
    const [minLng, minLat, maxLng, maxLat] = bbox({ type: "Feature", properties: {}, geometry });

    // Project corners to screen coordinates
    const topLeft = mapInstance.project([minLng, maxLat]);
    const bottomRight = mapInstance.project([maxLng, minLat]);

    // Calculate diagonal distance in pixels
    const dx = bottomRight.x - topLeft.x;
    const dy = bottomRight.y - topLeft.y;
    return Math.sqrt(dx * dx + dy * dy);
  } catch {
    return Infinity; // If calculation fails, show the label
  }
}

// Get the last coordinate of a geometry (for label placement)
function getEndCoordinate(geometry: GeoJSON.Geometry): [number, number] | null {
  if (geometry.type === "LineString") {
    const coords = geometry.coordinates;
    return coords[coords.length - 1] as [number, number];
  }
  if (geometry.type === "Polygon") {
    const coords = geometry.coordinates[0];
    // Return the second-to-last coordinate (last unique point before closing)
    return coords[coords.length - 2] as [number, number];
  }
  return null;
}

// Get centroid of a polygon
function getCentroid(geometry: GeoJSON.Geometry): [number, number] | null {
  if (geometry.type === "Polygon") {
    const center = centroid({ type: "Feature", properties: {}, geometry });
    return center.geometry.coordinates as [number, number];
  }
  return null;
}

// Calculate labels for a feature based on its geometry and type
function calculateLabelsForFeature(
  featureId: string,
  geometry: GeoJSON.Geometry,
  measurementType: "line" | "distance" | "area" | "circle" | "walking" | "car",
  mapInstance: MaplibreMap | null,
  unitSystem: UnitSystem,
  locale: string,
  properties?: {
    radius?: number;
    formattedRadius?: string;
    azimuth?: number;
    formattedAzimuth?: string;
    perimeter?: number;
    formattedPerimeter?: string;
    routeDistance?: number;
    duration?: number;
    formattedDuration?: string;
    transfers?: number;
  }
): LabelData[] {
  const labels: LabelData[] = [];

  // Calculate if labels should be visible based on screen size
  const screenSize = mapInstance ? getFeatureScreenSize(geometry, mapInstance) : Infinity;
  const visible = screenSize >= MIN_FEATURE_SCREEN_SIZE;

  if (measurementType === "line" && geometry.type === "LineString") {
    const lineLength = length({ type: "Feature", properties: {}, geometry }, { units: "meters" });
    const coord = getEndCoordinate(geometry);
    if (coord) {
      labels.push({
        id: `${featureId}-length`,
        coordinates: coord,
        label: formatDistanceByUnit(lineLength, unitSystem, locale),
        type: "line",
        visible,
      });
    }
  } else if (measurementType === "distance" && geometry.type === "LineString") {
    // Flight distance - we still show the full line length in the label
    const lineLength = length({ type: "Feature", properties: {}, geometry }, { units: "meters" });
    const coord = getEndCoordinate(geometry);
    if (coord) {
      labels.push({
        id: `${featureId}-length`,
        coordinates: coord,
        label: formatDistanceByUnit(lineLength, unitSystem, locale),
        type: "line",
        visible,
      });
    }
  } else if (measurementType === "area" && geometry.type === "Polygon") {
    const polygonArea = area({ type: "Feature", properties: {}, geometry });
    const coords = geometry.coordinates[0];

    // Area label at centroid
    const centerCoord = getCentroid(geometry);
    if (centerCoord) {
      labels.push({
        id: `${featureId}-area`,
        coordinates: centerCoord,
        label: formatAreaByUnit(polygonArea, unitSystem, locale),
        type: "area",
        visible,
      });
    }

    // Perimeter label at end point
    const perimeterLine = {
      type: "Feature" as const,
      properties: {},
      geometry: {
        type: "LineString" as const,
        coordinates: coords,
      },
    };
    const perimeterLength = length(perimeterLine, { units: "meters" });
    const endCoord = getEndCoordinate(geometry);
    if (endCoord) {
      labels.push({
        id: `${featureId}-perimeter`,
        coordinates: endCoord,
        label: formatDistanceByUnit(perimeterLength, unitSystem, locale),
        type: "perimeter",
        visible,
      });
    }
  } else if (measurementType === "circle" && geometry.type === "Polygon") {
    // Circle measurement - polygon geometry (from measurement.geometry or display)
    const circleArea = area({ type: "Feature", properties: {}, geometry });
    const radiusMeters = properties?.radius ?? Math.sqrt(circleArea / Math.PI);
    const perimeterMeters = properties?.perimeter ?? 2 * Math.PI * radiusMeters;
    const areaLabel = formatAreaByUnit(circleArea, unitSystem, locale);
    const perimeterLabel =
      properties?.formattedPerimeter ?? formatDistanceByUnit(perimeterMeters, unitSystem, locale);
    const areaWithPerimeter = perimeterLabel ? `${areaLabel} / ${perimeterLabel}` : areaLabel;

    // Area label at centroid (center of circle)
    const centerCoord = getCentroid(geometry);
    if (centerCoord) {
      labels.push({
        id: `${featureId}-area`,
        coordinates: centerCoord,
        label: areaWithPerimeter,
        type: "area",
        visible,
      });
    }

    // Radius label at edge - use properties if provided, otherwise calculate from area
    const specifiedAzimuth = properties?.formattedAzimuth;
    const azimuthLabel = specifiedAzimuth
      ? specifiedAzimuth
      : typeof properties?.azimuth === "number"
        ? `${properties.azimuth.toFixed(1)}°`
        : undefined;
    const specifiedRadiusLabel = properties?.formattedRadius;
    const radiusLabel = specifiedRadiusLabel ?? formatDistanceByUnit(radiusMeters, unitSystem, locale);
    const radiusWithAzimuth = azimuthLabel ? `${radiusLabel} / ${azimuthLabel}` : radiusLabel;
    const endCoord = getEndCoordinate(geometry);
    if (endCoord) {
      labels.push({
        id: `${featureId}-radius`,
        coordinates: endCoord,
        label: radiusWithAzimuth,
        type: "radius",
        visible,
      });
    }
  } else if (measurementType === "circle" && geometry.type === "LineString") {
    // Circle measurement - LineString geometry (radius line from drawControl during editing)
    const coords = geometry.coordinates as [number, number][];
    if (coords.length >= 2) {
      const center = coords[0];
      const edge = coords[1];
      const radiusKm = distance(center, edge, { units: "kilometers" });
      const radiusMeters = radiusKm * 1000;
      const azimuthDegrees = bearing(center, edge);
      const normalizedAzimuth = ((azimuthDegrees % 360) + 360) % 360;
      const azimuthLabel = `${normalizedAzimuth.toFixed(1)}°`;
      const radiusLabel = formatDistanceByUnit(radiusMeters, unitSystem, locale);
      const combinedRadiusLabel = `${radiusLabel} / ${azimuthLabel}`;
      // Generate circle for area calculation
      const circlePolygon = circle(center, radiusKm, { units: "kilometers", steps: 64 });
      const circleArea = area(circlePolygon);
      const perimeterMeters = 2 * Math.PI * radiusMeters;
      const perimeterLabel = formatDistanceByUnit(perimeterMeters, unitSystem, locale);
      const areaLabel = formatAreaByUnit(circleArea, unitSystem, locale);
      const areaWithPerimeter = `${areaLabel} / ${perimeterLabel}`;

      // Area label at center
      labels.push({
        id: `${featureId}-area`,
        coordinates: center,
        label: areaWithPerimeter,
        type: "area",
        visible,
      });

      // Radius label at edge
      labels.push({
        id: `${featureId}-radius`,
        coordinates: edge,
        label: combinedRadiusLabel,
        type: "radius",
        visible,
      });
    }
  }

  // Routing-based measurements (walking, car)
  if ((measurementType === "walking" || measurementType === "car") && geometry.type === "LineString") {
    const routeDistance = properties?.routeDistance || 0;
    const routeDuration = properties?.formattedDuration;
    const coord = getEndCoordinate(geometry);

    if (coord && routeDuration) {
      const routeLabel = `${formatDistanceByUnit(routeDistance, unitSystem, locale)} / ${routeDuration}`;

      labels.push({
        id: `${featureId}-route`,
        coordinates: coord,
        label: routeLabel,
        type: "route",
        visible,
      });
    }
  }

  return labels;
}

// Label popup component with MUI Chip-like styling (no arrow)
function MeasureLabel({ label }: { label: LabelData }) {
  return (
    <Popup
      longitude={label.coordinates[0]}
      latitude={label.coordinates[1]}
      closeButton={false}
      closeOnClick={false}
      anchor="bottom"
      offset={[0, -12] as [number, number]}
      className="measure-label-popup"
      style={{ pointerEvents: "none" }}>
      <div
        style={{
          backgroundColor: "#dc2626",
          color: "white",
          padding: "4px 12px",
          borderRadius: "16px",
          fontSize: "12px",
          fontWeight: 600,
          whiteSpace: "nowrap",
          boxShadow: "0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)",
          lineHeight: "1.4",
          pointerEvents: "none",
        }}>
        {label.label}
      </div>
    </Popup>
  );
}

export function MeasureLabels() {
  const { map } = useMap();
  const { drawControl } = useDraw();
  const measurements = useAppSelector((state) => state.map.measurements);
  const activeTool = useAppSelector((state) => state.map.activeMeasureTool);
  const [labels, setLabels] = useState<LabelData[]>([]);
  const animationFrameRef = useRef<number | null>(null);
  const { unit: systemUnit } = usePreferredUnitSystem();
  const { i18n } = useTranslation();
  const locale = i18n.language || "en-US";

  // Update all labels in real-time (for both drawing and editing)
  const updateLabels = useCallback(() => {
    if (!drawControl) {
      setLabels([]);
      return;
    }

    // Get the map instance for screen size calculations
    const mapInstance = map?.getMap() || null;

    try {
      const allFeatures = drawControl.getAll();
      const newLabels: LabelData[] = [];

      // Process each feature in drawControl
      allFeatures.features.forEach((feature) => {
        const geometry = feature.geometry;
        const featureId = feature.id as string;

        // Find if this feature belongs to a measurement
        const measurement = measurements.find((m) => m.drawFeatureId === featureId);

        if (measurement) {
          // This is a completed measurement - calculate labels from real-time geometry
          const resolvedUnit = resolveUnitSystem(measurement.unitSystem, systemUnit);
          const calculatedLabels = calculateLabelsForFeature(
            measurement.id,
            geometry,
            measurement.type as "line" | "distance" | "area" | "circle" | "walking" | "car",
            mapInstance,
            resolvedUnit,
            locale,
            measurement.properties
          );
          newLabels.push(...calculatedLabels);
        } else if (activeTool) {
          // This is a feature being drawn (not yet in measurements)
          // Always show labels while actively drawing (visible = true)
          if (
            geometry.type === "LineString" &&
            (activeTool === "line" ||
              activeTool === "distance" ||
              activeTool === "walking" ||
              activeTool === "car")
          ) {
            const coords = geometry.coordinates;
            if (coords.length >= 2) {
              // For routing modes, check if we have route data in properties
              const props = (feature as GeoJSON.Feature).properties || {};
              const isRoutingMode = activeTool === "walking" || activeTool === "car";

              if (isRoutingMode && props.routeDuration !== undefined) {
                // Show route information at the end of the routed line geometry
                // Use the last coordinate from the routed geometry, not the waypoint
                const routedGeometry = props.routedGeometry as GeoJSON.LineString | undefined;
                const routedCoords = routedGeometry?.coordinates;
                const labelCoord =
                  routedCoords && routedCoords.length > 0
                    ? (routedCoords[routedCoords.length - 1] as [number, number])
                    : (coords[coords.length - 2] as [number, number]); // Fallback to last waypoint

                const routeDistance = props.routeDistance || 0;
                const formattedDuration =
                  props.formattedDuration || `${Math.floor(props.routeDuration / 60)}min`;

                const routeLabel = `${formatDistanceByUnit(routeDistance, systemUnit, locale)} / ${formattedDuration}`;

                newLabels.push({
                  id: `drawing-${featureId}-route`,
                  coordinates: labelCoord,
                  label: routeLabel,
                  type: "route",
                  visible: true,
                });
              } else if (isRoutingMode && props.routeDistance !== undefined && props.isRoutingError) {
                // Routing failed - show straight-line distance without duration
                const routedGeometry = props.routedGeometry as GeoJSON.LineString | undefined;
                const routedCoords = routedGeometry?.coordinates;
                const labelCoord =
                  routedCoords && routedCoords.length > 0
                    ? (routedCoords[routedCoords.length - 1] as [number, number])
                    : (coords[coords.length - 2] as [number, number]);

                const routeDistance = props.routeDistance || 0;
                const routeLabel = `${formatDistanceByUnit(routeDistance, systemUnit, locale)} (straight line)`;

                newLabels.push({
                  id: `drawing-${featureId}-route`,
                  coordinates: labelCoord,
                  label: routeLabel,
                  type: "route",
                  visible: true,
                });
              } else {
                // Show simple line length while waiting for route
                const lineLength = length(feature as GeoJSON.Feature<GeoJSON.LineString>, {
                  units: "meters",
                });
                // For routing modes during loading, show at last waypoint instead of ghost point
                const labelCoord =
                  isRoutingMode && coords.length > 2
                    ? (coords[coords.length - 2] as [number, number])
                    : (coords[coords.length - 1] as [number, number]);
                newLabels.push({
                  id: `drawing-${featureId}-length`,
                  coordinates: labelCoord,
                  label: isRoutingMode ? "Loading..." : formatDistanceByUnit(lineLength, systemUnit, locale),
                  type: "line",
                  visible: true,
                });
              }
            }
          } else if (geometry.type === "Polygon" && activeTool === "area") {
            const coords = geometry.coordinates[0];
            if (coords.length >= 3) {
              // Perimeter at cursor
              const perimeterLine = {
                type: "Feature" as const,
                properties: {},
                geometry: {
                  type: "LineString" as const,
                  coordinates: coords,
                },
              };
              const perimeterLength = length(perimeterLine, { units: "meters" });
              const cursorCoord = coords[coords.length - 2] as [number, number];
              newLabels.push({
                id: `drawing-${featureId}-perimeter`,
                coordinates: cursorCoord,
                label: formatDistanceByUnit(perimeterLength, systemUnit, locale),
                type: "perimeter",
                visible: true, // Always show while drawing
              });

              // Area at centroid (only if polygon has enough points)
              if (coords.length > 4) {
                const polygonArea = area(feature as GeoJSON.Feature<GeoJSON.Polygon>);
                const center = centroid(feature as GeoJSON.Feature<GeoJSON.Polygon>);
                newLabels.push({
                  id: `drawing-${featureId}-area`,
                  coordinates: center.geometry.coordinates as [number, number],
                  label: formatAreaByUnit(polygonArea, systemUnit, locale),
                  type: "area",
                  visible: true, // Always show while drawing
                });
              }
            }
          } else if (geometry.type === "LineString" && activeTool === "circle") {
            // Circle is drawn as a LineString (center to edge)
            const coords = geometry.coordinates;
            if (coords.length >= 2) {
              const center = coords[0] as [number, number];
              const edge = coords[coords.length - 1] as [number, number];

              // Calculate radius
              const radiusKm = distance(center, edge, { units: "kilometers" });
              const radiusMeters = radiusKm * 1000;
              const azimuthDegrees = bearing(center, edge);
              const normalizedAzimuth = ((azimuthDegrees % 360) + 360) % 360;
              const azimuthLabel = `${normalizedAzimuth.toFixed(1)}°`;
              const radiusLabel = formatDistanceByUnit(radiusMeters, systemUnit, locale);
              const combinedRadiusLabel = `${radiusLabel} / ${azimuthLabel}`;

              // Generate circle polygon for area calculation
              const circlePolygon = circle(center, radiusKm, { units: "kilometers", steps: 64 });
              const circleArea = area(circlePolygon);
              const perimeterMeters = 2 * Math.PI * radiusMeters;
              const perimeterLabel = formatDistanceByUnit(perimeterMeters, systemUnit, locale);
              const areaLabel = formatAreaByUnit(circleArea, systemUnit, locale);
              const areaWithPerimeter = `${areaLabel} / ${perimeterLabel}`;

              // Area at center
              newLabels.push({
                id: `drawing-${featureId}-area`,
                coordinates: center,
                label: areaWithPerimeter,
                type: "area",
                visible: true,
              });

              // Radius at edge
              newLabels.push({
                id: `drawing-${featureId}-radius`,
                coordinates: edge,
                label: combinedRadiusLabel,
                type: "radius",
                visible: true,
              });
            }
          }
        }
      });

      setLabels(newLabels);
    } catch {
      // DrawControl may not be ready yet
      setLabels([]);
    }
  }, [drawControl, activeTool, measurements, map, systemUnit, locale]);

  // Set up render loop for real-time updates (during drawing or when measurements exist)
  useEffect(() => {
    // Run the render loop if we have measurements or an active tool
    const shouldAnimate = map && (activeTool || measurements.length > 0);

    if (!shouldAnimate) {
      setLabels([]);
      return;
    }

    const animate = () => {
      updateLabels();
      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [map, activeTool, measurements.length, updateLabels]);

  return (
    <>
      {labels
        .filter((label) => label.visible)
        .map((label) => (
          <MeasureLabel key={label.id} label={label} />
        ))}
    </>
  );
}
