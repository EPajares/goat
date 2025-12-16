import { Fab, Stack, Tooltip, useTheme } from "@mui/material";
import { useMap } from "react-map-gl/maplibre";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

type ToolboxProps = {
  open?: boolean;
  onToggle?: (toolboxOpen: boolean) => void;
};

export function Toolbox(props: ToolboxProps) {
  const theme = useTheme();
  const { map } = useMap();

  return (
    <>
      {map && (
        <>
          <Stack
            direction="column"
            sx={{
              alignItems: "flex-start",
              my: 1,
            }}>
            <Tooltip title={props.open ? "Close Toolbox" : "Open Toolbox"} arrow placement="right">
              <Fab
                onClick={() => props.onToggle && props.onToggle(!props.open)}
                size="small"
                sx={{
                  pointerEvents: "all",
                  backgroundColor: theme.palette.background.paper,
                  marginTop: theme.spacing(1),
                  marginBottom: theme.spacing(1),
                  color: props.open ? theme.palette.primary.main : theme.palette.text.secondary,
                  "&:hover": {
                    backgroundColor: theme.palette.background.default,
                  },
                }}>
                <Icon iconName={ICON_NAME.TOOLBOX} htmlColor="inherit" fontSize="small" />
              </Fab>
            </Tooltip>
          </Stack>
        </>
      )}
    </>
  );
}
