import ImageIcon from "@mui/icons-material/Image";
import { Box } from "@mui/material";
import React from "react";

import type { Layer } from "@/lib/validations/layer";
import type { ProjectLayer } from "@/lib/validations/project";
import { rgbToHex } from "@/lib/utils/helpers";
import { getLegendColorMap, resolveFeatureMarker } from "@/lib/utils/map/legend";

import { MaskedImageIcon } from "@/components/map/panels/style/other/MaskedImageIcon";

interface LayerIconProps {
  type: "point" | "line" | "polygon" | "raster" | string;
  color?: string;
  strokeColor?: string;
  filled?: boolean;
  iconUrl?: string; // For custom markers or raster thumbnails
  iconSource?: "custom" | "library"; // To determine if we should apply mask
}

export const LayerIcon = ({
  type,
  color,
  strokeColor,
  filled = true,
  iconUrl,
  iconSource = "library",
}: LayerIconProps) => {
  if (type === "raster") {
    return <ImageIcon fontSize="small" sx={{ color: "#888" }} />;
  }

  // Custom Marker Image
  if (type === "point" && iconUrl) {
    // For library icons (SDF), apply mask with color
    // For custom icons (external URLs), render directly without color
    const shouldApplyMask = iconSource === "library" && !!color;

    return (
      <Box sx={{ width: 20, height: 20, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <MaskedImageIcon imageUrl={iconUrl} dimension="16px" applyMask={shouldApplyMask} imgColor={color} />
      </Box>
    );
  }

  // SVG Geometry Icons
  return (
    <svg height="20" width="20" style={{ display: "block" }}>
      {type === "point" && (
        <circle
          cx="10"
          cy="10"
          r="6"
          fill={filled ? color : "none"}
          stroke={strokeColor || color} // Default stroke to fill if missing
          strokeWidth={strokeColor || !filled ? 2 : 0}
          fillOpacity={filled ? 1 : 0}
        />
      )}
      {type === "line" && (
        // line with round caps centered
        <line
          x1="4"
          y1="14"
          x2="16"
          y2="6"
          stroke={strokeColor || color}
          strokeWidth="3"
          strokeLinecap="round"
        />
      )}
      {type === "polygon" && (
        <rect
          x="4"
          y="4"
          width="12"
          height="12"
          rx="2"
          fill={filled ? color : "none"}
          stroke={strokeColor || (!filled ? color : "none")}
          strokeWidth={strokeColor || !filled ? 2 : 0}
          fillOpacity={filled ? 1 : 0}
        />
      )}
    </svg>
  );
};

/**
 * Multi-color swatch for layers with attribute-based legends (e.g.
 * `color_field`, `stroke_color_field`). Renders the legend's color stops
 * as vertical bands inside a small rounded square — a compact preview
 * of what the full LayerLegendPanel shows in the Layers panel.
 */
function LegendSwatch({ colors }: { colors: string[] }) {
  const safe = colors.length > 0 ? colors : ["#ccc"];
  return (
    <Box
      sx={{
        display: "flex",
        width: 18,
        height: 18,
        borderRadius: 0.5,
        overflow: "hidden",
        boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)",
      }}>
      {safe.map((c, i) => (
        <Box key={i} sx={{ flex: 1, bgcolor: c }} />
      ))}
    </Box>
  );
}

/**
 * Build a small icon representing a layer's style — the same affordance
 * the Layers panel renders next to each layer name. Mirrors the branching
 * logic in `ProjectLayerTree`:
 *
 *   1. Tables → a table glyph (skipped here; popups don't open on tables)
 *   2. Raster → image icon
 *   3. Custom marker → the marker glyph; with `featureProperties` given,
 *      the marker the feature actually renders with (marker_mapping)
 *   4. Complex legend (color_field / stroke_color_field / marker_field)
 *      → multi-color swatch built from `getLegendColorMap` so the user
 *      sees that the layer is attribute-styled, not a single color
 *   5. Simple feature → `<LayerIcon>` with the base color/stroke (point
 *      dot, line, or polygon rect)
 *
 * Returns `undefined` only when the layer is missing or has no
 * recognizable geometry type, so callers can fall back to a generic icon.
 */
export function buildLayerIcon(
  layer: ProjectLayer | Layer | undefined,
  featureProperties?: Record<string, unknown>,
): React.ReactNode | undefined {
  if (!layer) return undefined;

  const layerType = (layer as { layer_type?: string }).layer_type;
  if (layerType === "raster") return <LayerIcon type="raster" />;

  const geomType = (
    layer as { feature_layer_geometry_type?: string }
  ).feature_layer_geometry_type;
  if (!geomType) return undefined;

  const props = (layer.properties as Record<string, unknown>) ?? {};

  const colorToHex = (c: unknown): string | undefined => {
    if (Array.isArray(c) && c.length >= 3 && typeof c[0] === "number") {
      return rgbToHex(c as [number, number, number]);
    }
    if (typeof c === "string") return c;
    return undefined;
  };

  const baseColor = colorToHex(props.color) ?? "#ccc";
  const strokeColor = colorToHex(props.stroke_color);
  const filled = props.filled !== false;
  const stroked = props.stroked !== false;
  const customMarker = Boolean(props.custom_marker);

  // Custom marker: the marker IS the visible affordance on the map, so it
  // takes precedence over any color-based legend swatch. For marker_field
  // layers, resolveFeatureMarker picks the clicked feature's mapped icon
  // (base marker when there is no match or no feature) — the same
  // precedence the icon-image match expression uses on the map.
  const resolvedMarker = customMarker ? resolveFeatureMarker(props, featureProperties) : undefined;
  if (resolvedMarker) {
    const iconColor = !filled ? "#000000" : baseColor;
    return (
      <LayerIcon
        type={geomType.toLowerCase()}
        color={iconColor}
        filled={filled}
        iconUrl={resolvedMarker.url}
        iconSource={resolvedMarker.source}
      />
    );
  }

  // Attribute-based styling: pull the legend color stops and render them
  // as a multi-color swatch. Mirrors what the Layers panel does at
  // ProjectLayerTree.tsx around L1071-L1085 (LegendPanel for the full
  // breakdown; we just need a compact preview).
  const hasComplexLegend = Boolean(
    props.color_field || props.stroke_color_field || props.marker_field,
  );
  if (hasComplexLegend) {
    const fillStops = getLegendColorMap(props, "color").map((s) => s.color);
    const strokeStops = getLegendColorMap(props, "stroke_color").map((s) => s.color);
    const stops = (fillStops.length > 1 ? fillStops : strokeStops).filter(Boolean);
    if (stops.length > 1) return <LegendSwatch colors={stops} />;
    // marker_field with no color stops: fall through to the simple-
    // feature preview below.
  }

  const iconColor = !filled && customMarker ? "#000000" : baseColor;

  return (
    <LayerIcon
      type={geomType.toLowerCase()}
      color={iconColor}
      strokeColor={stroked ? strokeColor : undefined}
      filled={filled}
    />
  );
}
