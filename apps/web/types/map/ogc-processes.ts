/**
 * OGC API Processes types for generic toolbox
 *
 * Based on OGC API - Processes - Part 1: Core (OGC 18-062r2)
 * Extended with UI hints for generic form rendering
 */

// ============================================================================
// OGC Process List Types
// ============================================================================

export interface OGCLink {
  href: string;
  rel: string;
  type?: string;
  title?: string;
  templated?: boolean;
}

export interface OGCProcessSummary {
  id: string;
  title: string;
  description?: string;
  version: string;
  jobControlOptions: string[];
  outputTransmission: string[];
  links: OGCLink[];
}

export interface OGCProcessList {
  processes: OGCProcessSummary[];
  links: OGCLink[];
}

// ============================================================================
// OGC Process Description Types
// ============================================================================

export interface OGCMetadata {
  title: string;
  role?: string;
  href?: string;
  value?: unknown;
}

export interface OGCInputDescription {
  title: string;
  description?: string;
  schema: OGCInputSchema;
  minOccurs: number;
  maxOccurs: number | string;
  keywords: string[];
  metadata: OGCMetadata[];
}

export interface OGCOutputDescription {
  title: string;
  description?: string;
  schema: OGCInputSchema;
}

export interface OGCProcessDescription extends OGCProcessSummary {
  inputs: Record<string, OGCInputDescription>;
  outputs: Record<string, OGCOutputDescription>;
}

// ============================================================================
// JSON Schema Types (subset used by OGC)
// ============================================================================

export interface OGCInputSchema {
  type?: string;
  title?: string;
  description?: string;
  default?: unknown;
  enum?: (string | number | boolean)[];
  format?: string;
  minimum?: number;
  maximum?: number;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  items?: OGCInputSchema;
  properties?: Record<string, OGCInputSchema>;
  required?: string[];
  anyOf?: OGCInputSchema[];
  oneOf?: OGCInputSchema[];
  allOf?: OGCInputSchema[];
  $ref?: string;
  $defs?: Record<string, OGCInputSchema>;
}

// ============================================================================
// Execution Types
// ============================================================================

export interface OGCExecuteRequest {
  inputs: Record<string, unknown>;
  outputs?: Record<string, OGCOutputDefinition>;
  response?: "raw" | "document";
}

export interface OGCOutputDefinition {
  transmissionMode?: "value" | "reference";
  format?: Record<string, string>;
}

export interface OGCJobStatus {
  processID?: string;
  type: string;
  jobID: string;
  status: "accepted" | "running" | "successful" | "failed" | "dismissed";
  message?: string;
  created?: string;
  started?: string;
  finished?: string;
  updated?: string;
  progress?: number;
  links: OGCLink[];
}

// ============================================================================
// UI Helper Types
// ============================================================================

/**
 * Inferred input type based on schema analysis
 */
export type InferredInputType =
  | "layer" // Layer selector (keywords includes "layer")
  | "field" // Field selector (keywords includes "field")
  | "enum" // Dropdown (schema has enum)
  | "boolean" // Switch (type is boolean)
  | "number" // Number input (type is number/integer)
  | "string" // Text input (type is string)
  | "array" // Array input (type is array)
  | "object" // Nested object (type is object)
  | "unknown"; // Fallback

/**
 * Processed input for UI rendering
 */
export interface ProcessedInput {
  name: string;
  title: string;
  description?: string;
  inputType: InferredInputType;
  required: boolean;
  schema: OGCInputSchema;
  defaultValue?: unknown;
  enumValues?: (string | number | boolean)[];
  isLayerInput: boolean;
  geometryConstraints?: string[];
  metadata: OGCMetadata[];
}

/**
 * Tool category for grouping in toolbox
 */
export type ToolCategory =
  | "geoprocessing"
  | "geoanalysis"
  | "data_management"
  | "accessibility_indicators"
  | "other";

/**
 * Tool with category assignment
 */
export interface CategorizedTool extends OGCProcessSummary {
  category: ToolCategory;
  icon?: string;
}

// ============================================================================
// Utility Functions Types
// ============================================================================

/**
 * Map tool IDs to categories (client-side mapping until backend provides it)
 */
export const TOOL_CATEGORY_MAP: Record<string, ToolCategory> = {
  // Geoprocessing
  buffer: "geoprocessing",
  clip: "geoprocessing",
  difference: "geoprocessing",
  intersection: "geoprocessing",
  union: "geoprocessing",
  merge: "geoprocessing",
  centroid: "geoprocessing",
  // Geoanalysis
  origin_destination: "geoanalysis",
  // Data management
  join: "data_management",
};

/**
 * Map tool IDs to icons (client-side mapping)
 */
export const TOOL_ICON_MAP: Record<string, string> = {
  buffer: "BUFFER",
  clip: "CLIP",
  difference: "DIFFERENCE",
  intersection: "INTERSECTION",
  union: "UNION",
  merge: "MERGE",
  centroid: "CENTROID",
  join: "JOIN",
  origin_destination: "ROUTE",
};

/**
 * Inputs that should be hidden from the generic form (handled automatically)
 */
export const HIDDEN_INPUTS = ["user_id", "project_id", "save_results"];

/**
 * Inputs that should be shown in advanced settings
 */
export const ADVANCED_INPUTS = ["output_crs", "output_name", "scenario_id"];
