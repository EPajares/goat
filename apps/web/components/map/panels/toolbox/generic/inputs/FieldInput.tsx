/**
 * Field Input Component
 *
 * Renders a field selector that shows fields from a related layer.
 * The related layer is determined by:
 * 1. Explicit metadata (relatedLayer) in the input schema
 * 2. Naming convention: {prefix}_field -> {prefix}_layer_id
 */
import { Box, Typography } from "@mui/material";
import { useParams } from "next/navigation";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import type { LayerFieldType } from "@/lib/validations/layer";

import type { ProcessedInput } from "@/types/map/ogc-processes";

import useLayerFields from "@/hooks/map/CommonHooks";
import { useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";

import LayerFieldSelector from "@/components/map/common/LayerFieldSelector";

interface FieldInputProps {
  input: ProcessedInput;
  value: unknown;
  onChange: (value: unknown) => void;
  disabled?: boolean;
  /** All current form values - needed to get the related layer's value */
  formValues: Record<string, unknown>;
  /** Map of layer input names to their dataset IDs (computed by parent) */
  layerDatasetIds?: Record<string, string>;
}

/**
 * Infer the related layer input name from a field input name
 * E.g., "target_field" -> "target_layer_id"
 *       "join_field" -> "join_layer_id"
 *       "source_field" -> "source_layer_id"
 */
function inferRelatedLayerInput(fieldInputName: string): string | null {
  // Check for explicit patterns
  const patterns = [
    { match: /^(.+)_field$/, replacement: "$1_layer_id" },
    { match: /^(.+)Field$/, replacement: "$1LayerId" },
    { match: /^field_(.+)$/, replacement: "layer_id_$1" },
  ];

  for (const pattern of patterns) {
    if (pattern.match.test(fieldInputName)) {
      return fieldInputName.replace(pattern.match, pattern.replacement);
    }
  }

  return null;
}

export default function FieldInput({
  input,
  value,
  onChange,
  disabled,
  formValues,
  layerDatasetIds = {},
}: FieldInputProps) {
  const { t } = useTranslation("common");
  const { projectId } = useParams();

  // Determine which layer this field relates to
  const relatedLayerInputName = useMemo(() => {
    // 1. Check metadata for explicit relationship
    const relatedLayerMeta = input.metadata?.find(
      (m) => m.role === "relatedLayer" || m.title === "relatedLayer"
    );
    if (relatedLayerMeta?.value) {
      return relatedLayerMeta.value as string;
    }

    // 2. Fall back to naming convention
    return inferRelatedLayerInput(input.name);
  }, [input.name, input.metadata]);

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
    // First check if parent provided it
    if (relatedLayerInputName && layerDatasetIds[relatedLayerInputName]) {
      return layerDatasetIds[relatedLayerInputName];
    }

    // Otherwise try to find it from project layers
    if (!selectedLayerId || !projectLayers) return "";

    // The selectedLayerId from OGC/form could be:
    // - A project layer id (number as string)
    // - A layer_id (string UUID which is the dataset_id)
    const layer = projectLayers.find(
      (l) => l.id === Number(selectedLayerId) || l.layer_id === selectedLayerId
    );
    // layer_id IS the dataset_id in the project layer schema
    return layer?.layer_id || "";
  }, [selectedLayerId, projectLayers, relatedLayerInputName, layerDatasetIds]);

  // Fetch fields for the layer
  const { layerFields, isLoading } = useLayerFields(datasetId);

  // Convert value to LayerFieldType format
  const selectedField = useMemo((): LayerFieldType | undefined => {
    if (!value) return undefined;

    // Value might be just the field name (string) or a full object
    if (typeof value === "string") {
      return layerFields.find((f) => f.name === value);
    }

    // If it's already an object with name/type
    if (typeof value === "object" && value !== null && "name" in value) {
      return value as LayerFieldType;
    }

    return undefined;
  }, [value, layerFields]);

  const handleChange = (field: LayerFieldType | undefined) => {
    // Store just the field name for the API
    onChange(field?.name ?? null);
  };

  // Show message if no layer is selected
  if (!selectedLayerId) {
    return (
      <Box>
        <Typography variant="body2" color="text.secondary" sx={{ fontStyle: "italic" }}>
          {input.title || input.name}: {t("select_layer_first")}
        </Typography>
      </Box>
    );
  }

  // Show loading state
  if (isLoading) {
    return (
      <Box>
        <Typography variant="body2" color="text.secondary">
          {t("loading_fields")}...
        </Typography>
      </Box>
    );
  }

  // Show message if no fields available
  if (layerFields.length === 0) {
    return (
      <Box>
        <Typography variant="body2" color="text.secondary">
          {input.title || input.name}: {t("no_fields_available")}
        </Typography>
      </Box>
    );
  }

  return (
    <LayerFieldSelector
      selectedField={selectedField}
      setSelectedField={handleChange}
      fields={layerFields}
      label={input.title || input.name}
      tooltip={input.description}
      disabled={disabled}
    />
  );
}
