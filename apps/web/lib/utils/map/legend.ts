import { formatNumber, rgbToHex } from "@/lib/utils/helpers";

import type { RGBColor } from "@/types/map/color";

// Types
export type ColorMapItem = {
  value: string[] | null;
  color: string;
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
  isLast?: boolean
): void => {
  const range = `${isFirst ? "<" : ""}${formatNumber(rangeStart, 2)} - ${isLast ? ">" : ""}${formatNumber(rangeEnd, 2)}`;
  colorMap.push({ value: [range], color });
};

// --- MAIN PARSERS ---

export function getLegendColorMap(
  properties: Record<string, unknown> | null,
  type: "color" | "stroke_color"
): ColorMapItem[] {
  const colorMap: ColorMapItem[] = [];
  if (!properties) return colorMap;

  // 1. Attribute Field Based (Complex Legend)
  if (properties?.[`${type}_field`]) {
    if (["ordinal"].includes(properties[`${type}_scale`] as string)) {
      // Ordinal (Categories)
      ((properties[`${type}_range`] as Record<string, unknown>)?.color_map as unknown[])?.forEach(
        (value: unknown) => {
          if (Array.isArray(value) && value.length === 2) {
            colorMap.push({ value: value[0], color: value[1] as string });
          }
        }
      );
    } else {
      // Sequential/Quantile (Ranges)
      const scaleType = properties[`${type}_scale`] as string;
      let classBreaksValues = properties[`${type}_scale_breaks`] as Record<string, unknown>;
      let colors = (properties[`${type}_range`] as Record<string, unknown>)?.colors as string[];

      if (scaleType === "custom_breaks") {
        const colorMapValues = (properties[`${type}_range`] as Record<string, unknown>)?.color_map;
        const _customClassBreaks: { breaks: number[]; min?: number; max?: number } = {
          breaks: [],
          ...(classBreaksValues || {}),
        };
        const _colors: string[] = [];

        (colorMapValues as unknown[])?.forEach((value: unknown, index: number) => {
          const valueArray = value as [unknown[], string];
          _colors.push(valueArray[1]);
          if (index === 0) return;
          if (valueArray[0] !== null && valueArray[0] !== undefined) {
            _customClassBreaks.breaks.push(Number(valueArray[0][0]));
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
        ((classBreaksValues as Record<string, unknown>).breaks as number[]).forEach(
          (value: number, index: number) => {
            if (index === 0) {
              createRangeAndColor(
                colorMap,
                (classBreaksValues as Record<string, unknown>).min as number,
                value,
                getColor(colors, index),
                true
              );
              createRangeAndColor(
                colorMap,
                value,
                ((classBreaksValues as Record<string, unknown>).breaks as number[])[index + 1],
                getColor(colors, index + 1)
              );
            } else if (
              index ===
              ((classBreaksValues as Record<string, unknown>).breaks as number[]).length - 1
            ) {
              createRangeAndColor(
                colorMap,
                value,
                (classBreaksValues as Record<string, unknown>).max as number,
                getColor(colors, index + 1),
                false,
                true
              );
            } else {
              createRangeAndColor(
                colorMap,
                value,
                ((classBreaksValues as Record<string, unknown>).breaks as number[])[index + 1],
                getColor(colors, index + 1)
              );
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

  return colorMap;
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
