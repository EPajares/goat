import { Box, Stack, Typography } from "@mui/material";
import React from "react";

import { getLegendColorMap, getLegendMarkerMap } from "@/lib/utils/map/legend";
import type { RasterLayerProperties } from "@/lib/validations/layer";

import { LayerIcon } from "./LayerIcon";

interface LayerLegendPanelProps {
  properties: Record<string, unknown>;
  geometryType: string; // "point", "line", "polygon"
}

export const LayerLegendPanel = ({ properties, geometryType }: LayerLegendPanelProps) => {
  // Check if this is a raster layer with styling
  const rasterProperties = properties as RasterLayerProperties;
  const rasterStyle = rasterProperties?.style;

  // 1. Raster Layer Legends
  if (rasterStyle) {
    return <RasterLayerLegend style={rasterStyle} />;
  }

  // 2. Feature Layer Legends
  // Compute Maps
  const colorMap = getLegendColorMap(properties, "color");
  const strokeMap = getLegendColorMap(properties, "stroke_color");
  const markerMap = getLegendMarkerMap(properties);

  // 2. Helper to render a single legend row
  const renderRow = (label: string, iconNode: React.ReactNode) => (
    <Stack direction="row" alignItems="center" spacing={1} sx={{ py: 0.5 }} key={label}>
      <Box sx={{ width: 20, display: "flex", justifyContent: "center" }}>{iconNode}</Box>
      <Typography variant="caption" sx={{ lineHeight: 1.2 }}>
        {label}
      </Typography>
    </Stack>
  );

  // --- RENDER LOGIC ---

  // A. Attribute-based Colors (Fill)
  if (colorMap.length > 1) {
    return (
      <Box sx={{ pb: 1 }}>
        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
          {(properties.color_field as { name?: string })?.name || "Legend"}
        </Typography>
        {colorMap.map((item) =>
          renderRow(item.value?.join(", ") || "Other", <LayerIcon type={geometryType} color={item.color} />)
        )}
      </Box>
    );
  }

  // B. Attribute-based Stroke (Line or Outline)
  if (strokeMap.length > 1) {
    return (
      <Box sx={{ pb: 1 }}>
        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
          {(properties.stroke_color_field as { name?: string })?.name || "Legend"}
        </Typography>
        {strokeMap.map((item) =>
          renderRow(
            item.value?.join(", ") || "Other",
            <LayerIcon type={geometryType} color={undefined} strokeColor={item.color} filled={false} />
          )
        )}
      </Box>
    );
  }

  // C. Custom Markers (Points)
  if (markerMap.length > 1 && geometryType === "point") {
    return (
      <Box sx={{ pb: 1 }}>
        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
          {(properties.marker_field as { name?: string })?.name || "Legend"}
        </Typography>
        {markerMap.map((item) =>
          renderRow(item.value?.join(", ") || "Other", <LayerIcon type="point" iconUrl={item.marker || ""} />)
        )}
      </Box>
    );
  }

  // If no expanded legend is needed (Simple single-color layer),
  // usually we don't render anything here because the main Row Icon handles it.
  return null;
};

// Raster Layer Legend Component
interface RasterLayerLegendProps {
  style: RasterLayerProperties["style"];
}

const RasterLayerLegend = ({ style }: RasterLayerLegendProps) => {
  if (!style) return null;

  // Helper to render a single legend row
  const renderRow = (label: string, color: string) => (
    <Stack direction="row" alignItems="center" spacing={1} sx={{ py: 0.5 }} key={label}>
      <Box
        sx={{
          width: 20,
          height: 12,
          backgroundColor: color,
          border: "1px solid",
          borderColor: "divider",
          borderRadius: 0.5,
        }}
      />
      <Typography variant="caption" sx={{ lineHeight: 1.2 }}>
        {label}
      </Typography>
    </Stack>
  );

  // 1. Categories Style
  if (style.style_type === "categories") {
    return (
      <Box sx={{ pb: 1 }}>
        {style.categories.map((cat) => renderRow(cat.label || `Value ${cat.value}`, cat.color))}
      </Box>
    );
  }

  // 2. Color Range Style
  if (style.style_type === "color_range" && style.color_map.length > 0) {
    const minLabel =
      style.min_label || style.min_value?.toString() || style.color_map[0]?.[0]?.toString() || "Min";
    const maxLabel =
      style.max_label ||
      style.max_value?.toString() ||
      style.color_map[style.color_map.length - 1]?.[0]?.toString() ||
      "Max";

    return (
      <Box sx={{ pb: 1 }}>
        <Box
          sx={{
            width: "100%",
            height: 16,
            background: `linear-gradient(to right, ${style.color_map.map(([, color]) => color).join(", ")})`,
            border: "1px solid",
            borderColor: "divider",
            borderRadius: 0.5,
            mb: 0.5,
          }}
        />
        <Stack direction="row" justifyContent="space-between">
          <Typography variant="caption" color="text.secondary">
            {minLabel}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {maxLabel}
          </Typography>
        </Stack>
      </Box>
    );
  }

  // 3. Image/Hillshade Styles - No legend needed
  return null;
};
