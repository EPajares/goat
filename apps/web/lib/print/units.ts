/**
 * Unit conversion utilities for print layouts
 * Converts between millimeters (print units) and pixels (screen units)
 */

// Standard DPI for screen displays
export const SCREEN_DPI = 96;

// Standard DPI for print quality
export const PRINT_DPI = 300;

// Conversion constant: 1 inch = 25.4 millimeters
export const MM_PER_INCH = 25.4;

/**
 * Convert millimeters to pixels
 * @param mm - Value in millimeters
 * @param dpi - Dots per inch (default: 96 for screen)
 * @returns Value in pixels
 */
export function mmToPx(mm: number, dpi: number = SCREEN_DPI): number {
  return (mm / MM_PER_INCH) * dpi;
}

/**
 * Convert pixels to millimeters
 * @param px - Value in pixels
 * @param dpi - Dots per inch (default: 96 for screen)
 * @returns Value in millimeters
 */
export function pxToMm(px: number, dpi: number = SCREEN_DPI): number {
  return (px / dpi) * MM_PER_INCH;
}

/**
 * Convert inches to millimeters
 */
export function inchesToMm(inches: number): number {
  return inches * MM_PER_INCH;
}

/**
 * Convert millimeters to inches
 */
export function mmToInches(mm: number): number {
  return mm / MM_PER_INCH;
}

/**
 * Standard page sizes in millimeters
 */
export const PAGE_SIZES = {
  A4: { width: 210, height: 297 },
  A3: { width: 297, height: 420 },
  Letter: { width: inchesToMm(8.5), height: inchesToMm(11) },
  Legal: { width: inchesToMm(8.5), height: inchesToMm(14) },
  Tabloid: { width: inchesToMm(11), height: inchesToMm(17) },
} as const;

export type PageSize = keyof typeof PAGE_SIZES;
export type PageOrientation = "portrait" | "landscape";

/**
 * Get page dimensions in millimeters
 * @param size - Page size name
 * @param orientation - Page orientation
 * @returns Width and height in millimeters
 */
export function getPageDimensions(
  size: PageSize,
  orientation: PageOrientation = "portrait"
): { width: number; height: number } {
  const dims = PAGE_SIZES[size];

  if (orientation === "landscape") {
    return { width: dims.height, height: dims.width };
  }

  return { width: dims.width, height: dims.height };
}

/**
 * Calculate scale factor to fit content to page
 * @param contentWidth - Content width in mm
 * @param contentHeight - Content height in mm
 * @param pageSize - Target page size
 * @param orientation - Page orientation
 * @param margins - Page margins in mm
 * @returns Scale factor (1.0 = 100%)
 */
export function calculateScaleToFit(
  contentWidth: number,
  contentHeight: number,
  pageSize: PageSize,
  orientation: PageOrientation = "portrait",
  margins = { top: 10, right: 10, bottom: 10, left: 10 }
): number {
  const page = getPageDimensions(pageSize, orientation);
  const availableWidth = page.width - margins.left - margins.right;
  const availableHeight = page.height - margins.top - margins.bottom;

  const scaleX = availableWidth / contentWidth;
  const scaleY = availableHeight / contentHeight;

  // Use the smaller scale to ensure content fits
  return Math.min(scaleX, scaleY, 1); // Never scale up beyond 100%
}
