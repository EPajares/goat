/* eslint-disable @typescript-eslint/no-explicit-any */
import { Box } from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { useMap } from "react-map-gl/maplibre";

import { useDatasetCollectionItems } from "@/lib/api/layers";
import type { TemporaryFilter } from "@/lib/store/map/slice";
import { addTemporaryFilter, removeTemporaryFilter, updateTemporaryFilter } from "@/lib/store/map/slice";
import { zoomToFeatureCollection } from "@/lib/utils/map/navigate";
import { type ProjectLayer } from "@/lib/validations/project";
import { type FilterDataSchema, filterLayoutTypes } from "@/lib/validations/widget";

import { useAppDispatch, useAppSelector } from "@/hooks/store/ContextHooks";

import { WidgetStatusContainer } from "@/components/builder/widgets/common/WidgetStatusContainer";
import CheckboxFilter from "@/components/builder/widgets/data/CheckboxFilter";
import ChipsFilter from "@/components/builder/widgets/data/ChipsFilter";
import RangeFilter from "@/components/builder/widgets/data/RangeFilter";
import SelectorLayerValue from "@/components/map/panels/common/SelectorLayerValue";

// Deep compare helper
const areFiltersEqual = (a: TemporaryFilter | undefined, b: TemporaryFilter) => {
  if (!a) return false;
  const cleanA = { ...a, id: undefined }; // ignore ID
  const cleanB = { ...b, id: undefined };
  return JSON.stringify(cleanA) === JSON.stringify(cleanB);
};

interface FilterDataProps {
  id: string;
  config: FilterDataSchema;
  projectLayers: ProjectLayer[];
  viewOnly?: boolean;
}

export const FilterDataWidget = ({ id, config: rawConfig, projectLayers }: FilterDataProps) => {
  const dispatch = useAppDispatch();
  const { map } = useMap();
  const isRangeLayout = rawConfig?.setup?.layout === filterLayoutTypes.Values.range;

  // Local dropdown state (for select, chips, checkbox)
  const [selectedValues, setSelectedValues] = useState<string[] | string | undefined>(
    rawConfig?.setup?.multiple ? [] : ""
  );

  // Local range state (for range filter)
  const [selectedRange, setSelectedRange] = useState<[number, number] | null>(null);

  const existingFilter = useAppSelector((state) =>
    state.map.temporaryFilters.find((filter) => filter.id === id)
  );

  const layer = useMemo(() => {
    return projectLayers?.find((l) => l.id === rawConfig?.setup?.layer_project_id) ?? null;
  }, [projectLayers, rawConfig?.setup?.layer_project_id]);

  /**
   * Sync local state with config changes.
   * If user changes column/layer in the config panel, wipe local state + related filter.
   */
  useEffect(() => {
    setSelectedValues(rawConfig?.setup?.multiple ? [] : "");
    setSelectedRange(null);
    if (existingFilter) {
      dispatch(removeTemporaryFilter(id));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rawConfig?.setup?.column_name, rawConfig?.setup?.layer_project_id]);

  /**
   * Sync local state when filter is removed externally
   * (e.g. FilterConfigPanel removes it).
   */
  useEffect(() => {
    if (!existingFilter) {
      setSelectedValues(rawConfig?.setup?.multiple ? [] : "");
      setSelectedRange(null);
    }
  }, [existingFilter, rawConfig?.setup?.multiple]);

  // Fetch geometry data for zoom functionality
  const geometryDataQueryParams = useMemo(() => {
    const values = Array.isArray(selectedValues) ? selectedValues : [selectedValues];
    if (
      !selectedValues?.length ||
      !rawConfig?.setup?.column_name ||
      !layer ||
      !rawConfig?.options?.zoom_to_selection
    )
      return undefined;

    return {
      limit: 50,
      offset: 0,
      filter: JSON.stringify({
        op: "or",
        args: values.map((value) => ({
          op: "=",
          args: [{ property: rawConfig.setup.column_name }, value],
        })),
      }),
    };
  }, [selectedValues, rawConfig, layer]);

  const { data: geometryData } = useDatasetCollectionItems(layer?.layer_id || "", geometryDataQueryParams);

  /**
   * Build additional targets for multi-layer filtering
   */
  const buildAdditionalTargets = (filterValues: string[]) => {
    const targetLayers = rawConfig?.options?.target_layers;
    if (!targetLayers?.length || !filterValues.length) return undefined;

    return targetLayers
      .map((target) => {
        const targetLayer = projectLayers.find((l) => l.id === target.layer_project_id);
        if (!targetLayer) return null;

        return {
          layer_id: targetLayer.id,
          filter: {
            op: "or",
            args: filterValues.map((value) => ({
              op: "=",
              args: [{ property: target.column_name }, value],
            })),
          },
        };
      })
      .filter(Boolean) as { layer_id: number; filter: object }[];
  };

  /**
   * Build additional targets for range filter
   */
  const buildAdditionalTargetsRange = (min: number, max: number) => {
    const targetLayers = rawConfig?.options?.target_layers;
    if (!targetLayers?.length) return undefined;

    return targetLayers
      .map((target) => {
        const targetLayer = projectLayers.find((l) => l.id === target.layer_project_id);
        if (!targetLayer) return null;

        return {
          layer_id: targetLayer.id,
          filter: {
            op: "and",
            args: [
              { op: ">=", args: [{ property: target.column_name }, min] },
              { op: "<=", args: [{ property: target.column_name }, max] },
            ],
          },
        };
      })
      .filter(Boolean) as { layer_id: number; filter: object }[];
  };

  /**
   * Keep store in sync with selected values (for select, chips, checkbox)
   */
  useEffect(() => {
    // Skip for range layout - handled separately
    if (isRangeLayout) return;

    // Nothing selected or invalid config
    if (
      !selectedValues ||
      (Array.isArray(selectedValues) && selectedValues.length === 0) ||
      !layer ||
      !rawConfig?.setup?.column_name
    ) {
      if (existingFilter) dispatch(removeTemporaryFilter(id));
      return;
    }

    const normalizedValues = Array.isArray(selectedValues) ? selectedValues : [selectedValues];

    const newFilter: TemporaryFilter = {
      id,
      layer_id: layer.id,
      filter: {
        op: "or",
        args: normalizedValues.map((value) => ({
          op: "=",
          args: [{ property: rawConfig.setup.column_name }, value],
        })),
      },
      additional_targets: buildAdditionalTargets(normalizedValues),
    };

    // Zoom to selection if enabled and we have geometry data
    if (geometryData?.features?.length && rawConfig?.options?.zoom_to_selection && map) {
      zoomToFeatureCollection(map, geometryData as GeoJSON.FeatureCollection, {
        duration: 200,
      });
    }

    // Compare and update store only if different
    if (!areFiltersEqual(existingFilter, newFilter)) {
      if (existingFilter) {
        dispatch(updateTemporaryFilter(newFilter));
      } else {
        dispatch(addTemporaryFilter(newFilter));
      }
    }
  }, [
    dispatch,
    existingFilter,
    geometryData,
    id,
    isRangeLayout,
    layer,
    map,
    rawConfig?.options?.target_layers,
    rawConfig?.options?.zoom_to_selection,
    rawConfig.setup.column_name,
    selectedValues,
    projectLayers,
  ]);

  /**
   * Keep store in sync with selected range (for range filter)
   */
  useEffect(() => {
    // Skip for non-range layouts
    if (!isRangeLayout) return;

    // No range selected or invalid config
    if (!selectedRange || !layer || !rawConfig?.setup?.column_name) {
      if (existingFilter) dispatch(removeTemporaryFilter(id));
      return;
    }

    const [min, max] = selectedRange;

    const newFilter: TemporaryFilter = {
      id,
      layer_id: layer.id,
      filter: {
        op: "and",
        args: [
          {
            op: ">=",
            args: [{ property: rawConfig.setup.column_name }, min],
          },
          {
            op: "<=",
            args: [{ property: rawConfig.setup.column_name }, max],
          },
        ],
      },
      additional_targets: buildAdditionalTargetsRange(min, max),
    };

    // Compare and update store only if different
    if (!areFiltersEqual(existingFilter, newFilter)) {
      if (existingFilter) {
        dispatch(updateTemporaryFilter(newFilter));
      } else {
        dispatch(addTemporaryFilter(newFilter));
      }
    }
  }, [
    dispatch,
    existingFilter,
    id,
    isRangeLayout,
    layer,
    rawConfig?.setup?.column_name,
    rawConfig?.options?.target_layers,
    selectedRange,
    projectLayers,
  ]);

  return (
    <Box sx={{ mb: 2 }}>
      <WidgetStatusContainer isNotConfigured={!layer || !rawConfig?.setup?.column_name} height={100} />
      {layer &&
        rawConfig?.setup.column_name &&
        rawConfig?.setup.layout === filterLayoutTypes.Values.select && (
          <SelectorLayerValue
            clearable
            selectedValues={selectedValues as any}
            onSelectedValuesChange={(values: string[] | string | null) => {
              if (values === null || (Array.isArray(values) && values.length === 0)) {
                setSelectedValues(rawConfig?.setup.multiple ? [] : "");
                return;
              }
              setSelectedValues(values as any);
            }}
            layerId={layer.layer_id}
            fieldName={rawConfig?.setup.column_name}
            placeholder={rawConfig?.setup.placeholder}
            multiple={rawConfig?.setup.multiple}
            cqlFilter={layer.query?.cql}
          />
        )}
      {layer &&
        rawConfig?.setup.column_name &&
        rawConfig?.setup.layout === filterLayoutTypes.Values.chips && (
          <ChipsFilter
            layerId={layer.layer_id}
            fieldName={rawConfig?.setup.column_name}
            selectedValues={
              Array.isArray(selectedValues) ? selectedValues : selectedValues ? [selectedValues] : []
            }
            onSelectedValuesChange={(values: string[]) => {
              setSelectedValues(values);
            }}
            minVisibleOptions={rawConfig?.setup.min_visible_options}
            multiple={rawConfig?.setup.multiple}
            wrap={rawConfig?.setup.wrap}
            customOrder={rawConfig?.setup.custom_order}
            cqlFilter={layer.query?.cql}
            color={rawConfig?.setup.color}
          />
        )}
      {layer &&
        rawConfig?.setup.column_name &&
        rawConfig?.setup.layout === filterLayoutTypes.Values.checkbox && (
          <CheckboxFilter
            layerId={layer.layer_id}
            fieldName={rawConfig?.setup.column_name}
            selectedValues={
              Array.isArray(selectedValues) ? selectedValues : selectedValues ? [selectedValues] : []
            }
            onSelectedValuesChange={(values: string[]) => {
              setSelectedValues(values);
            }}
            minVisibleOptions={rawConfig?.setup.min_visible_options}
            multiple={rawConfig?.setup.multiple}
            customOrder={rawConfig?.setup.custom_order}
            cqlFilter={layer.query?.cql}
            color={rawConfig?.setup.color}
          />
        )}
      {layer &&
        rawConfig?.setup.column_name &&
        rawConfig?.setup.layout === filterLayoutTypes.Values.range && (
          <RangeFilter
            layerId={layer.layer_id}
            fieldName={rawConfig?.setup.column_name}
            selectedRange={selectedRange}
            onSelectedRangeChange={setSelectedRange}
            showHistogram={rawConfig?.setup.show_histogram}
            steps={rawConfig?.setup.steps}
            showSlider={rawConfig?.setup.show_slider}
            cqlFilter={layer.query?.cql}
            color={rawConfig?.setup.color}
          />
        )}
    </Box>
  );
};
