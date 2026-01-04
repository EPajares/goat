import { formatNumber } from "@/lib/utils/format-number";

export type UnitSystem = "metric" | "imperial";
export type UnitPreference = UnitSystem | "default";

const FEET_PER_METER = 3.280839895;
const SQUARE_FEET_PER_SQUARE_METER = FEET_PER_METER * FEET_PER_METER;
const ACRES_PER_SQUARE_METER = 0.000247105381;
const SQUARE_MILES_PER_SQUARE_METER = 3.861021585e-7;

const clampNumber = (value: number) => {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.max(0, value);
};

const formatMetricDistance = (meters: number, language: string): string => {
  if (meters >= 1000) {
    return `${formatNumber(meters / 1000, "decimal_2", language)} km`;
  }
  return `${formatNumber(meters, "decimal_2", language)} m`;
};

const formatImperialDistance = (meters: number, language: string): string => {
  const feet = meters * FEET_PER_METER;
  if (feet >= 5280) {
    return `${formatNumber(feet / 5280, "decimal_2", language)} mi`;
  }
  return `${formatNumber(feet, "decimal_2", language)} ft`;
};

const formatMetricArea = (squareMeters: number, language: string): string => {
  if (squareMeters >= 1000000) {
    return `${formatNumber(squareMeters / 1000000, "decimal_2", language)} km²`;
  }
  return `${formatNumber(squareMeters, "decimal_2", language)} m²`;
};

const formatImperialArea = (squareMeters: number, language: string): string => {
  const squareFeet = squareMeters * SQUARE_FEET_PER_SQUARE_METER;
  if (squareFeet >= 27878400) {
    const squareMiles = squareMeters * SQUARE_MILES_PER_SQUARE_METER;
    return `${formatNumber(squareMiles, "decimal_2", language)} mi²`;
  }
  if (squareFeet >= 43560) {
    const acres = squareMeters * ACRES_PER_SQUARE_METER;
    return `${formatNumber(acres, "decimal_2", language)} ac`;
  }
  return `${formatNumber(squareFeet, "decimal_2", language)} ft²`;
};

export const resolveUnitSystem = (
  preference: UnitPreference | undefined,
  fallback: UnitSystem
): UnitSystem => {
  if (preference && preference !== "default") {
    return preference;
  }
  return fallback;
};

export const formatDistance = (
  meters: number,
  unitSystem: UnitSystem,
  language: string = "en-US"
): string => {
  const safeMeters = clampNumber(meters);
  return unitSystem === "metric"
    ? formatMetricDistance(safeMeters, language)
    : formatImperialDistance(safeMeters, language);
};

export const formatArea = (
  squareMeters: number,
  unitSystem: UnitSystem,
  language: string = "en-US"
): string => {
  const safeArea = clampNumber(squareMeters);
  return unitSystem === "metric"
    ? formatMetricArea(safeArea, language)
    : formatImperialArea(safeArea, language);
};
