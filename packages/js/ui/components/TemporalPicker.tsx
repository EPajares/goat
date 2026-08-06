import { FormControl, FormHelperText, Stack, useTheme } from "@mui/material";
import { DateTimePicker } from "@mui/x-date-pickers/DateTimePicker";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import dayjs, { type Dayjs } from "dayjs";
import utc from "dayjs/plugin/utc";
import { useState } from "react";

import { TEMPORAL_DISPLAY_FORMAT, TEMPORAL_VALUE_FORMAT } from "./temporalFormats";

dayjs.extend(utc);

// Values are UTC instants (or naive wall times, which the platform treats as
// UTC). Parse in UTC so offset-suffixed values show their UTC wall time
// instead of shifting to the browser's timezone; the emitted literal is the
// wall time as picked, never converted.
const parseValue = (value?: string): Dayjs | null => {
  if (!value) return null;
  const parsed = dayjs.utc(value);
  return parsed.isValid() ? parsed : null;
};

type TemporalPickerProps = {
  kind?: "datetime";
  value?: string;
  onChange: (value: string) => void;
  label?: string;
};

export default function TemporalPicker(props: TemporalPickerProps) {
  const theme = useTheme();
  const [focused, setFocused] = useState(false);

  const handleChange = (next: Dayjs | null) => {
    props.onChange(next && next.isValid() ? next.format(TEMPORAL_VALUE_FORMAT) : "");
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <FormControl size="small" fullWidth>
        {/* Label above the input, matching the platform's panel inputs
            (FormLabelHelper pattern) instead of MUI's floating label. */}
        {!!props.label && (
          <Stack
            direction="row"
            alignItems="center"
            sx={{
              color: focused ? theme.palette.primary.main : theme.palette.text.secondary,
              mb: 1,
            }}>
            <FormHelperText sx={{ color: "inherit", ml: 0, mt: 0, mr: 1 }}>{props.label}</FormHelperText>
          </Stack>
        )}
        <DateTimePicker
          value={parseValue(props.value)}
          onChange={handleChange}
          format={TEMPORAL_DISPLAY_FORMAT}
          ampm={false}
          slotProps={{
            textField: {
              size: "small",
              fullWidth: true,
              onFocus: () => setFocused(true),
              onBlur: () => setFocused(false),
            },
            actionBar: { actions: [] },
          }}
          sx={{
            "& .MuiInputBase-root": {
              height: "40px",
              fontSize: theme.typography.body2.fontSize,
              color: theme.palette.text.secondary,
            },
          }}
        />
      </FormControl>
    </LocalizationProvider>
  );
}
