/**
 * Generic Layer Input Component
 *
 * Renders a layer selector based on OGC process input schema.
 * Filters layers by geometry type constraints from metadata.
 */
import { useParams } from "next/navigation";
import { useMemo } from "react";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import type { SelectorItem } from "@/types/map/common";
import type { ProcessedInput } from "@/types/map/ogc-processes";

import { useFilteredProjectLayers } from "@/hooks/map/LayerPanelHooks";

import Selector from "@/components/map/panels/common/Selector";

interface LayerInputProps {
  input: ProcessedInput;
  value: string | undefined;
  onChange: (value: string | undefined) => void;
  disabled?: boolean;
  /** Layer IDs to exclude from the selector (e.g., already selected in other items) */
  excludedLayerIds?: string[];
}

/**
 * Map geometry constraint names to layer types
 */
function mapGeometryToLayerType(geometry: string): string {
  const normalized = geometry.toLowerCase();
  if (normalized.includes("polygon")) return "polygon";
  if (normalized.includes("line") || normalized.includes("linestring")) return "line";
  if (normalized.includes("point")) return "point";
  return normalized;
}

export default function LayerInput({
  input,
  value,
  onChange,
  disabled,
  excludedLayerIds = [],
}: LayerInputProps) {
  const { projectId } = useParams();
  const { layers: projectLayers } = useFilteredProjectLayers(projectId as string);

  // Filter layers based on geometry constraints and exclusions
  const filteredLayers = useMemo(() => {
    if (!projectLayers) return [];

    let filtered = projectLayers;

    // Apply geometry constraints if present
    if (input.geometryConstraints && input.geometryConstraints.length > 0) {
      const allowedTypes = input.geometryConstraints.map(mapGeometryToLayerType);

      filtered = filtered.filter((layer) => {
        const layerGeomType = layer.feature_layer_geometry_type?.toLowerCase();
        if (!layerGeomType) return true; // Allow if no geometry type (tables, etc.)

        return allowedTypes.some((allowed) => layerGeomType.includes(allowed));
      });
    }

    // Exclude already-selected layers (for repeatable objects)
    if (excludedLayerIds.length > 0) {
      filtered = filtered.filter((layer) => !excludedLayerIds.includes(layer.layer_id));
    }

    return filtered;
  }, [projectLayers, input.geometryConstraints, excludedLayerIds]);

  // Convert layers to selector items
  const layerItems: SelectorItem[] = useMemo(() => {
    return filteredLayers.map((layer) => ({
      value: layer.layer_id,
      label: layer.name,
    }));
  }, [filteredLayers]);

  // Find selected item
  const selectedItem = useMemo(() => {
    if (!value) return undefined;
    return layerItems.find((item) => item.value === value);
  }, [value, layerItems]);

  const handleChange = (item: SelectorItem | SelectorItem[] | undefined) => {
    if (Array.isArray(item)) {
      onChange(item[0]?.value as string | undefined);
    } else {
      onChange(item?.value as string | undefined);
    }
  };

  // Build tooltip with geometry constraints info
  const tooltip = useMemo(() => {
    let tip = input.description || "";
    if (input.geometryConstraints && input.geometryConstraints.length > 0) {
      tip += tip ? "\n\n" : "";
      tip += `Accepted geometry types: ${input.geometryConstraints.join(", ")}`;
    }
    return tip;
  }, [input.description, input.geometryConstraints]);

  return (
    <Selector
      selectedItems={selectedItem}
      setSelectedItems={handleChange}
      items={layerItems}
      label={input.title}
      tooltip={tooltip}
      placeholder={`Select ${input.title.toLowerCase()}`}
      emptyMessage="No matching layers found"
      emptyMessageIcon={ICON_NAME.LAYERS}
      disabled={disabled}
    />
  );
}
