/**
 * Generic Input Component
 *
 * Routes to the appropriate input component based on the inferred input type.
 */
import { Typography } from "@mui/material";

import type { ProcessedInput } from "@/types/map/ogc-processes";

import ArrayInput from "@/components/map/panels/toolbox/generic/inputs/ArrayInput";
import BooleanInput from "@/components/map/panels/toolbox/generic/inputs/BooleanInput";
import EnumInput from "@/components/map/panels/toolbox/generic/inputs/EnumInput";
import FieldInput from "@/components/map/panels/toolbox/generic/inputs/FieldInput";
import LayerInput from "@/components/map/panels/toolbox/generic/inputs/LayerInput";
import NumberInput from "@/components/map/panels/toolbox/generic/inputs/NumberInput";
import StringInput from "@/components/map/panels/toolbox/generic/inputs/StringInput";

interface GenericInputProps {
  input: ProcessedInput;
  value: unknown;
  onChange: (value: unknown) => void;
  disabled?: boolean;
  /** All current form values - needed for field inputs to know the selected layer */
  formValues?: Record<string, unknown>;
}

export default function GenericInput({
  input,
  value,
  onChange,
  disabled,
  formValues = {},
}: GenericInputProps) {
  switch (input.inputType) {
    case "layer":
      return (
        <LayerInput
          input={input}
          value={value as string | undefined}
          onChange={onChange}
          disabled={disabled}
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

    case "enum":
      return (
        <EnumInput
          input={input}
          value={value as string | number | boolean | undefined}
          onChange={onChange}
          disabled={disabled}
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

    case "object":
      // For complex objects, show a message for now
      // TODO: Implement nested object input
      return (
        <Typography variant="body2" color="text.secondary">
          Complex input: {input.title} (not yet supported in generic form)
        </Typography>
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
