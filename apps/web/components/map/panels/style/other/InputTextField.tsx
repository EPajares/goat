import { OutlinedInput } from "@mui/material";

const InputTextField = ({
  value,
  onChange,
  onBlur,
  min = 0,
  max = 100,
  step,
  error,
  outlineInputSx = {},
}: {
  value: number | number[];
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: () => void;
  min?: number;
  max?: number;
  step?: number;
  error?: boolean;
  outlineInputSx?: React.CSSProperties;
}) => {
  return (
    <OutlinedInput
      value={value}
      size="small"
      onChange={onChange}
      onBlur={onBlur}
      sx={{
        pr: 0,
        "& input::-webkit-outer-spin-button, & input::-webkit-inner-spin-button": {
          display: "none",
        },
        "& input[type=number]": {
          MozAppearance: "textfield",
        },
        ...outlineInputSx,
      }}
      error={error}
      inputProps={{
        step: step,
        min: min,
        max: max,
        type: "number",
        style: {
          width: "48px",
          padding: "0px 0px 0px 5px",
          height: "30px",
          fontSize: "0.75rem",
        },
      }}
    />
  );
};

export default InputTextField;
