import dayjs from "dayjs";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { DesktopTimePicker } from "@mui/x-date-pickers/DesktopTimePicker";
import { useTheme } from "@mui/material";

type TimePickerProps = {
  time: number; // time in seconds
  onChange: (time: number) => void;
  errorMessage?: string;
  error?: boolean;
};

export default function TimePicker(props: TimePickerProps) {
  const theme = useTheme();
  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <DesktopTimePicker
        slotProps={{
          actionBar: { actions: [] },
          textField: {
            error: props.error || !!props.errorMessage,
            helperText: props.errorMessage,
          },
        }}
        sx={{
          "& .MuiInputBase-root": {
            height: "40px",
            fontWeight: theme.typography.fontWeightBold,
            fontSize: theme.typography.body2.fontSize,
            color: theme.palette.text.secondary,
          },
        }}
        onChange={(newTime) => {
          const secondsFromMidnight = dayjs(newTime).diff(
            dayjs().startOf("day"),
            "second",
          );
          props.onChange(secondsFromMidnight);
        }}
        value={dayjs().startOf("day").add(props.time, "second")}
      />
    </LocalizationProvider>
  );
}
