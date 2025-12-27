"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { useMeasure } from "@/lib/providers/MeasureProvider";
import type { MeasureToolType, Measurement } from "@/lib/store/map/slice";
import type { UnitPreference } from "@/lib/utils/measurementUnits";

import { useRealtimeMeasurements } from "@/hooks/map/useRealtimeMeasurements";
import { useAppSelector } from "@/hooks/store/ContextHooks";

export interface UseMeasureToolReturn {
  // State
  measureOpen: boolean;
  isMeasureActive: boolean;
  activeMeasureTool: MeasureToolType | undefined;
  measurements: Measurement[];
  realtimeMeasurements: Measurement[];
  selectedMeasurementId: string | undefined;

  // Handlers
  handleMeasureToggle: (open: boolean) => void;
  handleMeasureToolSelect: (tool: MeasureToolType) => void;
  handleMeasureClose: () => void;
  selectMeasurement: (measurementId: string) => void;
  deleteMeasurement: (measurementId: string) => void;
  setMeasurementUnitSystem: (measurementId: string, unitSystem: UnitPreference) => void;
  deactivateTool: () => void;
  zoomToMeasurement: (measurementId: string) => void;
}

/**
 * Hook that encapsulates all measure tool logic for reuse across different layouts.
 * This hook manages:
 * - Measure tool open/close state
 * - Active tool selection
 * - Measurements list (both Redux and real-time)
 * - All event handlers for the measure functionality
 */
export function useMeasureTool(): UseMeasureToolReturn {
  const {
    startMeasuring,
    stopMeasuring,
    deactivateTool,
    activeTool: activeMeasureTool,
    selectMeasurement,
    deleteMeasurement,
    setMeasurementUnitSystem,
    zoomToMeasurement,
  } = useMeasure();

  const measurements = useAppSelector((state) => state.map.measurements);
  const realtimeMeasurements = useRealtimeMeasurements();
  const selectedMeasurementId = useAppSelector((state) => state.map.selectedMeasurementId);

  // Local state for menu open
  const [measureOpen, setMeasureOpen] = useState(false);

  // Track when we transition from having measurements to none to fully reset the tool
  const previousMeasurementCountRef = useRef(measurements.length);

  useEffect(() => {
    if (previousMeasurementCountRef.current > 0 && measurements.length === 0) {
      setMeasureOpen(false);
      stopMeasuring();
    }

    previousMeasurementCountRef.current = measurements.length;
  }, [measurements.length, stopMeasuring]);

  // Determine if the measure button should appear active (green)
  const isMeasureActive = measureOpen || activeMeasureTool !== undefined || measurements.length > 0;

  const handleMeasureToggle = useCallback(
    (open: boolean) => {
      setMeasureOpen(open);
      if (!open && measurements.length === 0) {
        // Only fully stop if there are no measurements
        stopMeasuring();
      } else if (!open) {
        // Just deactivate the tool, keep measurements
        deactivateTool();
      }
    },
    [measurements.length, stopMeasuring, deactivateTool]
  );

  const handleMeasureToolSelect = useCallback(
    (tool: MeasureToolType) => {
      startMeasuring(tool);
      setMeasureOpen(true);
    },
    [startMeasuring]
  );

  const handleMeasureClose = useCallback(() => {
    setMeasureOpen(false);
    stopMeasuring();
  }, [stopMeasuring]);

  return {
    // State
    measureOpen,
    isMeasureActive,
    activeMeasureTool,
    measurements,
    realtimeMeasurements,
    selectedMeasurementId,

    // Handlers
    handleMeasureToggle,
    handleMeasureToolSelect,
    handleMeasureClose,
    selectMeasurement,
    deleteMeasurement,
    setMeasurementUnitSystem,
    deactivateTool,
    zoomToMeasurement,
  };
}

export default useMeasureTool;
