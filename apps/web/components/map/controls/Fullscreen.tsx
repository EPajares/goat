import { Fab, Stack, Tooltip, useTheme } from "@mui/material";
import { useState } from "react";
import { useMap } from "react-map-gl/maplibre";
import screenfull from "screenfull";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

type FullscreenProps = {
  tooltipOpen?: string;
  tooltipExit?: string;
};

export function Fullscren(props: FullscreenProps) {
  const [fullscreen, setFullscreen] = useState(screenfull.isFullscreen);

  const theme = useTheme();

  const { map } = useMap();
  if (screenfull.isEnabled) {
    screenfull.on("change", () => {
      setFullscreen(screenfull.isFullscreen);
    });
  }
  const toggleFullscreen = () => {
    if (screenfull.isEnabled) {
      screenfull.toggle();
    }
  };
  return (
    <>
      {map && (
        <>
          <Stack
            direction="column"
            sx={{
              alignItems: "flex-end",
              my: 1,
            }}>
            <Tooltip
              title={fullscreen ? props.tooltipExit || "Exit Fullscreen" : props.tooltipOpen || "Fullscreen"}
              arrow
              placement="left">
              <Fab
                onClick={() => toggleFullscreen()}
                size="small"
                sx={{
                  pointerEvents: "all",
                  backgroundColor: theme.palette.background.paper,
                  marginTop: theme.spacing(1),
                  marginBottom: theme.spacing(1),
                  color: theme.palette.text.secondary,
                  "&:hover": {
                    backgroundColor: theme.palette.background.default,
                  },
                }}>
                <Icon
                  iconName={fullscreen ? ICON_NAME.MINIMIZE : ICON_NAME.MAXIMIZE}
                  htmlColor="inherit"
                  fontSize="small"
                />
              </Fab>
            </Tooltip>
          </Stack>
        </>
      )}
    </>
  );
}
