/**
 * Generic Number Input Component
 *
 * Renders a number input with optional slider based on schema constraints.
 */
import { Stack, TextField } from "@mui/material";
import { useMemo } from "react";

import { getEffectiveSchema } from "@/lib/utils/ogc-utils";

import type { ProcessedInput } from "@/types/map/ogc-processes";

import FormLabelHelper from "@/components/common/FormLabelHelper";
import SliderInput from "@/components/map/panels/common/SliderInput";

interface NumberInputProps {
  input: ProcessedInput;
  value: number | undefined;
  onChange: (value: number | undefined) => void;
  disabled?: boolean;
}

export default function NumberInput({ input, value, onChange, disabled }: NumberInputProps) {
  const effectiveSchema = useMemo(() => getEffectiveSchema(input.schema), [input.schema]);

  // Extract constraints
  const min = effectiveSchema.minimum;
  const max = effectiveSchema.maximum;
  const hasRange = min !== undefined && max !== undefined;

  // Determine if we should use a slider (has reasonable range)
  const useSlider = useMemo(() => {
    if (!hasRange) return false;
    const range = (max as number) - (min as number);
    // Use slider for ranges that make sense (not too large)
    return range <= 10000 && range > 0;
  }, [hasRange, min, max]);

  const handleSliderChange = (newValue: number) => {
    onChange(newValue);
  };

  const handleTextChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value === "" ? undefined : Number(event.target.value);
    onChange(newValue);
  };

  if (useSlider) {
    return (
      <Stack>
        <FormLabelHelper label={input.title} tooltip={input.description} color="inherit" />
        <SliderInput
          value={value ?? (input.defaultValue as number) ?? min ?? 0}
          isRange={false}
          min={min as number}
          max={max as number}
          step={effectiveSchema.type === "integer" ? 1 : undefined}
          onChange={handleSliderChange}
        />
      </Stack>
    );
  }

  return (
    <Stack>
      <FormLabelHelper label={input.title} tooltip={input.description} color="inherit" />
      <TextField
        type="number"
        size="small"
        value={value ?? ""}
        onChange={handleTextChange}
        disabled={disabled}
        inputProps={{
          min,
          max,
          step: effectiveSchema.type === "integer" ? 1 : "any",
        }}
        placeholder={input.defaultValue !== undefined ? String(input.defaultValue) : undefined}
        fullWidth
      />
    </Stack>
  );
}
