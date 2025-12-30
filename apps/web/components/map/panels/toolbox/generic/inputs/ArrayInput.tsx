/**
 * Generic Array Input Component
 *
 * Renders an input for array values (e.g., list of numbers for buffer distances).
 */
import { Chip, Stack, TextField } from "@mui/material";
import { useState } from "react";

import { getEffectiveSchema } from "@/lib/utils/ogc-utils";

import type { ProcessedInput } from "@/types/map/ogc-processes";

import FormLabelHelper from "@/components/common/FormLabelHelper";

interface ArrayInputProps {
  input: ProcessedInput;
  value: unknown[] | undefined;
  onChange: (value: unknown[] | undefined) => void;
  disabled?: boolean;
}

export default function ArrayInput({ input, value, onChange, disabled }: ArrayInputProps) {
  const [inputValue, setInputValue] = useState("");
  const effectiveSchema = getEffectiveSchema(input.schema);
  const itemSchema = effectiveSchema.items;
  const itemType = itemSchema?.type || "string";

  const currentValues = value ?? [];

  const handleAddValue = () => {
    if (!inputValue.trim()) return;

    let newValue: unknown;
    if (itemType === "number" || itemType === "integer") {
      newValue = Number(inputValue);
      if (isNaN(newValue as number)) return;
    } else {
      newValue = inputValue;
    }

    onChange([...currentValues, newValue]);
    setInputValue("");
  };

  const handleRemoveValue = (index: number) => {
    const newValues = [...currentValues];
    newValues.splice(index, 1);
    onChange(newValues.length > 0 ? newValues : undefined);
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === "Enter") {
      event.preventDefault();
      handleAddValue();
    }
  };

  return (
    <Stack spacing={1}>
      <FormLabelHelper label={input.title} tooltip={input.description} color="inherit" />

      {/* Current values as chips */}
      {currentValues.length > 0 && (
        <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
          {currentValues.map((val, index) => (
            <Chip
              key={index}
              label={String(val)}
              size="small"
              onDelete={disabled ? undefined : () => handleRemoveValue(index)}
              disabled={disabled}
            />
          ))}
        </Stack>
      )}

      {/* Input for new values */}
      <Stack direction="row" spacing={1}>
        <TextField
          size="small"
          type={itemType === "number" || itemType === "integer" ? "number" : "text"}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={disabled}
          placeholder={`Add ${input.title.toLowerCase()}`}
          fullWidth
          helperText="Press Enter to add"
        />
      </Stack>
    </Stack>
  );
}
