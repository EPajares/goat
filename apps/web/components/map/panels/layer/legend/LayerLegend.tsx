import { Box, Stack, Typography } from "@mui/material";
import React from "react";
import { useTranslation } from "react-i18next";

import { getLegendColorMap, getLegendMarkerMap } from "@/lib/utils/map/legend";
import type { RasterLayerProperties } from "@/lib/validations/layer";

import { LayerIcon } from "./LayerIcon";

interface LayerLegendPanelProps {
  properties: Record<string, unknown>;
  geometryType: string; // "point", "line", "polygon"
}

export const LayerLegendPanel = ({ properties, geometryType }: LayerLegendPanelProps) => {
  const { t } = useTranslation("common");

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
    <Stack direction="row" alignItems="center" spacing={1} sx={{ py: 0.5 }}>
      <Box sx={{ width: 20, display: "flex", justifyContent: "center" }}>{iconNode}</Box>
      <Typography variant="caption" sx={{ lineHeight: 1.2 }}>
        {label}
      </Typography>
    </Stack>
  );

  // --- RENDER LOGIC ---
  // Priority: Check if markers and colors represent the same attribute
  // If they do, show only the colored markers
  // If they don't, show both sections separately

  const markerFieldName = (properties.marker_field as { name?: string })?.name;
  const colorFieldName = (properties.color_field as { name?: string })?.name;
  const hasMatchingFields = markerFieldName && colorFieldName && markerFieldName === colorFieldName;

  // A. Custom Markers with matching color field - show colored markers only
  if (markerMap.length > 1 && geometryType === "point" && hasMatchingFields) {
    return (
      <Box sx={{ pb: 1, pr: 2, pt: 0.5 }}>
        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
          {markerFieldName || "Legend"}
        </Typography>
        {markerMap.map((item, index) => (
          <React.Fragment key={`${item.marker}-${item.value?.join(",") || index}`}>
            {renderRow(
              item.value?.join(", ") || "Other",
              <LayerIcon
                type="point"
                iconUrl={item.marker || ""}
                color={item.color || undefined}
                iconSource={item.source}
              />
            )}
          </React.Fragment>
        ))}
      </Box>
    );
  }

  // B. Custom Markers WITHOUT matching color field - show both sections
  if (markerMap.length > 1 && geometryType === "point" && !hasMatchingFields) {
    return (
      <Box sx={{ pb: 1, pr: 2, pt: 0.5 }}>
        {/* Icons section */}
        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
          {markerFieldName ? t("icons_based_on", { field: markerFieldName }) : t("icons")}
        </Typography>
        {markerMap.map((item, index) => (
          <React.Fragment key={`${item.marker}-${item.value?.join(",") || index}`}>
            {renderRow(
              item.value?.join(", ") || "Other",
              <LayerIcon
                type="point"
                iconUrl={item.marker || ""}
                color={item.color || undefined}
                iconSource={item.source}
              />
            )}
          </React.Fragment>
        ))}

        {/* Fill color section if it exists */}
        {colorMap.length > 1 && (
          <>
            <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 2, mb: 0.5 }}>
              {t("fill_color_based_on", { field: colorFieldName || t("color") })}
            </Typography>
            {colorMap.map((item, index) => (
              <React.Fragment key={`${item.color}-${item.value?.join(",") || index}`}>
                {renderRow(item.value?.join(", ") || "Other", <LayerIcon type="point" color={item.color} />)}
              </React.Fragment>
            ))}
          </>
        )}
      </Box>
    );
  }

  // C. Single marker with attribute-based colors - show icon in each color
  if (markerMap.length === 1 && geometryType === "point" && colorMap.length > 1) {
    const singleMarker = markerMap[0];
    return (
      <Box sx={{ pb: 1, pr: 2, pt: 0.5 }}>
        {/* Show the icon in each color instead of circles */}
        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
          {colorFieldName || "Legend"}
        </Typography>
        {colorMap.map((item, index) => (
          <React.Fragment key={`${item.color}-${item.value?.join(",") || index}`}>
            {renderRow(
              item.value?.join(", ") || "Other",
              <LayerIcon
                type="point"
                iconUrl={singleMarker.marker || ""}
                color={item.color}
                iconSource={singleMarker.source}
              />
            )}
          </React.Fragment>
        ))}
      </Box>
    );
  }

  // D. Attribute-based Colors (Fill) with or without stroke
  if (colorMap.length > 1) {
    // Check if stroke color is also attribute-based on a different field
    const strokeColorFieldName = (properties.stroke_color_field as { name?: string })?.name;
    const hasDifferentStrokeField = strokeColorFieldName && strokeColorFieldName !== colorFieldName;

    // Get stroke properties for proper rendering
    const stroked = properties.stroked !== false; // Default to true if not specified
    const strokeColor = properties.stroke_color
      ? Array.isArray(properties.stroke_color)
        ? `rgb(${(properties.stroke_color as number[]).join(",")})`
        : (properties.stroke_color as string)
      : undefined;
    const filled = properties.filled !== false; // Default to true if not specified

    // If both fill and stroke are attribute-based on different fields, show both sections
    if (hasDifferentStrokeField && strokeMap.length > 1) {
      return (
        <Box sx={{ pb: 1, pr: 2, pt: 0.5 }}>
          {/* Fill color section */}
          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
            {t("fill_color_based_on", { field: colorFieldName || t("color") })}
          </Typography>
          {colorMap.map((item, index) => (
            <React.Fragment key={`fill-${item.color}-${item.value?.join(",") || index}`}>
              {renderRow(
                item.value?.join(", ") || "Other",
                <LayerIcon type={geometryType} color={item.color} filled={filled} />
              )}
            </React.Fragment>
          ))}

          {/* Stroke color section */}
          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 2, mb: 0.5 }}>
            {t("stroke_color_based_on", { field: strokeColorFieldName })}
          </Typography>
          {strokeMap.map((item, index) => (
            <React.Fragment key={`stroke-${item.color}-${item.value?.join(",") || index}`}>
              {renderRow(
                item.value?.join(", ") || "Other",
                <LayerIcon type={geometryType} color={undefined} strokeColor={item.color} filled={false} />
              )}
            </React.Fragment>
          ))}
        </Box>
      );
    }

    // Otherwise, show fill color with static stroke (if enabled)
    return (
      <Box sx={{ pb: 1, pr: 2, pt: 0.5 }}>
        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
          {colorFieldName || "Legend"}
        </Typography>
        {colorMap.map((item, index) => (
          <React.Fragment key={`${item.color}-${item.value?.join(",") || index}`}>
            {renderRow(
              item.value?.join(", ") || "Other",
              <LayerIcon
                type={geometryType}
                color={item.color}
                strokeColor={stroked ? strokeColor : undefined}
                filled={filled}
              />
            )}
          </React.Fragment>
        ))}
      </Box>
    );
  }

  // E. Attribute-based Stroke only (no fill color field)
  if (strokeMap.length > 1) {
    return (
      <Box sx={{ pb: 1, pr: 2, pt: 0.5 }}>
        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
          {(properties.stroke_color_field as { name?: string })?.name || "Legend"}
        </Typography>
        {strokeMap.map((item, index) => (
          <React.Fragment key={`${item.color}-${item.value?.join(",") || index}`}>
            {renderRow(
              item.value?.join(", ") || "Other",
              <LayerIcon type={geometryType} color={undefined} strokeColor={item.color} filled={false} />
            )}
          </React.Fragment>
        ))}
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
    <Stack direction="row" alignItems="center" spacing={1} sx={{ py: 0.5 }}>
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
      <Box sx={{ pb: 1, pr: 2, pt: 0.5 }}>
        {style.categories.map((cat) => (
          <React.Fragment key={`${cat.value}-${cat.color}`}>
            {renderRow(cat.label || `Value ${cat.value}`, cat.color)}
          </React.Fragment>
        ))}
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
      <Box sx={{ pb: 1, pr: 2, pt: 3 }}>
        <Box
          sx={{
            width: "100%",
            height: 16,
            background: `linear-gradient(to right, ${style.color_map.map(([, color]) => color).join(", ")})`,
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
