/**
 * @p4b/draw - Formatting utilities
 */
import type { UnitPreference, UnitSystem } from "../types";

// ============================================================================
// Constants
// ============================================================================

const FEET_PER_METER = 3.280839895;
const SQUARE_FEET_PER_SQUARE_METER = FEET_PER_METER * FEET_PER_METER;
const ACRES_PER_SQUARE_METER = 0.000247105381;
const SQUARE_MILES_PER_SQUARE_METER = 3.861021585e-7;

// ============================================================================
// Number Formatting
// ============================================================================

export type NumberFormatter = (value: number, decimals: number, locale?: string) => string;

const defaultFormatter: NumberFormatter = (value, decimals, locale = "en-US") => {
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  }).format(value);
};

// ============================================================================
// Helpers
// ============================================================================

const clamp = (value: number): number => {
  if (!isFinite(value) || isNaN(value)) return 0;
  return Math.max(0, value);
};

export const resolveUnitSystem = (
  preference: UnitPreference | undefined,
  fallback: UnitSystem
): UnitSystem => {
  return preference && preference !== "default" ? preference : fallback;
};

// ============================================================================
// Distance
// ============================================================================

export const formatDistance = (
  meters: number,
  unitSystem: UnitSystem,
  locale = "en-US",
  formatter: NumberFormatter = defaultFormatter
): string => {
  const m = clamp(meters);
  if (unitSystem === "metric") {
    return m >= 1000 ? `${formatter(m / 1000, 2, locale)} km` : `${formatter(m, 2, locale)} m`;
  }
  const feet = m * FEET_PER_METER;
  return feet >= 5280 ? `${formatter(feet / 5280, 2, locale)} mi` : `${formatter(feet, 2, locale)} ft`;
};

// ============================================================================
// Area
// ============================================================================

export const formatArea = (
  squareMeters: number,
  unitSystem: UnitSystem,
  locale = "en-US",
  formatter: NumberFormatter = defaultFormatter
): string => {
  const sqm = clamp(squareMeters);
  if (unitSystem === "metric") {
    return sqm >= 1000000 ? `${formatter(sqm / 1000000, 2, locale)} km²` : `${formatter(sqm, 2, locale)} m²`;
  }
  const sqft = sqm * SQUARE_FEET_PER_SQUARE_METER;
  if (sqft >= 27878400) return `${formatter(sqm * SQUARE_MILES_PER_SQUARE_METER, 2, locale)} mi²`;
  if (sqft >= 43560) return `${formatter(sqm * ACRES_PER_SQUARE_METER, 2, locale)} ac`;
  return `${formatter(sqft, 2, locale)} ft²`;
};

// ============================================================================
// Duration
// ============================================================================

export const formatDuration = (seconds: number): string => {
  const s = clamp(seconds);
  const minutes = Math.floor(s / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    const h = hours % 24;
    return h > 0 ? `${days}d ${h}h` : `${days}d`;
  }
  if (hours > 0) {
    const m = minutes % 60;
    return m > 0 ? `${hours}h ${m}min` : `${hours}h`;
  }
  return `${Math.max(1, minutes)}min`;
};
