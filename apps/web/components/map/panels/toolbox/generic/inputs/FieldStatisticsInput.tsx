/**
 * Field Statistics Input Component
 *
 * Renders a field statistics selector that combines:
 * 1. An operation dropdown (count, sum, min, max, mean, standard_deviation)
 * 2. A field selector (when operation is not 'count')
 *
 * The related layer is determined by widget_options.source_layer.
 */
import { Box, FormControl, InputLabel, MenuItem, Select, Typography } from "@mui/material";
import { useParams } from "next/navigation";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import type { LayerFieldType } from "@/lib/validations/layer";

import type { ProcessedInput } from "@/types/map/ogc-processes";

import useLayerFields from "@/hooks/map/CommonHooks";
import { useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";

import LayerFieldSelector from "@/components/map/common/LayerFieldSelector";

// Define the statistic operations supported by the backend
const STATISTIC_OPERATIONS = [
  { value: "count", labelKey: "count" },
  { value: "sum", labelKey: "sum" },
  { value: "min", labelKey: "min" },
  { value: "max", labelKey: "max" },
  { value: "mean", labelKey: "mean" },
  { value: "standard_deviation", labelKey: "standard_deviation" },
] as const;

interface FieldStatisticsValue {
  operation: string;
  field?: string | null;
}

interface FieldStatisticsInputProps {
  input: ProcessedInput;
  value: unknown;
  onChange: (value: unknown) => void;
  disabled?: boolean;
  /** All current form values - needed to get the related layer's value */
  formValues: Record<string, unknown>;
}

export default function FieldStatisticsInput({
  input,
  value,
  onChange,
  disabled,
  formValues,
}: FieldStatisticsInputProps) {
  const { t } = useTranslation("common");
  const { projectId } = useParams();

  // Parse the current value
  const currentValue = useMemo((): FieldStatisticsValue => {
    if (typeof value === "object" && value !== null) {
      const v = value as FieldStatisticsValue;
      return {
        operation: v.operation || "",
        field: v.field ?? null,
      };
    }
    return { operation: "", field: null };
  }, [value]);

  // Determine which layer this field relates to from widget_options.source_layer
  const relatedLayerInputName = useMemo(() => {
    const sourceLayer = input.uiMeta?.widget_options?.source_layer;
    return typeof sourceLayer === "string" ? sourceLayer : null;
  }, [input.uiMeta]);

  // Get the selected layer ID from form values
  const selectedLayerId = useMemo(() => {
    if (!relatedLayerInputName) return null;
    const layerId = formValues[relatedLayerInputName];
    return typeof layerId === "string" ? layerId : null;
  }, [relatedLayerInputName, formValues]);

  // Get project layers to find the dataset ID
  const { layers: projectLayers } = useFilteredProjectLayers(projectId as string);

  // Find the dataset ID for the selected layer
  const datasetId = useMemo(() => {
    if (!selectedLayerId || !projectLayers) return "";

    const layer = projectLayers.find(
      (l) => l.id === Number(selectedLayerId) || l.layer_id === selectedLayerId
    );
    return layer?.layer_id || "";
  }, [selectedLayerId, projectLayers]);

  // Fetch only numeric fields for the layer (statistics require numeric columns)
  const { layerFields, isLoading } = useLayerFields(datasetId, "number");

  // Cast to LayerFieldType[] - the hook normalizes types to "string" | "number" | "object"
  const numericFields = layerFields as LayerFieldType[];

  // Check if the current operation requires a field
  const requiresField = currentValue.operation && currentValue.operation !== "count";

  // Convert the selected field name to LayerFieldType format
  const selectedField = useMemo((): LayerFieldType | undefined => {
    if (!currentValue.field || !requiresField) return undefined;
    return numericFields.find((f) => f.name === currentValue.field);
  }, [currentValue.field, numericFields, requiresField]);

  const handleOperationChange = (operation: string) => {
    if (operation === "count") {
      // Count operation doesn't need a field
      onChange({ operation, field: null });
    } else {
      // Preserve field if it was already selected, otherwise set to null
      onChange({ operation, field: currentValue.field || null });
    }
  };

  const handleFieldChange = (field: LayerFieldType | undefined) => {
    onChange({
      operation: currentValue.operation,
      field: field?.name ?? null,
    });
  };

  // Get label from uiMeta or fallback to title
  const label = input.uiMeta?.label || input.title || input.name;

  // Show message if no layer is selected
  if (!selectedLayerId) {
    return (
      <Box>
        <Typography variant="body2" color="text.secondary" sx={{ fontStyle: "italic" }}>
          {label}: {t("select_layer_first")}
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {/* Operation Selector */}
      <FormControl size="small" fullWidth disabled={disabled}>
        <InputLabel id={`${input.name}-operation-label`}>{t("select_operation")}</InputLabel>
        <Select
          labelId={`${input.name}-operation-label`}
          value={currentValue.operation}
          onChange={(e) => handleOperationChange(e.target.value)}
          label={t("select_operation")}>
          {STATISTIC_OPERATIONS.map((op) => (
            <MenuItem key={op.value} value={op.value}>
              {t(op.labelKey)}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Field Selector (hidden for count operation) */}
      {requiresField && (
        <LayerFieldSelector
          selectedField={selectedField}
          setSelectedField={handleFieldChange}
          fields={numericFields}
          label={t("select_field")}
          tooltip={t("select_numeric_field_for_statistics")}
          disabled={disabled || isLoading}
        />
      )}
    </Box>
  );
}
