/**
 * Generic Boolean Input Component
 *
 * Renders a switch toggle for boolean values.
 */
import { Stack, Switch, Typography } from "@mui/material";

import type { ProcessedInput } from "@/types/map/ogc-processes";

import FormLabelHelper from "@/components/common/FormLabelHelper";

interface BooleanInputProps {
  input: ProcessedInput;
  value: boolean | undefined;
  onChange: (value: boolean) => void;
  disabled?: boolean;
}

export default function BooleanInput({ input, value, onChange, disabled }: BooleanInputProps) {
  const defaultValue = input.defaultValue as boolean | undefined;
  const currentValue = value ?? defaultValue ?? false;

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onChange(event.target.checked);
  };

  return (
    <Stack
      direction="row"
      alignItems="center"
      justifyContent="space-between"
      sx={{
        py: 1,
        px: 0,
      }}>
      <Stack direction="row" alignItems="center" spacing={1}>
        <Typography variant="body2" color={disabled ? "text.secondary" : "text.primary"}>
          {input.title}
        </Typography>
        {input.description && <FormLabelHelper label="" tooltip={input.description} color="inherit" />}
      </Stack>
      <Switch checked={currentValue} onChange={handleChange} disabled={disabled} size="small" />
    </Stack>
  );
}
