import type {
  IconButtonProps,
  SxProps,
  Theme,
  TooltipProps,
} from "@mui/material";
import { IconButton, Tooltip } from "@mui/material";
import DarkModeIcon from "@mui/icons-material/Brightness4";
import LightModeIcon from "@mui/icons-material/Brightness7";

export type DarkModeSwitchProps = {
  sx?: SxProps<Theme>;
  isDarkModeEnabled: boolean;
  toolTipProps?: Omit<TooltipProps, "children">;
} & IconButtonProps;

export default function DarkModeSwitch(props: DarkModeSwitchProps) {
  const { sx, isDarkModeEnabled, toolTipProps, children: _children, ...rest } = props;

  return (
    <Tooltip
      title={toolTipProps?.title ? toolTipProps.title : null}
      {...toolTipProps}
    >
      <IconButton
        sx={{
          transition: "transform 500ms",
          transform: isDarkModeEnabled ? "rotate(180deg)" : "rotate(0deg)",
          transitionTimingFunction: "cubic-bezier(.34,1.27,1,1)",
          ...sx,
        }}
        aria-label={isDarkModeEnabled ? "Light mode" : "Dark mode"}
        {...rest}
      >
        {isDarkModeEnabled ? (
          <LightModeIcon fontSize="inherit" />
        ) : (
          <DarkModeIcon fontSize="inherit" />
        )}
      </IconButton>
    </Tooltip>
  );
}
