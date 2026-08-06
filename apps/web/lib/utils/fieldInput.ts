/**
 * Shared helpers for editing field values by kind. Every editor surface
 * (feature panel, data table cells, map edit popover) goes through these so
 * option labels, parsing, and serialization stay identical.
 */

/** Options for boolean value dropdowns; the empty option writes NULL. */
export const BOOLEAN_SELECT_ITEMS = [
  { value: "", label: "—" },
  { value: "true", label: "True" },
  { value: "false", label: "False" },
] as const;

/** Select-input string -> stored boolean value ("" -> NULL). */
export const parseBooleanInput = (value: string): boolean | null =>
  value === "" ? null : value === "true";

/** Stored boolean value -> select-input string (NULL/undefined -> ""). */
export const booleanToSelectValue = (raw: unknown): string =>
  raw === true ? "true" : raw === false ? "false" : "";
