/**
 * Time Picker Input Component
 *
 * Renders a time picker for integer fields (seconds from midnight).
 */
import { Stack } from "@mui/material";

import TimePicker from "@p4b/ui/components/TimePicker";

import type { ProcessedInput } from "@/types/map/ogc-processes";

import FormLabelHelper from "@/components/common/FormLabelHelper";

interface TimePickerInputProps {
  input: ProcessedInput;
  value: number | undefined;
  onChange: (value: number) => void;
  disabled?: boolean;
}

export default function TimePickerInput({ input, value, onChange }: TimePickerInputProps) {
  return (
    <Stack>
      <FormLabelHelper label={input.title} tooltip={input.description} color="inherit" />
      <TimePicker time={value ?? (input.defaultValue as number) ?? 0} onChange={onChange} />
    </Stack>
  );
}
