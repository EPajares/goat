import { formatNumber, rgbToHex } from "@/lib/utils/helpers";

import type { RGBColor } from "@/types/map/color";

// Types
export type ColorMapItem = {
  value: string[] | null;
  color: string;
  label?: string;
};

export type MarkerMapItem = {
  value: string[] | null;
  marker: string | null;
  color?: string | null;
  source?: "custom" | "library" | undefined;
};

const DEFAULT_COLOR = "#000000";

const getColor = (colors: string[], index: number): string =>
  colors && colors[index] !== undefined ? colors[index] : DEFAULT_COLOR;

const createRangeAndColor = (
  colorMap: ColorMapItem[],
  rangeStart: number,
  rangeEnd: number,
  color: string,
  isFirst?: boolean,
  isLast?: boolean,
  label?: string
): void => {
  const range = `${isFirst ? "<" : ""}${formatNumber(rangeStart, 2)} - ${isLast ? ">" : ""}${formatNumber(rangeEnd, 2)}`;
  colorMap.push({ value: [range], color, ...(label ? { label } : {}) });
};

// --- MAIN PARSERS ---

export function getLegendColorMap(
  properties: Record<string, unknown> | null,
  type: "color" | "stroke_color"
): ColorMapItem[] {
  const colorMap: ColorMapItem[] = [];
  if (!properties) return colorMap;

  // Skip if the corresponding style toggle is inactive
  if (type === "color" && properties.filled === false) return colorMap;
  if (type === "stroke_color" && properties.stroked === false) return colorMap;

  // Read color_legends for custom labels
  const colorLegends = (properties[`${type}_range`] as Record<string, unknown>)?.color_legends as
    | Record<string, string>
    | undefined;

  // 1. Attribute Field Based (Complex Legend)
  if (properties?.[`${type}_field`]) {
    if (["ordinal"].includes(properties[`${type}_scale`] as string)) {
      // Ordinal (Categories)
      ((properties[`${type}_range`] as Record<string, unknown>)?.color_map as unknown[])?.forEach(
        (value: unknown, index: number) => {
          if (Array.isArray(value) && value.length === 2) {
            const color = value[1] as string;
            const values = value[0] as string[] | null;
            // Look up label by category value first, fall back to color key for backward compat
            const valueKey = values ? values.join(",") : String(index);
            const label = colorLegends?.[valueKey] || colorLegends?.[color];
            colorMap.push({
              value: values,
              color,
              ...(label ? { label } : {}),
            });
          }
        }
      );
    } else {
      // Sequential/Quantile (Ranges)
      const scaleType = properties[`${type}_scale`] as string;
      let classBreaksValues = properties[`${type}_scale_breaks`] as Record<string, unknown>;
      let colors = (properties[`${type}_range`] as Record<string, unknown>)?.colors as string[];
      // For custom_breaks, store original color_map value keys for legend label lookup
      let valueKeys: string[] | undefined;

      if (scaleType === "custom_breaks") {
        const colorMapValues = (properties[`${type}_range`] as Record<string, unknown>)?.color_map;
        // Create a new mutable object to avoid "object is not extensible" errors
        const _customClassBreaks: { breaks: number[]; min?: number; max?: number } = {
          breaks: [],
          min: (classBreaksValues as { min?: number })?.min,
          max: (classBreaksValues as { max?: number })?.max,
        };
        const _colors: string[] = [];
        valueKeys = [];

        (colorMapValues as unknown[])?.forEach((value: unknown, index: number) => {
          const valueArray = value as [unknown[], string];
          _colors.push(valueArray[1]);
          // Store the original value key (break value string) for legend label lookup
          const firstValue =
            valueArray[0] !== null && valueArray[0] !== undefined
              ? String(Array.isArray(valueArray[0]) ? valueArray[0][0] : valueArray[0])
              : String(index);
          valueKeys!.push(firstValue);
          if (index === 0) return;
          if (valueArray[0] !== null && valueArray[0] !== undefined) {
            _customClassBreaks.breaks.push(Number(firstValue));
          }
        });
        classBreaksValues = _customClassBreaks;
        colors = _colors;
      }

      if (
        classBreaksValues &&
        Array.isArray((classBreaksValues as Record<string, unknown>).breaks) &&
        colors
      ) {
        // Track running row index for legend label lookup
        // For custom_breaks: use original color_map value keys; for other scales: use row index
        let rowIdx = 0;
        const getLegendLabel = (rowIdx: number, colorFallback: string): string | undefined => {
          const key = valueKeys ? valueKeys[rowIdx] : String(rowIdx);
          return colorLegends?.[key] || colorLegends?.[colorFallback];
        };
        ((classBreaksValues as Record<string, unknown>).breaks as number[]).forEach(
          (value: number, index: number) => {
            if (index === 0) {
              const color0 = getColor(colors, index);
              createRangeAndColor(
                colorMap,
                (classBreaksValues as Record<string, unknown>).min as number,
                value,
                color0,
                true,
                false,
                getLegendLabel(rowIdx, color0)
              );
              rowIdx++;
              const color1 = getColor(colors, index + 1);
              createRangeAndColor(
                colorMap,
                value,
                ((classBreaksValues as Record<string, unknown>).breaks as number[])[index + 1],
                color1,
                false,
                false,
                getLegendLabel(rowIdx, color1)
              );
              rowIdx++;
            } else if (
              index ===
              ((classBreaksValues as Record<string, unknown>).breaks as number[]).length - 1
            ) {
              const color = getColor(colors, index + 1);
              createRangeAndColor(
                colorMap,
                value,
                (classBreaksValues as Record<string, unknown>).max as number,
                color,
                false,
                true,
                getLegendLabel(rowIdx, color)
              );
              rowIdx++;
            } else {
              const color = getColor(colors, index + 1);
              createRangeAndColor(
                colorMap,
                value,
                ((classBreaksValues as Record<string, unknown>).breaks as number[])[index + 1],
                color,
                false,
                false,
                getLegendLabel(rowIdx, color)
              );
              rowIdx++;
            }
          }
        );
      }
    }
  }
  // 2. Simple Color (Single Row)
  else if (properties[type]) {
    // Handle RGB Array or Hex String
    const colorVal = properties[type];
    const hex = Array.isArray(colorVal) ? rgbToHex(colorVal as RGBColor) : (colorVal as string);
    colorMap.push({ value: null, color: hex });
  }

  // 3. Append "No data" entry when a visible no-data color is configured
  const noDataColor = properties[`${type}_no_data`] as string | undefined;
  if (noDataColor && noDataColor !== "transparent" && properties[`${type}_field`]) {
    const noDataLabel = colorLegends?.["no_data"] || "No data";
    colorMap.push({ value: null, color: noDataColor, label: noDataLabel });
  }

  return colorMap;
}

/**
 * Resolves the marker image a given feature renders with on the map:
 * the `marker_mapping` entry matching the feature's `marker_field` value,
 * falling back to the layer's base `marker` — the same precedence as the
 * icon-image match expression in getMapboxStyleMarker. Without feature
 * properties (or without a match) the base marker is returned, so callers
 * can use this for layer-level icons too.
 */
export function resolveFeatureMarker(
  properties: Record<string, unknown>,
  featureProperties?: Record<string, unknown>,
): { url: string; source: "custom" | "library" } | undefined {
  if (properties?.custom_marker !== true) return undefined;

  const fieldName = (properties.marker_field as { name?: string } | undefined)?.name;
  const mapping = properties.marker_mapping as
    | [string[] | null, { url?: string; source?: "custom" | "library" } | null][]
    | undefined;

  if (fieldName && mapping?.length && featureProperties && featureProperties[fieldName] != null) {
    const value = String(featureProperties[fieldName]);
    for (const [values, marker] of mapping) {
      if (values?.map(String).includes(value) && marker?.url) {
        return { url: marker.url, source: marker.source ?? "library" };
      }
    }
  }

  const marker = properties.marker as
    | { url?: string; source?: "custom" | "library" }
    | undefined;
  if (marker?.url) return { url: marker.url, source: marker.source ?? "library" };
  return undefined;
}

export function getLegendMarkerMap(properties: Record<string, unknown>): MarkerMapItem[] {
  const markerMap: MarkerMapItem[] = [];
  if (!properties) return markerMap;

  // Only extract markers if custom_marker is enabled
  if (properties.marker_field && properties.custom_marker === true) {
    // Build a color lookup map from color_range.color_map if it exists and uses the same field
    const colorLookup = new Map<string, string>();
    const markerFieldName = (properties.marker_field as Record<string, unknown>)?.name;
    const colorFieldName = (properties.color_field as Record<string, unknown>)?.name;

    // Only use color mapping if both fields reference the same attribute
    if (markerFieldName === colorFieldName && properties.color_range) {
      const colorMapArray = (properties.color_range as Record<string, unknown>)?.color_map as unknown[];
      colorMapArray?.forEach((entry: unknown) => {
        if (Array.isArray(entry) && entry.length === 2) {
          const values = entry[0] as string[];
          const color = entry[1] as string;
          values?.forEach((val: string) => {
            colorLookup.set(val, color);
          });
        }
      });
    }

    // Get base color as fallback (for when there's no color_field)
    const baseColor = properties.color
      ? Array.isArray(properties.color)
        ? rgbToHex(properties.color as RGBColor)
        : (properties.color as string)
      : null;

    (properties.marker_mapping as unknown[])?.forEach((value: unknown) => {
      const valueArray = value as [string[], { url: string; source?: "custom" | "library" }];
      if (valueArray[1]?.url && valueArray[0]) {
        // Get the color for the first value in the array (categories typically have one value per entry)
        const categoryValue = valueArray[0][0];
        const color = categoryValue ? colorLookup.get(categoryValue) : undefined;

        markerMap.push({
          value: valueArray[0],
          marker: valueArray[1].url,
          color: color || baseColor,
          source: valueArray[1].source || "library",
        });
      }
    });
  } else if (properties.marker && properties.custom_marker === true) {
    // Get base color for single marker
    const baseColor = properties.color
      ? Array.isArray(properties.color)
        ? rgbToHex(properties.color as RGBColor)
        : (properties.color as string)
      : null;

    markerMap.push({
      value: null,
      marker: ((properties.marker as Record<string, unknown>)?.url as string) || null,
      color: baseColor,
      source: ((properties.marker as Record<string, unknown>)?.source as "custom" | "library") || "library",
    });
  }
  return markerMap;
}
