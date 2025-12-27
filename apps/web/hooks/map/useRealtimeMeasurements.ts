"use client";

import area from "@turf/area";
import bearing from "@turf/bearing";
import circle from "@turf/circle";
import distance from "@turf/distance";
import length from "@turf/length";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { useDraw } from "@/lib/providers/DrawProvider";
import type { Measurement } from "@/lib/store/map/slice";
import {
  formatArea as formatAreaByUnit,
  formatDistance as formatDistanceByUnit,
  resolveUnitSystem,
} from "@/lib/utils/measurementUnits";

import { usePreferredUnitSystem } from "@/hooks/settings/usePreferredUnitSystem";
import { useAppSelector } from "@/hooks/store/ContextHooks";

/**
 * Hook that provides real-time measurement values by reading from drawControl.
 * This includes both completed measurements (being edited) and features being drawn.
 */
export function useRealtimeMeasurements(): Measurement[] {
  const { drawControl } = useDraw();
  const measurements = useAppSelector((state) => state.map.measurements);
  const activeTool = useAppSelector((state) => state.map.activeMeasureTool);
  const { unit: systemUnit } = usePreferredUnitSystem();
  const { i18n } = useTranslation();
  const [realtimeMeasurements, setRealtimeMeasurements] = useState<Measurement[]>(measurements);
  const animationFrameRef = useRef<number | null>(null);
  const locale = i18n.language || "en-US";

  const resolveUnit = useCallback(
    (unitPreference?: Measurement["unitSystem"]) => resolveUnitSystem(unitPreference, systemUnit),
    [systemUnit]
  );

  // Calculate real-time values for a measurement based on current geometry
  const calculateRealtimeValues = useCallback(
    (measurement: Measurement, geometry: GeoJSON.Geometry): Measurement => {
      if (measurement.type === "line" && geometry.type === "LineString") {
        const lineLength = length({ type: "Feature", properties: {}, geometry }, { units: "meters" });
        const unit = resolveUnit(measurement.unitSystem);
        return {
          ...measurement,
          value: lineLength,
          formattedValue: formatDistanceByUnit(lineLength, unit, locale),
          geometry,
        };
      } else if (measurement.type === "distance" && geometry.type === "LineString") {
        // For flight distance, we still show total length in real-time
        const lineLength = length({ type: "Feature", properties: {}, geometry }, { units: "meters" });
        const unit = resolveUnit(measurement.unitSystem);
        return {
          ...measurement,
          value: lineLength,
          formattedValue: formatDistanceByUnit(lineLength, unit, locale),
          geometry,
        };
      } else if (measurement.type === "area" && geometry.type === "Polygon") {
        const polygonArea = area({ type: "Feature", properties: {}, geometry });
        const coords = geometry.coordinates[0];
        const perimeterLine = {
          type: "Feature" as const,
          properties: {},
          geometry: {
            type: "LineString" as const,
            coordinates: coords,
          },
        };
        const perimeterLength = length(perimeterLine, { units: "meters" });

        const unit = resolveUnit(measurement.unitSystem);
        return {
          ...measurement,
          value: polygonArea,
          formattedValue: formatAreaByUnit(polygonArea, unit, locale),
          geometry,
          properties: {
            ...measurement.properties,
            perimeter: perimeterLength,
            formattedPerimeter: formatDistanceByUnit(perimeterLength, unit, locale),
          },
        };
      } else if (measurement.type === "circle") {
        // Circle measurements: DrawControl stores a LineString (center + edge),
        // but measurement.geometry stores the calculated Polygon for display
        if (geometry.type === "LineString") {
          // Recalculate from the radius line (this is the real-time update during editing)
          const coords = geometry.coordinates as GeoJSON.Position[];
          if (coords.length < 2) return measurement;

          const center = coords[0] as [number, number];
          const edge = coords[1] as [number, number];
          const radiusKm = distance(center, edge, { units: "kilometers" });
          const radiusMeters = radiusKm * 1000;

          // Generate circle polygon for area calculation
          const circlePolygon = circle(center, radiusKm, { units: "kilometers", steps: 64 });
          const circleArea = area(circlePolygon);
          const perimeter = 2 * Math.PI * radiusMeters;

          // Calculate azimuth
          const azimuthDegrees = bearing(center, edge);
          const normalizedAzimuth = ((azimuthDegrees % 360) + 360) % 360;

          const unit = resolveUnit(measurement.unitSystem);
          return {
            ...measurement,
            value: circleArea,
            formattedValue: formatAreaByUnit(circleArea, unit, locale),
            geometry: circlePolygon.geometry, // Use calculated polygon for display
            properties: {
              ...measurement.properties,
              perimeter,
              formattedPerimeter: formatDistanceByUnit(perimeter, unit, locale),
              radius: radiusMeters,
              formattedRadius: formatDistanceByUnit(radiusMeters, unit, locale),
              azimuth: normalizedAzimuth,
              formattedAzimuth: `${normalizedAzimuth.toFixed(1)}°`,
              center,
            },
          };
        } else if (geometry.type === "Polygon") {
          // Fallback: if geometry is already a polygon (stored measurement display)
          const circleArea = area({ type: "Feature", properties: {}, geometry });
          const radiusMeters = Math.sqrt(circleArea / Math.PI);
          const perimeter = 2 * Math.PI * radiusMeters;

          const unit = resolveUnit(measurement.unitSystem);
          return {
            ...measurement,
            value: circleArea,
            formattedValue: formatAreaByUnit(circleArea, unit, locale),
            geometry,
            properties: {
              ...measurement.properties,
              perimeter,
              formattedPerimeter: formatDistanceByUnit(perimeter, unit, locale),
              radius: radiusMeters,
              formattedRadius: formatDistanceByUnit(radiusMeters, unit, locale),
              azimuth: measurement.properties?.azimuth,
              formattedAzimuth: measurement.properties?.formattedAzimuth,
            },
          };
        }
      }

      return measurement;
    },
    [locale, resolveUnit]
  );

  // Create a temporary measurement for a feature being drawn
  const createDrawingMeasurement = useCallback(
    (feature: GeoJSON.Feature, toolType: string): Measurement | null => {
      const geometry = feature.geometry;
      const featureId = feature.id as string;

      if (toolType === "line" && geometry.type === "LineString") {
        const coords = geometry.coordinates;
        if (coords.length < 2) return null;
        const lineLength = length(feature as GeoJSON.Feature<GeoJSON.LineString>, { units: "meters" });
        const unit = resolveUnit("default");
        return {
          id: `drawing-${featureId}`,
          drawFeatureId: featureId,
          type: "line",
          value: lineLength,
          formattedValue: formatDistanceByUnit(lineLength, unit, locale),
          geometry: geometry as GeoJSON.LineString,
          unitSystem: "default",
        };
      } else if (toolType === "distance" && geometry.type === "LineString") {
        const coords = geometry.coordinates;
        if (coords.length < 2) return null;
        const lineLength = length(feature as GeoJSON.Feature<GeoJSON.LineString>, { units: "meters" });
        const unit = resolveUnit("default");
        return {
          id: `drawing-${featureId}`,
          drawFeatureId: featureId,
          type: "distance",
          value: lineLength,
          formattedValue: formatDistanceByUnit(lineLength, unit, locale),
          geometry: geometry as GeoJSON.LineString,
          unitSystem: "default",
        };
      } else if (toolType === "area" && geometry.type === "Polygon") {
        const coords = geometry.coordinates[0];
        if (coords.length < 4) return null; // Need at least 3 points + closing point
        const polygonArea = area(feature as GeoJSON.Feature<GeoJSON.Polygon>);
        const perimeterLine = {
          type: "Feature" as const,
          properties: {},
          geometry: {
            type: "LineString" as const,
            coordinates: coords,
          },
        };
        const perimeterLength = length(perimeterLine, { units: "meters" });
        const unit = resolveUnit("default");
        return {
          id: `drawing-${featureId}`,
          drawFeatureId: featureId,
          type: "area",
          value: polygonArea,
          formattedValue: formatAreaByUnit(polygonArea, unit, locale),
          geometry: geometry as GeoJSON.Polygon,
          properties: {
            perimeter: perimeterLength,
            formattedPerimeter: formatDistanceByUnit(perimeterLength, unit, locale),
          },
          unitSystem: "default",
        };
      } else if (toolType === "circle" && geometry.type === "LineString") {
        // Circle is drawn as a LineString (center to edge), generate circle polygon
        const coords = geometry.coordinates as GeoJSON.Position[];
        if (coords.length < 2) return null;

        const center = coords[0] as [number, number];
        const edge = coords[coords.length - 1] as [number, number];

        // Calculate radius and azimuth
        const radiusKm = distance(center, edge, { units: "kilometers" });
        const radiusMeters = radiusKm * 1000;
        const azimuthDegrees = bearing(center, edge);
        const normalizedAzimuth = ((azimuthDegrees % 360) + 360) % 360;

        // Generate circle polygon
        const circlePolygon = circle(center, radiusKm, { units: "kilometers", steps: 64 });
        const circleGeometry = circlePolygon.geometry;

        // Calculate area and perimeter
        const circleArea = area(circlePolygon);
        const circleCoords = circleGeometry.coordinates[0];
        const perimeterLine = {
          type: "Feature" as const,
          properties: {},
          geometry: {
            type: "LineString" as const,
            coordinates: circleCoords,
          },
        };
        const perimeterLength = length(perimeterLine, { units: "meters" });

        const unit = resolveUnit("default");
        return {
          id: `drawing-${featureId}`,
          drawFeatureId: featureId,
          type: "circle" as const,
          value: circleArea,
          formattedValue: formatAreaByUnit(circleArea, unit, locale),
          geometry: circleGeometry,
          properties: {
            perimeter: perimeterLength,
            formattedPerimeter: formatDistanceByUnit(perimeterLength, unit, locale),
            radius: radiusMeters,
            formattedRadius: formatDistanceByUnit(radiusMeters, unit, locale),
            azimuth: normalizedAzimuth,
            formattedAzimuth: `${normalizedAzimuth.toFixed(1)}°`,
            center,
          },
          unitSystem: "default",
        };
      }

      return null;
    },
    [locale, resolveUnit]
  );

  // Update measurements with real-time values
  const updateMeasurements = useCallback(() => {
    if (!drawControl) {
      setRealtimeMeasurements(measurements);
      return;
    }

    try {
      const allFeatures = drawControl.getAll();
      const featureMap = new Map<string, GeoJSON.Feature>();

      // Build a map of feature IDs to their current features
      allFeatures.features.forEach((feature) => {
        if (feature.id) {
          featureMap.set(feature.id as string, feature);
        }
      });

      // Update existing measurements with real-time geometries
      const updated = measurements.map((measurement) => {
        const currentFeature = featureMap.get(measurement.drawFeatureId);
        if (currentFeature) {
          return calculateRealtimeValues(measurement, currentFeature.geometry);
        }
        return measurement;
      });

      // Find features being drawn (not yet in measurements)
      const drawingMeasurements: Measurement[] = [];
      if (activeTool) {
        allFeatures.features.forEach((feature) => {
          const featureId = feature.id as string;
          const isCompleted = measurements.some((m) => m.drawFeatureId === featureId);
          if (!isCompleted) {
            const drawingMeasurement = createDrawingMeasurement(feature, activeTool);
            if (drawingMeasurement) {
              drawingMeasurements.push(drawingMeasurement);
            }
          }
        });
      }

      // Combine completed measurements with drawing measurements
      setRealtimeMeasurements([...updated, ...drawingMeasurements]);
    } catch {
      // DrawControl may not be ready yet
      setRealtimeMeasurements(measurements);
    }
  }, [drawControl, measurements, activeTool, calculateRealtimeValues, createDrawingMeasurement]);

  // Set up animation frame loop for real-time updates
  useEffect(() => {
    // Run the loop if we have measurements OR an active tool (drawing)
    const shouldAnimate = measurements.length > 0 || activeTool;

    if (!shouldAnimate) {
      setRealtimeMeasurements([]);
      return;
    }

    const animate = () => {
      updateMeasurements();
      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [measurements.length, activeTool, updateMeasurements]);

  return realtimeMeasurements;
}

export default useRealtimeMeasurements;
