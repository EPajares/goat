"use client";

import type { Measurement } from "@/lib/store/map/slice";
import type { UnitPreference } from "@/lib/utils/measurementUnits";

import { useMeasureTool } from "@/hooks/map/useMeasureTool";

import { Measure, type MeasureToolType } from "./Measure";
import { MeasurementResults } from "./MeasurementResults";

export interface MeasureControlProps {
  /**
   * Whether to show the results panel. If false, only the button is rendered.
   * Useful when you want to position the results panel separately.
   */
  showResults?: boolean;
}

/**
 * Combined Measure control that includes the button and optionally the results panel.
 * This component uses the useMeasureTool hook internally to manage all measure state.
 *
 * For more control over positioning, you can use MeasureButton and MeasureResultsPanel
 * separately with the useMeasureTool hook.
 */
export function MeasureControl({ showResults = true }: MeasureControlProps) {
  const measureTool = useMeasureTool();

  return (
    <>
      <MeasureButton {...measureTool} />
      {showResults && <MeasureResultsPanel {...measureTool} />}
    </>
  );
}

/**
 * Props for components that use the measure tool hook
 */
export interface MeasureToolProps {
  measureOpen: boolean;
  isMeasureActive: boolean;
  activeMeasureTool: MeasureToolType | undefined;
  measurements: Measurement[];
  realtimeMeasurements: Measurement[];
  selectedMeasurementId: string | undefined;
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
 * Measure button component that can be used standalone with useMeasureTool hook
 */
export function MeasureButton({
  isMeasureActive,
  activeMeasureTool,
  handleMeasureToggle,
  handleMeasureToolSelect,
}: Pick<
  MeasureToolProps,
  "isMeasureActive" | "activeMeasureTool" | "handleMeasureToggle" | "handleMeasureToolSelect"
>) {
  return (
    <Measure
      open={isMeasureActive}
      activeTool={activeMeasureTool}
      onToggle={handleMeasureToggle}
      onSelectTool={handleMeasureToolSelect}
    />
  );
}

/**
 * Measure results panel component that can be used standalone with useMeasureTool hook
 */
export function MeasureResultsPanel({
  measureOpen,
  measurements,
  realtimeMeasurements,
  activeMeasureTool,
  selectedMeasurementId,
  handleMeasureClose,
  selectMeasurement,
  deleteMeasurement,
  setMeasurementUnitSystem,
  deactivateTool,
  zoomToMeasurement,
}: Pick<
  MeasureToolProps,
  | "measureOpen"
  | "measurements"
  | "realtimeMeasurements"
  | "activeMeasureTool"
  | "selectedMeasurementId"
  | "handleMeasureClose"
  | "selectMeasurement"
  | "deleteMeasurement"
  | "setMeasurementUnitSystem"
  | "deactivateTool"
  | "zoomToMeasurement"
>) {
  // Only show if menu is open or there are measurements
  if (!measureOpen && measurements.length === 0) {
    return null;
  }

  return (
    <MeasurementResults
      measurements={realtimeMeasurements}
      activeTool={activeMeasureTool}
      selectedMeasurementId={selectedMeasurementId}
      onClose={handleMeasureClose}
      onSelectMeasurement={selectMeasurement}
      onDeleteMeasurement={deleteMeasurement}
      onChangeUnitSystem={setMeasurementUnitSystem}
      onDeactivateTool={deactivateTool}
      onZoomToMeasurement={zoomToMeasurement}
    />
  );
}

export default MeasureControl;
