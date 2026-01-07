/**
 * Generic Input Component
 *
 * Routes to the appropriate input component based on the inferred input type.
 */
import { Typography } from "@mui/material";

import type { OGCInputSchema, ProcessedInput } from "@/types/map/ogc-processes";

import ArrayInput from "@/components/map/panels/toolbox/generic/inputs/ArrayInput";
import BooleanInput from "@/components/map/panels/toolbox/generic/inputs/BooleanInput";
import EnumInput from "@/components/map/panels/toolbox/generic/inputs/EnumInput";
import FieldInput from "@/components/map/panels/toolbox/generic/inputs/FieldInput";
import FieldStatisticsInput from "@/components/map/panels/toolbox/generic/inputs/FieldStatisticsInput";
import LayerInput from "@/components/map/panels/toolbox/generic/inputs/LayerInput";
import MultiEnumInput from "@/components/map/panels/toolbox/generic/inputs/MultiEnumInput";
import NumberInput from "@/components/map/panels/toolbox/generic/inputs/NumberInput";
import ObjectInput from "@/components/map/panels/toolbox/generic/inputs/ObjectInput";
import RepeatableObjectInput from "@/components/map/panels/toolbox/generic/inputs/RepeatableObjectInput";
import ScenarioInput from "@/components/map/panels/toolbox/generic/inputs/ScenarioInput";
import StartingPointsInput from "@/components/map/panels/toolbox/generic/inputs/StartingPointsInput";
import StringInput from "@/components/map/panels/toolbox/generic/inputs/StringInput";
import TimePickerInput from "@/components/map/panels/toolbox/generic/inputs/TimePickerInput";

interface GenericInputProps {
  input: ProcessedInput;
  value: unknown;
  onChange: (value: unknown) => void;
  /** Callback for layer inputs to report their associated CQL filter */
  onFilterChange?: (filter: Record<string, unknown> | undefined) => void;
  disabled?: boolean;
  /** All current form values - needed for field inputs to know the selected layer */
  formValues?: Record<string, unknown>;
  /** Schema definitions ($defs) for resolving $ref in nested objects */
  schemaDefs?: Record<string, OGCInputSchema>;
  /** Layer IDs to exclude from layer selectors (for repeatable objects) */
  excludedLayerIds?: string[];
}

export default function GenericInput({
  input,
  value,
  onChange,
  onFilterChange,
  disabled,
  formValues = {},
  schemaDefs,
  excludedLayerIds,
}: GenericInputProps) {
  switch (input.inputType) {
    case "layer":
      return (
        <LayerInput
          input={input}
          value={value as string | undefined}
          onChange={onChange}
          onFilterChange={onFilterChange}
          disabled={disabled}
          excludedLayerIds={excludedLayerIds}
        />
      );

    case "field":
      return (
        <FieldInput
          input={input}
          value={value}
          onChange={onChange}
          disabled={disabled}
          formValues={formValues}
        />
      );

    case "field-statistics":
      return (
        <FieldStatisticsInput
          input={input}
          value={value}
          onChange={onChange}
          disabled={disabled}
          formValues={formValues}
        />
      );

    case "scenario":
      return (
        <ScenarioInput
          input={input}
          value={value as string | undefined}
          onChange={onChange}
          disabled={disabled}
        />
      );

    case "enum":
      return (
        <EnumInput
          input={input}
          value={value as string | number | boolean | undefined}
          onChange={onChange}
          disabled={disabled}
          formValues={formValues}
        />
      );

    case "multi-enum":
      return (
        <MultiEnumInput
          input={input}
          value={value as (string | number)[] | undefined}
          onChange={onChange}
          disabled={disabled}
          schemaDefs={schemaDefs}
        />
      );

    case "boolean":
      return (
        <BooleanInput
          input={input}
          value={value as boolean | undefined}
          onChange={(v) => onChange(v)}
          disabled={disabled}
        />
      );

    case "number":
      return (
        <NumberInput
          input={input}
          value={value as number | undefined}
          onChange={onChange}
          disabled={disabled}
        />
      );

    case "time-picker":
      return (
        <TimePickerInput
          input={input}
          value={value as number | undefined}
          onChange={onChange}
          disabled={disabled}
        />
      );

    case "starting-points":
      return (
        <StartingPointsInput
          input={input}
          value={value as { latitude: number[]; longitude: number[] } | { layer_id: string } | undefined}
          onChange={onChange}
          disabled={disabled}
        />
      );

    case "string":
      return (
        <StringInput
          input={input}
          value={value as string | undefined}
          onChange={onChange}
          disabled={disabled}
        />
      );

    case "array":
      return (
        <ArrayInput
          input={input}
          value={value as unknown[] | undefined}
          onChange={onChange}
          disabled={disabled}
        />
      );

    case "repeatable-object":
      return (
        <RepeatableObjectInput
          input={input}
          value={value as Record<string, unknown>[] | undefined}
          onChange={onChange}
          disabled={disabled}
          schemaDefs={schemaDefs}
          formValues={formValues}
        />
      );

    case "object":
      return (
        <ObjectInput
          input={input}
          value={value as Record<string, unknown> | undefined}
          onChange={onChange}
          disabled={disabled}
          schemaDefs={schemaDefs}
          formValues={formValues}
        />
      );

    case "unknown":
    default:
      return (
        <Typography variant="body2" color="text.secondary">
          Unknown input type: {input.title}
        </Typography>
      );
  }
}
