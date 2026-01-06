"use client";

import { Box, Stack, Typography } from "@mui/material";
import React, { useMemo } from "react";

import type { ProjectLayer } from "@/lib/validations/project";
import type { ReportElement } from "@/lib/validations/reportLayout";

import { LayerIcon } from "@/components/map/panels/layer/legend/LayerIcon";
import { LayerLegendPanel } from "@/components/map/panels/layer/legend/LayerLegend";

/**
 * Legend element configuration interface
 */
export interface LegendElementConfig {
  /** Title configuration */
  title?: {
    text?: string;
  };
  /** Map element ID to bind to (null = show all layers) */
  mapElementId?: string | null;
  /** Layout options */
  layout?: {
    columns?: number;
    showLayerNames?: boolean;
    showBackground?: boolean;
  };
}

interface LegendElementRendererProps {
  element: ReportElement;
  projectLayers?: ProjectLayer[];
  mapElements?: ReportElement[];
  viewOnly?: boolean;
  /** Zoom level to scale content */
  zoom?: number;
}

/**
 * Get simple layer color for layers without attribute-based styling
 */
const getLayerSimpleColor = (layer: ProjectLayer): string | undefined => {
  const props = layer.properties as Record<string, unknown>;

  // For raster layers, they use their own style system
  if (layer.type === "raster") {
    return undefined;
  }

  // Check for fill color
  if (props.color) {
    if (Array.isArray(props.color)) {
      return `rgb(${(props.color as number[]).join(",")})`;
    }
    return props.color as string;
  }

  // Check for stroke color
  if (props.stroke_color) {
    if (Array.isArray(props.stroke_color)) {
      return `rgb(${(props.stroke_color as number[]).join(",")})`;
    }
    return props.stroke_color as string;
  }

  return "#666666"; // Default color
};

/**
 * Check if layer has attribute-based legend (needs expanded legend panel)
 */
const hasExpandedLegend = (layer: ProjectLayer): boolean => {
  const props = layer.properties as Record<string, unknown>;

  // Check for raster with style
  if (props.style) {
    return true;
  }

  // Check for color mapping
  if (props.color_field || props.stroke_color_field || props.marker_field) {
    return true;
  }

  return false;
};

/**
 * Get geometry type for a layer
 */
const getGeometryType = (layer: ProjectLayer): string => {
  if (layer.type === "feature") {
    return layer.feature_layer_geometry_type || "polygon";
  }
  if (layer.type === "raster") {
    return "raster";
  }
  return "polygon";
};

/**
 * Legend Element Renderer for print reports
 *
 * Displays layer legends in a configurable multi-column layout.
 * Reuses the LayerLegendPanel component for consistent legend rendering.
 */
const LegendElementRenderer: React.FC<LegendElementRendererProps> = ({
  element,
  projectLayers = [],
  mapElements = [],
  viewOnly: _viewOnly = true,
  zoom = 1,
}) => {
  // Extract legend config
  const config = element.config as LegendElementConfig;
  const titleText = config?.title?.text ?? "";
  const layoutConfig = config?.layout ?? { columns: 1, showLayerNames: true };

  // Filter layers based on map element binding
  const filteredLayers = useMemo(() => {
    // If bound to a specific map element, filter layers
    if (config?.mapElementId && mapElements.length > 0) {
      const mapElement = mapElements.find((m) => m.id === config.mapElementId);
      if (mapElement?.map_config?.layers) {
        const mapLayerIds = mapElement.map_config.layers;
        return projectLayers.filter((l) => mapLayerIds.includes(l.id));
      }
    }

    // Show all visible layers
    return projectLayers.filter((layer) => {
      const props = layer.properties as Record<string, unknown>;
      // Only show layers that are visible and have legend enabled
      const isVisible = props.visibility !== false;
      const legendShow = (props.legend as { show?: boolean })?.show !== false;
      return isVisible && legendShow;
    });
  }, [projectLayers, mapElements, config?.mapElementId]);

  // Limit columns to number of layers (no empty columns)
  const columns = Math.min(layoutConfig.columns || 1, filteredLayers.length || 1);
  const showBackground = layoutConfig.showBackground !== false;

  return (
    <Box
      sx={{
        width: `${100 / zoom}%`,
        height: `${100 / zoom}%`,
        overflow: "hidden",
        p: 1,
        boxSizing: "border-box",
        backgroundColor: showBackground ? "rgba(255, 255, 255, 0.9)" : "transparent",
        borderRadius: showBackground ? 1 : 0,
        transform: `scale(${zoom})`,
        transformOrigin: "top left",
      }}>
      {/* Title - only show if text is not empty */}
      {titleText && (
        <Typography
          variant="subtitle2"
          sx={{
            fontWeight: "bold",
            mb: 1,
          }}>
          {titleText}
        </Typography>
      )}

      {/* Legend content */}
      {filteredLayers.length === 0 ? (
        <Typography variant="caption" color="text.secondary">
          No layers to display
        </Typography>
      ) : (
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: `repeat(${columns}, 1fr)`,
            gap: 1,
            overflow: "hidden",
          }}>
          {filteredLayers.map((layer) => (
            <LayerLegendItem
              key={layer.id}
              layer={layer}
              showLayerName={layoutConfig.showLayerNames !== false}
            />
          ))}
        </Box>
      )}
    </Box>
  );
};

/**
 * Individual layer legend item
 */
interface LayerLegendItemProps {
  layer: ProjectLayer;
  showLayerName?: boolean;
}

const LayerLegendItem: React.FC<LayerLegendItemProps> = ({ layer, showLayerName = true }) => {
  const geometryType = getGeometryType(layer);
  const hasExpanded = hasExpandedLegend(layer);
  const simpleColor = getLayerSimpleColor(layer);

  return (
    <Box sx={{ minWidth: 0 }}>
      {/* Layer name with simple icon for non-expanded legends */}
      {showLayerName && (
        <Stack direction="row" alignItems="center" spacing={0.5} sx={{ mb: 0.5 }}>
          {!hasExpanded && (
            <Box sx={{ flexShrink: 0 }}>
              <LayerIcon type={geometryType} color={simpleColor} />
            </Box>
          )}
          <Typography
            variant="caption"
            sx={{
              fontWeight: 500,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}>
            {layer.name}
          </Typography>
        </Stack>
      )}

      {/* Expanded legend for attribute-based styling */}
      {hasExpanded && (
        <Box sx={{ pl: showLayerName ? 0 : 0 }}>
          <LayerLegendPanel
            properties={layer.properties as Record<string, unknown>}
            geometryType={geometryType}
          />
        </Box>
      )}
    </Box>
  );
};

export default LegendElementRenderer;
