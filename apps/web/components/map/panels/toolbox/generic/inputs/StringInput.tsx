/**
 * Generic String Input Component
 *
 * Renders a text input for string values.
 */
import { Stack, TextField } from "@mui/material";

import { getEffectiveSchema } from "@/lib/utils/ogc-utils";

import type { ProcessedInput } from "@/types/map/ogc-processes";

import FormLabelHelper from "@/components/common/FormLabelHelper";

interface StringInputProps {
  input: ProcessedInput;
  value: string | undefined;
  onChange: (value: string | undefined) => void;
  disabled?: boolean;
}

export default function StringInput({ input, value, onChange, disabled }: StringInputProps) {
  const effectiveSchema = getEffectiveSchema(input.schema);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value === "" ? undefined : event.target.value;
    onChange(newValue);
  };

  return (
    <Stack>
      <FormLabelHelper label={input.title} tooltip={input.description} color="inherit" />
      <TextField
        size="small"
        value={value ?? ""}
        onChange={handleChange}
        disabled={disabled}
        inputProps={{
          minLength: effectiveSchema.minLength,
          maxLength: effectiveSchema.maxLength,
          pattern: effectiveSchema.pattern,
        }}
        placeholder={input.defaultValue !== undefined ? String(input.defaultValue) : undefined}
        fullWidth
      />
    </Stack>
  );
}
