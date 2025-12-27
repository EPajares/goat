"use client";

import { Fab, Stack, Tooltip, useTheme } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useMap } from "react-map-gl/maplibre";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

import type { PopperMenuItem } from "@/components/common/PopperMenu";
import PopperMenu from "@/components/common/PopperMenu";

export type MeasureToolType = "line" | "distance" | "circle" | "area" | "walking" | "car";

// Shared icon mapping for measure tools - used in menu and results panel
export const MEASURE_TOOL_ICONS: Record<MeasureToolType, ICON_NAME> = {
  line: ICON_NAME.LINE_FEATURE,
  distance: ICON_NAME.PLANE,
  circle: ICON_NAME.CIRCLE_EMPTY,
  area: ICON_NAME.POLYGON_FEATURE,
  walking: ICON_NAME.RUN,
  car: ICON_NAME.CAR,
};

type MeasureProps = {
  open?: boolean;
  activeTool?: MeasureToolType;
  onToggle?: (measureOpen: boolean) => void;
  onSelectTool?: (tool: MeasureToolType) => void;
};

export function Measure(props: MeasureProps) {
  const theme = useTheme();
  const { map } = useMap();
  const { t } = useTranslation("common");

  const measureTools: PopperMenuItem[] = [
    {
      id: "line",
      label: t("measure_line"),
      icon: MEASURE_TOOL_ICONS.line,
      onClick: () => {
        props.onSelectTool?.("line");
      },
    },
    {
      id: "area",
      label: t("measure_polygon"),
      icon: MEASURE_TOOL_ICONS.area,
      onClick: () => {
        props.onSelectTool?.("area");
      },
    },
    {
      id: "circle",
      label: t("measure_circle"),
      icon: MEASURE_TOOL_ICONS.circle,
      onClick: () => {
        props.onSelectTool?.("circle");
      },
    },
    {
      id: "distance",
      label: t("measure_flight_distance"),
      icon: MEASURE_TOOL_ICONS.distance,
      onClick: () => {
        props.onSelectTool?.("distance");
      },
    },
    {
      id: "walking",
      label: t("measure_walking"),
      icon: MEASURE_TOOL_ICONS.walking,
      onClick: () => {
        props.onSelectTool?.("walking");
      },
    },
    {
      id: "car",
      label: t("measure_car"),
      icon: MEASURE_TOOL_ICONS.car,
      onClick: () => {
        props.onSelectTool?.("car");
      },
    },
  ];

  const selectedTool = measureTools.find((tool) => tool.id === props.activeTool);

  // Determine which icon to show - active tool icon or default measure icon
  const displayIcon: ICON_NAME = (props.activeTool && selectedTool?.icon) || ICON_NAME.RULER_HORIZONTAL;

  return (
    <>
      {map && (
        <Stack
          direction="column"
          sx={{
            alignItems: "flex-start",
            my: 1,
          }}>
          <PopperMenu
            menuItems={measureTools}
            selectedItem={selectedTool}
            placement="right"
            onSelect={(item) => {
              props.onSelectTool?.(item.id as MeasureToolType);
            }}
            menuButton={
              <Tooltip title={props.open ? t("close_measure") : t("open_measure")} arrow placement="right">
                <Fab
                  onClick={() => {
                    if (!props.open) {
                      props.onToggle?.(true);
                    } else {
                      props.onToggle?.(false);
                    }
                  }}
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
                  <Icon iconName={displayIcon} htmlColor="inherit" fontSize="small" />
                </Fab>
              </Tooltip>
            }
          />
        </Stack>
      )}
    </>
  );
}
