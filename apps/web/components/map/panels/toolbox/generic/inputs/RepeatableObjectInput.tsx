/**
 * Repeatable Object Input Component
 *
 * Renders a list of nested object forms with add/remove functionality.
 * Used for array fields with complex object items (e.g., opportunities in heatmap tools).
 */
import { Box, Button, Divider, IconButton, Stack, Typography, useTheme } from "@mui/material";
import { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { v4 as uuidv4 } from "uuid";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import { formatInputName, getVisibleInputs } from "@/lib/utils/ogc-utils";

import type { OGCInputSchema, ProcessedInput } from "@/types/map/ogc-processes";

import { GenericInput } from "@/components/map/panels/toolbox/generic/inputs";

interface RepeatableObjectInputProps {
  input: ProcessedInput;
  value: Record<string, unknown>[] | undefined;
  onChange: (value: Record<string, unknown>[] | undefined) => void;
  disabled?: boolean;
  /** Schema definitions ($defs) for resolving $ref */
  schemaDefs?: Record<string, OGCInputSchema>;
  /** All form values for conditional visibility */
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
 * Get default values for a new object item
 */
function getObjectDefaults(
  objectSchema: OGCInputSchema,
  schemaDefs?: Record<string, OGCInputSchema>
): Record<string, unknown> {
  const defaults: Record<string, unknown> = {};
  const properties = objectSchema.properties || {};

  for (const [propName, propSchema] of Object.entries(properties)) {
    // Resolve $ref if present
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

export default function RepeatableObjectInput({
  input,
  value,
  onChange,
  disabled,
  schemaDefs,
  formValues: _formValues,
}: RepeatableObjectInputProps) {
  const { t } = useTranslation("common");
  const theme = useTheme();

  // Get item schema (resolve $ref if needed)
  const itemSchema = useMemo(() => {
    const schema = input.schema.items;
    if (!schema) return null;

    if (schema.$ref && schemaDefs) {
      const refName = schema.$ref.replace("#/$defs/", "");
      return schemaDefs[refName] || schema;
    }
    return schema;
  }, [input.schema.items, schemaDefs]);

  // Process item properties into input definitions
  const itemInputs = useMemo(() => {
    if (!itemSchema) return [];
    return processObjectProperties(itemSchema, schemaDefs);
  }, [itemSchema, schemaDefs]);

  // Get UI constraints
  const minItems = input.uiMeta?.min_items ?? 0;
  const maxItems = input.uiMeta?.max_items ?? 10;

  // Current items (ensure at least minItems)
  const items = useMemo(() => {
    const currentItems = value || [];
    if (currentItems.length < minItems && itemSchema) {
      const defaults = getObjectDefaults(itemSchema, schemaDefs);
      const newItems = [...currentItems];
      while (newItems.length < minItems) {
        newItems.push({ ...defaults, _id: uuidv4() });
      }
      return newItems;
    }
    // Ensure all items have _id for stable keys
    return currentItems.map((item) => ({
      ...item,
      _id: (item as Record<string, unknown>)._id || uuidv4(),
    }));
  }, [value, minItems, itemSchema, schemaDefs]);

  // Initialize if empty
  useMemo(() => {
    if ((!value || value.length === 0) && minItems > 0 && itemSchema) {
      const defaults = getObjectDefaults(itemSchema, schemaDefs);
      const initialItems: Record<string, unknown>[] = [];
      for (let i = 0; i < minItems; i++) {
        initialItems.push({ ...defaults, _id: uuidv4() });
      }
      // Defer onChange to avoid render cycle
      setTimeout(() => onChange(initialItems), 0);
    }
  }, [value, minItems, itemSchema, schemaDefs, onChange]);

  // Add new item
  const handleAdd = useCallback(() => {
    if (items.length >= maxItems || !itemSchema) return;
    const defaults = getObjectDefaults(itemSchema, schemaDefs);
    const newItems = [...items, { ...defaults, _id: uuidv4() }];
    onChange(newItems);
  }, [items, maxItems, itemSchema, schemaDefs, onChange]);

  // Remove item
  const handleRemove = useCallback(
    (index: number) => {
      if (items.length <= minItems) return;
      const newItems = items.filter((_, i) => i !== index);
      onChange(newItems);
    },
    [items, minItems, onChange]
  );

  // Collect layer input names for detecting layer changes and exclusion
  const layerInputNames = useMemo(() => {
    return itemInputs.filter((inp) => inp.inputType === "layer").map((inp) => inp.name);
  }, [itemInputs]);

  // Update item property
  const handleItemChange = useCallback(
    (index: number, propName: string, propValue: unknown) => {
      const newItems = items.map((item, i) => {
        if (i !== index) return item;

        // If changing a layer input, reset all other fields to defaults (except _id)
        const isLayerInput = layerInputNames.includes(propName);
        if (isLayerInput && itemSchema) {
          const defaults = getObjectDefaults(itemSchema, schemaDefs);
          return {
            ...defaults,
            _id: (item as Record<string, unknown>)._id,
            [propName]: propValue,
          };
        }

        return { ...item, [propName]: propValue };
      });
      onChange(newItems);
    },
    [items, onChange, layerInputNames, itemSchema, schemaDefs]
  );

  // Get all selected layer IDs across all items for each layer input
  // This prevents selecting the same layer twice across items
  const selectedLayerIdsByInput = useMemo(() => {
    const result: Record<string, string[]> = {};
    for (const layerInputName of layerInputNames) {
      result[layerInputName] = items
        .map((item) => (item as Record<string, unknown>)[layerInputName] as string | undefined)
        .filter((id): id is string => Boolean(id));
    }
    return result;
  }, [items, layerInputNames]);

  if (!itemSchema || itemInputs.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        {t("complex_input_not_supported")}: {input.title}
      </Typography>
    );
  }

  const canAdd = items.length < maxItems;
  const canRemove = items.length > minItems;

  return (
    <Stack spacing={2}>
      {items.map((item, index) => {
        const itemValues = item as Record<string, unknown>;
        const visibleInputs = getVisibleInputs(itemInputs, itemValues);

        // Calculate excluded layer IDs for this item's layer inputs
        // (exclude layers selected in OTHER items, not this item's current selection)
        const getExcludedLayerIds = (inputName: string): string[] => {
          if (!layerInputNames.includes(inputName)) return [];
          const currentValue = itemValues[inputName] as string | undefined;
          return (selectedLayerIdsByInput[inputName] || []).filter((id) => id !== currentValue);
        };

        return (
          <Box key={itemValues._id as string} sx={{ position: "relative" }}>
            {/* Remove button for non-first items */}
            {index > 0 && canRemove && (
              <Stack direction="row" alignItems="center" justifyContent="flex-end" sx={{ mb: 1 }}>
                <IconButton
                  size="small"
                  disabled={disabled}
                  onClick={() => handleRemove(index)}
                  sx={{
                    p: 0.5,
                    "&:hover": {
                      color: theme.palette.error.main,
                    },
                  }}>
                  <Icon htmlColor="inherit" iconName={ICON_NAME.TRASH} style={{ fontSize: "14px" }} />
                </IconButton>
              </Stack>
            )}

            {/* Item fields */}
            <Stack spacing={2}>
              {visibleInputs.map((inputDef) => (
                <GenericInput
                  key={inputDef.name}
                  input={inputDef}
                  value={itemValues[inputDef.name]}
                  onChange={(newValue) => handleItemChange(index, inputDef.name, newValue)}
                  disabled={disabled}
                  formValues={{ ..._formValues, ...itemValues }}
                  schemaDefs={schemaDefs}
                  excludedLayerIds={getExcludedLayerIds(inputDef.name)}
                />
              ))}
            </Stack>

            {/* Divider between items */}
            {index < items.length - 1 && <Divider sx={{ mt: 2 }} />}
          </Box>
        );
      })}

      {/* Add button */}
      <Divider />
      <Button
        fullWidth
        disabled={disabled || !canAdd}
        onClick={handleAdd}
        variant="text"
        size="small"
        startIcon={<Icon iconName={ICON_NAME.PLUS} style={{ fontSize: "15px" }} />}>
        <Typography variant="body2" color="inherit">
          {t("add")} {formatInputName(input.title.replace(/s$/, ""))}
        </Typography>
      </Button>
    </Stack>
  );
}
