import type { SxProps } from "@mui/material";
import { Slider, Stack, useTheme } from "@mui/material";

import InputTextField from "@/components/map/panels/style/other/InputTextField";

const SliderInput = ({
  value,
  isRange,
  onChange,
  onChangeCommitted,
  min = 0,
  max = 100,
  step = 1,
  rootSx,
}: {
  value: number | number[];
  isRange: boolean;
  onChange?: (newValue: number | number[]) => void;
  onChangeCommitted?: (newValue: number | number[]) => void;
  min?: number;
  max?: number;
  step?: number;
  rootSx?: SxProps;
}) => {
  const theme = useTheme();

  // Helper function to clamp value between min and max
  const clampValue = (val: number) => Math.min(Math.max(val, min), max);

  return (
    <Stack
      sx={{
        ...rootSx,
      }}
      direction={isRange ? "column" : "row"}
      spacing={4}
      alignItems="center">
      <Slider
        size="small"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(_event: Event, newValue: number | number[]) => {
          onChange && onChange(newValue);
        }}
        onChangeCommitted={(_event: Event, value: number | number[]) => {
          onChangeCommitted && onChangeCommitted(value);
        }}
      />
      {!isRange && !Array.isArray(value) && (
        <Stack>
          <InputTextField
            min={min}
            max={max}
            step={step}
            value={value}
            onChange={(event) => {
              const newValue = clampValue(Number(event.target.value));
              onChange && onChange(newValue);
            }}
            onBlur={() => {
              onChangeCommitted && onChangeCommitted(value);
            }}
          />
        </Stack>
      )}
      {isRange && Array.isArray(value) && (
        <Stack
          direction="row"
          justifyContent="space-between"
          width="100%"
          style={{ marginTop: theme.spacing(1) }}>
          <InputTextField
            min={min}
            max={max}
            step={step}
            value={value[0]}
            onChange={(event) => {
              const newValue = clampValue(Number(event.target.value));
              onChange && onChange([newValue, value[1]]);
            }}
            onBlur={() => {
              onChangeCommitted && onChangeCommitted(value);
            }}
          />
          <InputTextField
            min={min}
            max={max}
            step={step}
            value={value[1]}
            onChange={(event) => {
              const newValue = clampValue(Number(event.target.value));
              onChange && onChange([value[0], newValue]);
            }}
            onBlur={() => {
              onChangeCommitted && onChangeCommitted(value);
            }}
          />
        </Stack>
      )}
    </Stack>
  );
};

export default SliderInput;
