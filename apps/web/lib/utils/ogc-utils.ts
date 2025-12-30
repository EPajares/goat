/**
 * Utility functions for processing OGC API Processes schemas
 *
 * Transforms OGC input descriptions into UI-friendly structures
 */
import type {
  InferredInputType,
  OGCInputDescription,
  OGCInputSchema,
  OGCProcessDescription,
  ProcessedInput,
} from "@/types/map/ogc-processes";

// Inputs that are handled automatically (not shown in form)
const HIDDEN_INPUT_NAMES = ["user_id", "project_id", "save_results"];

// Inputs that go in advanced settings section
const ADVANCED_INPUT_NAMES = ["output_crs", "output_name", "scenario_id"];

/**
 * Infer the input type from OGC input schema
 */
export function inferInputType(input: OGCInputDescription, inputName: string): InferredInputType {
  const { schema, keywords } = input;

  // Check keywords first (more specific)
  if (keywords.includes("layer")) {
    return "layer";
  }

  if (keywords.includes("field")) {
    return "field";
  }

  // Infer field type from naming convention (e.g., "target_field", "join_field")
  if (inputName.endsWith("_field") || inputName.endsWith("Field")) {
    return "field";
  }

  // Get the effective schema (handle anyOf/oneOf for nullable types)
  const effectiveSchema = getEffectiveSchema(schema);

  // Check schema type
  if (effectiveSchema.enum && effectiveSchema.enum.length > 0) {
    return "enum";
  }

  if (effectiveSchema.type === "boolean") {
    return "boolean";
  }

  if (effectiveSchema.type === "number" || effectiveSchema.type === "integer") {
    return "number";
  }

  if (effectiveSchema.type === "string") {
    return "string";
  }

  if (effectiveSchema.type === "array") {
    return "array";
  }

  if (effectiveSchema.type === "object" || effectiveSchema.properties) {
    return "object";
  }

  // Check for $ref (usually enum types)
  if (effectiveSchema.$ref) {
    return "enum";
  }

  return "unknown";
}

/**
 * Get the effective schema, handling anyOf/oneOf patterns for nullable types
 */
export function getEffectiveSchema(schema: OGCInputSchema): OGCInputSchema {
  // Handle anyOf pattern (commonly used for nullable types)
  if (schema.anyOf && schema.anyOf.length > 0) {
    // Find the non-null schema
    const nonNullSchema = schema.anyOf.find((s) => s.type !== "null");
    if (nonNullSchema) {
      return { ...nonNullSchema, default: schema.default };
    }
  }

  // Handle oneOf pattern
  if (schema.oneOf && schema.oneOf.length > 0) {
    const nonNullSchema = schema.oneOf.find((s) => s.type !== "null");
    if (nonNullSchema) {
      return { ...nonNullSchema, default: schema.default };
    }
  }

  return schema;
}

/**
 * Extract geometry constraints from input metadata
 */
export function extractGeometryConstraints(input: OGCInputDescription): string[] | undefined {
  const constraintMeta = input.metadata.find(
    (m) => m.role === "constraint" && m.title === "Accepted Geometry Types"
  );

  if (constraintMeta && Array.isArray(constraintMeta.value)) {
    return constraintMeta.value as string[];
  }

  return undefined;
}

/**
 * Extract enum values from schema
 */
export function extractEnumValues(schema: OGCInputSchema): (string | number | boolean)[] | undefined {
  const effectiveSchema = getEffectiveSchema(schema);

  if (effectiveSchema.enum) {
    return effectiveSchema.enum;
  }

  // Check for $ref to $defs (common pattern for enum types)
  // Note: This would need the full schema with $defs to resolve
  // For now, return undefined and handle in the component

  return undefined;
}

/**
 * Process a single OGC input description into UI-friendly format
 */
export function processInput(name: string, input: OGCInputDescription): ProcessedInput {
  const inputType = inferInputType(input, name);
  const effectiveSchema = getEffectiveSchema(input.schema);

  return {
    name,
    title: input.title,
    description: input.description,
    inputType,
    required: input.minOccurs > 0,
    schema: input.schema,
    defaultValue: effectiveSchema.default,
    enumValues: extractEnumValues(input.schema),
    isLayerInput: input.keywords.includes("layer"),
    geometryConstraints: extractGeometryConstraints(input),
    metadata: input.metadata,
  };
}

/**
 * Process all inputs from a process description
 */
export function processInputs(process: OGCProcessDescription): {
  mainInputs: ProcessedInput[];
  advancedInputs: ProcessedInput[];
  hiddenInputs: ProcessedInput[];
} {
  const mainInputs: ProcessedInput[] = [];
  const advancedInputs: ProcessedInput[] = [];
  const hiddenInputs: ProcessedInput[] = [];

  for (const [name, input] of Object.entries(process.inputs)) {
    const processed = processInput(name, input);

    if (HIDDEN_INPUT_NAMES.includes(name)) {
      hiddenInputs.push(processed);
    } else if (ADVANCED_INPUT_NAMES.includes(name)) {
      advancedInputs.push(processed);
    } else {
      mainInputs.push(processed);
    }
  }

  // Sort: required inputs first, then by name
  mainInputs.sort((a, b) => {
    if (a.required !== b.required) {
      return a.required ? -1 : 1;
    }
    return a.name.localeCompare(b.name);
  });

  return { mainInputs, advancedInputs, hiddenInputs };
}

/**
 * Get default values for all inputs
 */
export function getDefaultValues(process: OGCProcessDescription): Record<string, unknown> {
  const defaults: Record<string, unknown> = {};

  for (const [name, input] of Object.entries(process.inputs)) {
    const effectiveSchema = getEffectiveSchema(input.schema);
    if (effectiveSchema.default !== undefined) {
      defaults[name] = effectiveSchema.default;
    }
  }

  return defaults;
}

/**
 * Validate inputs against process schema
 * Returns array of error messages, empty if valid
 */
export function validateInputs(process: OGCProcessDescription, values: Record<string, unknown>): string[] {
  const errors: string[] = [];

  for (const [name, input] of Object.entries(process.inputs)) {
    const value = values[name];
    const isRequired = input.minOccurs > 0;

    // Check required fields
    if (isRequired && (value === undefined || value === null || value === "")) {
      // Skip hidden inputs that will be added automatically
      if (!HIDDEN_INPUT_NAMES.includes(name)) {
        errors.push(`${input.title} is required`);
      }
    }
  }

  return errors;
}

/**
 * Check if a layer type matches the geometry constraints
 */
export function matchesGeometryConstraint(
  layerGeometryType: string | undefined,
  constraints: string[] | undefined
): boolean {
  if (!constraints || constraints.length === 0) {
    return true; // No constraints means any geometry is accepted
  }

  if (!layerGeometryType) {
    return false;
  }

  // Normalize geometry type names for comparison
  const normalizedLayerType = layerGeometryType.toLowerCase();
  const normalizedConstraints = constraints.map((c) => c.toLowerCase());

  return normalizedConstraints.some((constraint) => {
    // Handle variations like "polygon" matching "Polygon" or "MultiPolygon"
    if (normalizedLayerType.includes(constraint)) {
      return true;
    }
    // Handle "multi" prefix
    if (constraint.startsWith("multi") && normalizedLayerType === constraint.substring(5)) {
      return true;
    }
    if (normalizedLayerType.startsWith("multi") && normalizedLayerType.substring(5) === constraint) {
      return true;
    }
    return normalizedLayerType === constraint;
  });
}

/**
 * Format input name for display (snake_case to Title Case)
 */
export function formatInputName(name: string): string {
  return name
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
