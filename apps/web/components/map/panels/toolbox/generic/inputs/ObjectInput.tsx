/**
 * Object Input Component
 *
 * Renders a nested object form with its properties.
 * Used for complex object fields that contain multiple sub-properties.
 */
import { Box, Stack, Typography, useTheme } from "@mui/material";
import { useMemo } from "react";

import { formatInputName, getVisibleInputs } from "@/lib/utils/ogc-utils";

import type { OGCInputSchema, ProcessedInput } from "@/types/map/ogc-processes";

import { GenericInput } from "@/components/map/panels/toolbox/generic/inputs";

interface ObjectInputProps {
  input: ProcessedInput;
  value: Record<string, unknown> | undefined;
  onChange: (value: Record<string, unknown> | undefined) => void;
  disabled?: boolean;
  /** Schema definitions ($defs) for resolving $ref */
  schemaDefs?: Record<string, OGCInputSchema>;
  /** All form values for conditional visibility and field inputs */
  formValues?: Record<string, unknown>;
}

/**
 * Process object schema properties into ProcessedInput array
 */
function processObjectProperties(
  objectSchema: OGCInputSchema,
  schemaDefs?: Record<string, OGCInputSchema>
): ProcessedInput[] {
  const properties = objectSchema.properties || {};
  const requiredFields = objectSchema.required || [];

  const inputs: ProcessedInput[] = [];

  for (const [propName, propSchema] of Object.entries(properties)) {
    // Resolve $ref if present (direct or within anyOf for nullable types)
    let resolvedSchema = propSchema;

    if (propSchema.$ref && schemaDefs) {
      // Direct $ref
      const refName = propSchema.$ref.replace("#/$defs/", "");
      const refSchema = schemaDefs[refName];
      if (refSchema) {
        resolvedSchema = { ...refSchema, ...propSchema, $ref: undefined };
      }
    } else if (propSchema.anyOf && schemaDefs) {
      // anyOf pattern (commonly used for nullable enums: [{"$ref": "..."}, {"type": "null"}])
      const refItem = propSchema.anyOf.find((item) => item.$ref);
      if (refItem?.$ref) {
        const refName = refItem.$ref.replace("#/$defs/", "");
        const refSchema = schemaDefs[refName];
        if (refSchema) {
          // Merge: ref schema provides enum/type, propSchema provides description/x-ui/default
          resolvedSchema = { ...refSchema, ...propSchema, anyOf: undefined };
        }
      }
    }

    const uiMeta = resolvedSchema["x-ui"] || propSchema["x-ui"];
    const isRequired = requiredFields.includes(propName);

    // Infer input type
    let inputType: ProcessedInput["inputType"] = "string";

    if (uiMeta?.widget === "layer-selector") {
      inputType = "layer";
    } else if (uiMeta?.widget === "field-selector" || propName.endsWith("_field")) {
      inputType = "field";
    } else if (resolvedSchema.enum) {
      inputType = "enum";
    } else if (resolvedSchema.type === "boolean") {
      inputType = "boolean";
    } else if (resolvedSchema.type === "number" || resolvedSchema.type === "integer") {
      inputType = "number";
    } else if (resolvedSchema.type === "string") {
      inputType = "string";
    } else if (resolvedSchema.type === "array") {
      inputType = "array";
    } else if (resolvedSchema.type === "object") {
      inputType = "object";
    }

    // Extract enum values
    let enumValues: (string | number | boolean)[] | undefined;
    if (resolvedSchema.enum) {
      enumValues = resolvedSchema.enum;
    }

    inputs.push({
      name: propName,
      title: resolvedSchema.title || formatInputName(propName),
      description: resolvedSchema.description,
      inputType,
      required: isRequired,
      schema: resolvedSchema,
      defaultValue: resolvedSchema.default,
      enumValues,
      isLayerInput: uiMeta?.widget === "layer-selector",
      geometryConstraints: uiMeta?.widget_options?.geometry_types as string[] | undefined,
      metadata: [],
      section: uiMeta?.section || "main",
      fieldOrder: uiMeta?.field_order ?? 100,
      uiMeta,
    });
  }

  // Sort by field order
  inputs.sort((a, b) => a.fieldOrder - b.fieldOrder);

  return inputs;
}

/**
 * Get default values for a nested object
 */
function getObjectDefaults(
  objectSchema: OGCInputSchema,
  schemaDefs?: Record<string, OGCInputSchema>
): Record<string, unknown> {
  const defaults: Record<string, unknown> = {};
  const properties = objectSchema.properties || {};

  for (const [propName, propSchema] of Object.entries(properties)) {
    // Resolve $ref if needed
    let resolvedSchema = propSchema;
    if (propSchema.$ref && schemaDefs) {
      const refName = propSchema.$ref.replace("#/$defs/", "");
      const refSchema = schemaDefs[refName];
      if (refSchema) {
        resolvedSchema = { ...refSchema, ...propSchema };
      }
    }

    if (resolvedSchema.default !== undefined) {
      defaults[propName] = resolvedSchema.default;
    }
  }

  return defaults;
}

export default function ObjectInput({
  input,
  value,
  onChange,
  disabled,
  schemaDefs,
  formValues: _formValues = {},
}: ObjectInputProps) {
  const theme = useTheme();

  // Get object schema (resolve $ref if needed)
  const objectSchema = useMemo(() => {
    const schema = input.schema;
    if (!schema) return null;

    if (schema.$ref && schemaDefs) {
      const refName = schema.$ref.replace("#/$defs/", "");
      return schemaDefs[refName] || schema;
    }
    return schema;
  }, [input.schema, schemaDefs]);

  // Process object properties into input definitions
  const objectInputs = useMemo(() => {
    if (!objectSchema) return [];
    return processObjectProperties(objectSchema, schemaDefs);
  }, [objectSchema, schemaDefs]);

  // Initialize value with defaults if undefined
  const objectValue = useMemo(() => {
    if (value !== undefined) return value;
    if (!objectSchema) return {};
    return getObjectDefaults(objectSchema, schemaDefs);
  }, [value, objectSchema, schemaDefs]);

  // Get visible inputs based on current values
  const visibleInputs = getVisibleInputs(objectInputs, objectValue);

  const handlePropertyChange = (propName: string, newValue: unknown) => {
    const updated = { ...objectValue, [propName]: newValue };
    onChange(updated);
  };

  if (!objectSchema) {
    return (
      <Typography variant="body2" color="text.secondary">
        Invalid object schema
      </Typography>
    );
  }

  return (
    <Box>
      {/* Object label */}
      <Typography variant="body2" fontWeight="medium" sx={{ mb: 1.5, color: theme.palette.text.secondary }}>
        {input.title || formatInputName(input.name)}
      </Typography>

      {/* Object properties */}
      <Stack
        spacing={2}
        sx={{
          pl: 2,
          borderLeft: `2px solid ${theme.palette.divider}`,
        }}>
        {visibleInputs.map((inputDef) => (
          <GenericInput
            key={inputDef.name}
            input={inputDef}
            value={objectValue[inputDef.name]}
            onChange={(newValue) => handlePropertyChange(inputDef.name, newValue)}
            disabled={disabled}
            formValues={{ ..._formValues, ...objectValue }}
            schemaDefs={schemaDefs}
          />
        ))}
      </Stack>
    </Box>
  );
}
