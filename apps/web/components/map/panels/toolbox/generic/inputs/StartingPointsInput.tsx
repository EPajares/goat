/**
 * Starting Points Input Component
 *
 * Allows selecting starting points either by clicking on the map
 * or by selecting from an existing point layer.
 * Integrates with Redux store for map click handling.
 */
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import { setIsMapGetInfoActive, setMapCursor, setToolboxStartingPoints } from "@/lib/store/map/slice";

import type { SelectorItem } from "@/types/map/common";
import type { ProcessedInput } from "@/types/map/ogc-processes";

import { useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";
import { useLayerByGeomType, useLayerDatasetId } from "@/hooks/map/ToolsHooks";
import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import Selector from "@/components/map/panels/common/Selector";

import StartingPointsTable from "./StartingPointsTable";

/**
 * Starting points value type
 * Either map coordinates or layer reference
 */
interface StartingPointsMapValue {
  latitude: number[];
  longitude: number[];
}

interface StartingPointsLayerValue {
  layer_id: string;
  layer_filter?: Record<string, unknown>;
}

type StartingPointsValue = StartingPointsMapValue | StartingPointsLayerValue | undefined;

interface StartingPointsInputProps {
  input: ProcessedInput;
  value: StartingPointsValue;
  onChange: (value: StartingPointsValue) => void;
  disabled?: boolean;
}

/**
 * Check if value is layer type
 */
function isLayerValue(value: StartingPointsValue): value is StartingPointsLayerValue {
  return value !== undefined && "layer_id" in value;
}

export default function StartingPointsInput({ input, value, onChange, disabled }: StartingPointsInputProps) {
  const { t } = useTranslation("common");
  const dispatch = useAppDispatch();
  const { projectId } = useParams();

  // Get starting points from Redux (for map clicks)
  const toolboxStartingPoints = useAppSelector((state) => state.map.toolboxStartingPoints);

  // Track previous starting points count to detect new additions
  const prevPointsCountRef = useRef<number>(0);

  // Track last emitted layer UUID to prevent infinite loops
  const lastEmittedUuidRef = useRef<string | undefined>(undefined);

  // Track selected layer DB ID for UUID lookup
  const [selectedLayerDbId, setSelectedLayerDbId] = useState<number | undefined>(undefined);

  // Get UUID (layer_id) from DB ID using hook
  const selectedLayerUuid = useLayerDatasetId(selectedLayerDbId, projectId as string);

  // Starting point method options
  const startingPointMethods: SelectorItem[] = useMemo(
    () => [
      {
        value: "map",
        label: t("select_on_map"),
      },
      {
        value: "browser_layer",
        label: t("select_from_point_layer"),
      },
    ],
    [t]
  );

  // Determine initial method from value
  const getInitialMethod = (): SelectorItem => {
    if (isLayerValue(value)) {
      return startingPointMethods[1]; // browser_layer
    }
    return startingPointMethods[0]; // map (default)
  };

  const [method, setMethod] = useState<SelectorItem>(getInitialMethod);

  // Get point layers for layer selector
  const { filteredLayers } = useLayerByGeomType(["feature"], ["point"], projectId as string);

  // Get all project layers to access their filters
  const { layers: projectLayers } = useFilteredProjectLayers(projectId as string);

  // Currently selected layer (for display in dropdown)
  const selectedLayer = useMemo(() => {
    if (selectedLayerDbId !== undefined) {
      return filteredLayers.find((layer) => layer.value === selectedLayerDbId);
    }
    return undefined;
  }, [selectedLayerDbId, filteredLayers]);

  // Get the CQL filter for the selected layer (from project layer query)
  const selectedLayerFilter = useMemo(() => {
    if (selectedLayerDbId === undefined || !projectLayers) return undefined;
    const projectLayer = projectLayers.find((layer) => layer.id === selectedLayerDbId);
    return projectLayer?.query?.cql as Record<string, unknown> | undefined;
  }, [selectedLayerDbId, projectLayers]);

  // Update onChange when UUID is resolved (only if changed)
  useEffect(() => {
    if (method.value === "browser_layer" && selectedLayerDbId !== undefined && selectedLayerUuid) {
      // Only emit if UUID actually changed to prevent infinite loops
      if (lastEmittedUuidRef.current !== selectedLayerUuid) {
        lastEmittedUuidRef.current = selectedLayerUuid;
        const layerValue: StartingPointsLayerValue = {
          layer_id: selectedLayerUuid,
          // Include the layer's active CQL filter if present
          layer_filter: selectedLayerFilter,
        };
        onChange(layerValue);
      }
    }
  }, [selectedLayerUuid, selectedLayerDbId, method.value, onChange, selectedLayerFilter]);

  // Sync Redux starting points with component value (for map method)
  // Only update when points actually change to avoid loops
  useEffect(() => {
    if (method.value !== "map") return;

    const currentCount = toolboxStartingPoints?.length ?? 0;

    // Only call onChange when points change
    if (currentCount !== prevPointsCountRef.current) {
      prevPointsCountRef.current = currentCount;

      if (toolboxStartingPoints && toolboxStartingPoints.length > 0) {
        const newValue: StartingPointsMapValue = {
          latitude: toolboxStartingPoints.map((p) => p[1]),
          longitude: toolboxStartingPoints.map((p) => p[0]),
        };
        onChange(newValue);
      } else {
        onChange(undefined);
      }
    }
  }, [toolboxStartingPoints, method.value, onChange]);

  // Enable/disable map click mode based on method
  useEffect(() => {
    if (!disabled && method.value === "map") {
      dispatch(setIsMapGetInfoActive(false));
      dispatch(setMapCursor("crosshair"));
    } else {
      dispatch(setIsMapGetInfoActive(true));
      dispatch(setMapCursor(undefined));
    }

    return () => {
      // Cleanup on unmount
      dispatch(setIsMapGetInfoActive(true));
      dispatch(setMapCursor(undefined));
    };
  }, [dispatch, disabled, method.value]);

  // Handle method change
  const handleMethodChange = useCallback(
    (item: SelectorItem | SelectorItem[] | undefined) => {
      const newMethod = item as SelectorItem;
      setMethod(newMethod);

      // Clear starting points and layer selection when switching methods
      dispatch(setToolboxStartingPoints(undefined));
      prevPointsCountRef.current = 0;
      setSelectedLayerDbId(undefined);
      lastEmittedUuidRef.current = undefined;
      onChange(undefined);
    },
    [dispatch, onChange]
  );

  // Handle layer selection
  const handleLayerChange = useCallback(
    (item: SelectorItem | SelectorItem[] | undefined) => {
      if (!item || Array.isArray(item)) {
        setSelectedLayerDbId(undefined);
        lastEmittedUuidRef.current = undefined;
        onChange(undefined);
        return;
      }
      // Set DB ID - the useEffect will call onChange with the resolved UUID
      setSelectedLayerDbId(item.value as number);
    },
    [onChange]
  );

  // Get max starting points from widget options
  const maxStartingPoints = input.uiMeta?.widget_options?.max_starting_points as number | undefined;

  return (
    <>
      <Selector
        selectedItems={method}
        setSelectedItems={handleMethodChange}
        items={startingPointMethods}
        label={t("select_starting_point_method")}
        placeholder={t("select_starting_point_method_placeholder")}
        tooltip={t("select_starting_point_method_tooltip")}
        disabled={disabled}
      />

      {method.value === "browser_layer" && (
        <Selector
          selectedItems={selectedLayer}
          setSelectedItems={handleLayerChange}
          items={filteredLayers}
          emptyMessage={t("no_point_layer_found")}
          emptyMessageIcon={ICON_NAME.LAYERS}
          label={t("select_point_layer")}
          placeholder={t("select_point_layer_placeholder")}
          tooltip={t("select_point_layer_tooltip")}
          disabled={disabled}
        />
      )}

      {method.value === "map" && <StartingPointsTable maxStartingPoints={maxStartingPoints} />}
    </>
  );
}
