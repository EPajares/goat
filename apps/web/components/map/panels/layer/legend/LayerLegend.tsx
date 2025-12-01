import { Box, Stack, Typography } from "@mui/material";
import React from "react";

import { getLegendColorMap, getLegendMarkerMap } from "@/lib/utils/map/legend";

import { LayerIcon } from "./LayerIcon";

interface LayerLegendPanelProps {
  properties: Record<string, unknown>;
  geometryType: string; // "point", "line", "polygon"
}

export const LayerLegendPanel = ({ properties, geometryType }: LayerLegendPanelProps) => {
  // 1. Compute Maps
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
