import type {
  RasterStyleCategoriesProperties,
  RasterStyleColorRangeProperties,
  RasterStyleHillshadeProperties,
  RasterStyleProperties,
} from "@/lib/validations/layer";

/**
 * Type for pixel data from COG (array of band values)
 */
type PixelData = Float32Array | Uint8Array | Uint16Array | Int16Array | Uint32Array | Int32Array;

/**
 * Type for color output (RGBA as Uint8ClampedArray with 4 elements)
 */
type ColorOutput = Uint8ClampedArray;

/**
 * COG metadata interface from maplibre-cog-protocol
 */
interface CogMetadata {
  noData?: number;
  offset?: number;
  scale?: number;
}

/**
 * Color function type that maplibre-cog-protocol expects
 */
export type COGColorFunction = (pixel: PixelData, color: ColorOutput, metadata: CogMetadata) => void;

/**
 * Generates a color function for COG layers based on the style properties.
 * Note: 'image' style should use MapLibre native raster paint properties instead.
 * This integrates with the maplibre-cog-protocol via setColorFunction().
 * @see https://github.com/geomatico/maplibre-cog-protocol#apply-a-custom-color-function-to-any-cog
 */
export function generateCOGColorFunction(styleProps: RasterStyleProperties): COGColorFunction | null {
  switch (styleProps.style_type) {
    case "color_range":
      return generateColorRangeColorFunction(styleProps);
    case "categories":
      return generateCategoriesColorFunction(styleProps);
    case "hillshade":
      return generateHillshadeColorFunction(styleProps);
    case "image":
      // Image style should use MapLibre native properties, not custom color function
      console.warn("Image style should use MapLibre native raster paint properties");
      return null;
    default:
      // Fallback to simple pass-through
      return (pixel, color) => {
        if (pixel[0] !== null && pixel[0] !== undefined) {
          color.set([pixel[0], pixel[0], pixel[0], 255]);
        } else {
          color.set([0, 0, 0, 0]);
        }
      };
  }
}

/**
 * Parse hex color string to RGB values
 */
function parseColor(colorStr: string): [number, number, number] {
  // Remove # if present
  const hex = colorStr.replace(/^#/, "");

  // Parse hex values
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  return [r, g, b];
}

/**
 * Generate color range color function with gradient
 */
function generateColorRangeColorFunction(props: RasterStyleColorRangeProperties): COGColorFunction {
  const band = (props.band || 1) - 1; // Convert to 0-indexed
  const { min_value, max_value, color_map, no_data_color, interpolate } = props;

  // Build color stops from color_map
  const colorStops = color_map.map(([value, colorStr]) => {
    const rgb = parseColor(colorStr);
    return { value, r: rgb[0], g: rgb[1], b: rgb[2] };
  });

  // Calculate min/max from color_map if not provided
  const minVal = min_value !== undefined ? min_value : (colorStops[0]?.value ?? 0);
  const maxVal = max_value !== undefined ? max_value : (colorStops[colorStops.length - 1]?.value ?? 255);

  const noDataRgba =
    no_data_color && no_data_color !== "transparent" ? [...parseColor(no_data_color), 0] : [0, 0, 0, 0];

  return (pixel, color, metadata) => {
    let value = pixel[band];

    // Handle no-data
    if (value === null || value === undefined || value === metadata.noData) {
      color.set(noDataRgba as unknown as ArrayLike<number>);
      return;
    }

    // Apply scale and offset
    if (metadata.scale !== undefined) {
      value = value * metadata.scale;
    }
    if (metadata.offset !== undefined) {
      value = value + metadata.offset;
    }

    // Out of range handling
    if (value < minVal || value > maxVal) {
      color.set(noDataRgba as unknown as ArrayLike<number>);
      return;
    }

    // Find the two stops to interpolate between
    if (interpolate !== false) {
      for (let i = 0; i < colorStops.length - 1; i++) {
        if (value >= colorStops[i].value && value <= colorStops[i + 1].value) {
          const t = (value - colorStops[i].value) / (colorStops[i + 1].value - colorStops[i].value);
          color.set([
            Math.round(colorStops[i].r + t * (colorStops[i + 1].r - colorStops[i].r)),
            Math.round(colorStops[i].g + t * (colorStops[i + 1].g - colorStops[i].g)),
            Math.round(colorStops[i].b + t * (colorStops[i + 1].b - colorStops[i].b)),
            255,
          ]);
          return;
        }
      }
    } else {
      // Discrete (nearest neighbor)
      let nearestStop = colorStops[0];
      let minDist = Math.abs(value - colorStops[0].value);
      for (let i = 1; i < colorStops.length; i++) {
        const dist = Math.abs(value - colorStops[i].value);
        if (dist < minDist) {
          minDist = dist;
          nearestStop = colorStops[i];
        }
      }
      color.set([nearestStop.r, nearestStop.g, nearestStop.b, 255]);
      return;
    }

    // Fallback to last color
    const lastStop = colorStops[colorStops.length - 1];
    color.set([lastStop.r, lastStop.g, lastStop.b, 255]);
  };
}

/**
 * Generate categorical color function
 */
function generateCategoriesColorFunction(props: RasterStyleCategoriesProperties): COGColorFunction {
  const band = (props.band || 1) - 1; // Convert to 0-indexed
  const { categories, default_color, no_data_color } = props;

  // Build category map
  const categoryMap = new Map<number, [number, number, number, number]>();
  categories.forEach((cat) => {
    // Handle transparent colors
    if (cat.color.toLowerCase() === "transparent") {
      categoryMap.set(cat.value, [0, 0, 0, 0]);
    } else {
      const rgb = parseColor(cat.color);
      categoryMap.set(cat.value, [rgb[0], rgb[1], rgb[2], 255]);
    }
  });

  // Handle transparent default color
  const defaultRgba =
    default_color && default_color.toLowerCase() === "transparent"
      ? [0, 0, 0, 0]
      : [...parseColor(default_color || "#cccccc"), 255];

  const noDataRgba =
    no_data_color && no_data_color !== "transparent" ? [...parseColor(no_data_color), 0] : [0, 0, 0, 0];

  return (pixel, color, metadata) => {
    let value = pixel[band];

    // Handle no-data
    if (value === null || value === undefined || value === metadata.noData) {
      color.set(noDataRgba as unknown as ArrayLike<number>);
      return;
    }

    // Apply scale and offset
    if (metadata.scale !== undefined) {
      value = value * metadata.scale;
    }
    if (metadata.offset !== undefined) {
      value = value + metadata.offset;
    }

    // Round to nearest integer for category lookup
    value = Math.round(value);

    const rgba = categoryMap.get(value);
    if (rgba) {
      color.set(rgba);
    } else {
      color.set(defaultRgba as unknown as ArrayLike<number>);
    }
  };
}

/**
 * Generate hillshade color function
 * Note: True hillshade requires neighboring pixels for slope calculation.
 * This is a simplified version.
 */
function generateHillshadeColorFunction(props: RasterStyleHillshadeProperties): COGColorFunction {
  const band = (props.band || 1) - 1; // Convert to 0-indexed
  const opacity = Math.floor((props.opacity || 1.0) * 255);

  // Note: Proper hillshade requires access to neighboring pixels for slope calculation
  // This is a simplified version that just creates a grayscale representation
  // For true hillshade, consider using MapLibre's built-in hillshade layer type with raster-dem source

  return (pixel, color, metadata) => {
    let elevation = pixel[band];

    // Handle no-data
    if (elevation === null || elevation === undefined || elevation === metadata.noData) {
      color.set([0, 0, 0, 0]);
      return;
    }

    // Apply scale and offset
    if (metadata.scale !== undefined) {
      elevation = elevation * metadata.scale;
    }
    if (metadata.offset !== undefined) {
      elevation = elevation + metadata.offset;
    }

    // Apply z-factor
    elevation = elevation * (props.z_factor || 1.0);

    // Simplified shading (just use elevation as intensity)
    // In production, this should calculate slope and aspect from neighboring pixels
    const intensity = Math.max(0, Math.min(255, Math.floor(elevation)));

    color.set([intensity, intensity, intensity, opacity]);
  };
}

/**
 * Validates that style properties match the expected raster style schema
 */
export function validateCOGStyleProperties(styleProps: unknown): styleProps is RasterStyleProperties {
  if (!styleProps || typeof styleProps !== "object") {
    return false;
  }

  const props = styleProps as Record<string, unknown>;

  // Check for required style_type field
  if (
    !props.style_type ||
    !["image", "color_range", "categories", "hillshade"].includes(props.style_type as string)
  ) {
    return false;
  }

  return true;
}
